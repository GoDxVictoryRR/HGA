"""
hostelguard/attacks/replay_attack.py
Simulated replay attack.

An eavesdropper captures a valid telemetry message, then re-injects it
later.  Against the insecure broker there is no timestamp or counter check,
so the replayed message is accepted as fresh.

This module is educational only.  It operates entirely within the
in-process simulation and never touches a real network.
"""

import logging

from hostelguard.sim.interfaces import AttackBase, AttackResult, SystemContainer
from hostelguard.sim.wire import Attacker
from hostelguard import config

logger = logging.getLogger(__name__)


class ReplayAttack(AttackBase):
    """Capture messages and replay them later.

    In the insecure system the replayed messages are accepted.
    In the secure system they are rejected because the counter has already
    been seen and the timestamp is outside the replay window.
    """

    @property
    def name(self) -> str:
        return "Replay Attack"

    def _capture_messages(self, system: SystemContainer) -> list:
        """Attach attacker, let devices emit messages, return captured envelopes."""
        attacker = Attacker()
        system.wire.attach_attacker(attacker)
        for device in system.devices[:config.ATTACK_REPLAY_COUNT]:
            envelope = device.publish_telemetry()
            system.broker.publish(envelope)
        captured = list(attacker.captured)
        logger.info("Replay attack captured %d messages", len(captured))
        if hasattr(system.clock, "advance"):
            system.clock.advance(config.REPLAY_WINDOW_SECONDS + 10)
        system.wire.detach_attacker()
        return captured

    def _replay_messages(self, system: SystemContainer, captured: list):
        """Replay captured envelopes; return (replayed_count, accepted_count)."""
        from hostelguard.exceptions import ReplayError, AuthenticationError, TamperError
        replayed = accepted = 0
        for env in captured[:config.ATTACK_REPLAY_COUNT]:
            replayed += 1
            if system.mode == "insecure":
                system.wire.inject(env)
                accepted += 1
            else:
                try:
                    system.broker.publish(env)
                    accepted += 1
                except (ReplayError, AuthenticationError, TamperError, Exception):
                    pass
        return replayed, accepted

    def run(self, system: SystemContainer) -> AttackResult:
        """Execute: sniff some messages, advance clock, replay them."""
        captured = self._capture_messages(system)
        replayed, accepted = self._replay_messages(system, captured)
        succeeded = accepted > 0
        return AttackResult(
            name=self.name,
            mode=system.mode,
            succeeded=succeeded,
            detail=(
                f"Replayed {replayed} messages; {accepted} accepted (no counter/timestamp check)"
                if succeeded
                else f"All {replayed} replay attempts blocked (counter+timestamp check)"
            ),
            metrics={"captured": len(captured), "replayed": replayed, "accepted": accepted},
        )
