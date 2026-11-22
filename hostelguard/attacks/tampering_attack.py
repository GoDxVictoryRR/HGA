"""
hostelguard/attacks/tampering_attack.py
Simulated message-tampering attack.

The attacker intercepts a message in flight and modifies its payload.
Against the insecure broker there is no MAC or signature check, so the
tampered message is accepted by the recipient.

This module is educational only and operates entirely in-process.
"""

import json
import logging

from hostelguard.sim.interfaces import AttackBase, AttackResult, SystemContainer
from hostelguard.sim.wire import Attacker
from hostelguard.sim.messages import MessageEnvelope

logger = logging.getLogger(__name__)


class TamperingAttack(AttackBase):
    """Intercept and modify a message in flight."""

    @property
    def name(self) -> str:
        return "Tampering Attack"

    def run(self, system: SystemContainer) -> AttackResult:
        """Replace the payload of the next temperature reading with fake data."""
        tampered_messages = []

        def _tamper(envelope: MessageEnvelope):
            """Modify the payload of temperature sensor messages."""
            if "temperature_sensor" in envelope.topic or "temp" in envelope.device_id:
                # Replace with an extreme false reading
                fake = json.dumps({"temperature_c": -99.0, "tampered": True}).encode()
                modified = envelope.copy()
                modified.payload = fake
                tampered_messages.append(modified)
                logger.warning(
                    "Tampering: modified payload of %s", envelope.device_id
                )
                return modified  # deliver the tampered version
            return envelope  # let other messages through unchanged

        attacker = Attacker()
        attacker.set_tamper_fn(_tamper)
        system.wire.attach_attacker(attacker)

        # Let temperature devices publish so the attacker has something to tamper
        for device in system.devices:
            if "temp" in device.device_id:
                envelope = device.publish_telemetry()
                system.broker.publish(envelope)

        system.wire.detach_attacker()

        succeeded = len(tampered_messages) > 0
        return AttackResult(
            name=self.name,
            mode=system.mode,
            succeeded=succeeded,
            detail=(
                f"Tampered {len(tampered_messages)} messages (no MAC check)"
                if succeeded
                else "No messages tampered"
            ),
            metrics={"tampered": len(tampered_messages)},
        )
