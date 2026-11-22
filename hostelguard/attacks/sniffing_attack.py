"""
hostelguard/attacks/sniffing_attack.py
Simulated passive sniffing attack.

The attacker attaches to the wire in read-only mode and observes plaintext
messages.  Against the insecure system all payloads are readable.
In the secure system payloads are encrypted, so the attacker cannot extract
meaningful information.

This module is educational only and operates entirely in-process.
"""

import json
import logging

from hostelguard.sim.interfaces import AttackBase, AttackResult, SystemContainer
from hostelguard.sim.wire import Attacker
from hostelguard import config

logger = logging.getLogger(__name__)


class SniffingAttack(AttackBase):
    """Passively capture and read messages off the wire."""

    @property
    def name(self) -> str:
        return "Sniffing Attack"

    def run(self, system: SystemContainer) -> AttackResult:
        """Attach a passive listener, let devices publish, read the contents."""
        attacker = Attacker()
        system.wire.attach_attacker(attacker)

        # Let some devices publish so the attacker has something to capture
        for device in system.devices[:config.ATTACK_SNIFF_COUNT]:
            envelope = device.publish_telemetry()
            system.broker.publish(envelope)

        captured = attacker.captured[:]
        system.wire.detach_attacker()

        # Try to read the plaintext content of each captured message
        readable = []
        for env in captured:
            if not env.encrypted:
                try:
                    data = json.loads(env.payload.decode("utf-8"))
                    readable.append(data)
                except Exception:
                    readable.append(str(env.payload[:50]))

        succeeded = len(readable) > 0
        logger.warning(
            "Sniffing attack captured %d messages, read %d plaintext payloads",
            len(captured), len(readable),
        )

        return AttackResult(
            name=self.name,
            mode=system.mode,
            succeeded=succeeded,
            detail=(
                f"Read {len(readable)} plaintext payloads from {len(captured)} messages"
                if succeeded
                else "No readable messages captured"
            ),
            metrics={
                "captured": len(captured),
                "readable": len(readable),
                "sample": str(readable[0]) if readable else "",
            },
        )
