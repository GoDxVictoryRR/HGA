"""
hostelguard/attacks/spoofing_attack.py
Simulated message-spoofing attack.

The attacker crafts a fake message pretending to come from a legitimate
device (e.g., an unlock command from a door lock it does not own).  Against
the insecure broker there is no signature check, so the spoofed message
is delivered as if it came from the real device.

This module is educational only and operates entirely in-process.
"""

import json
import logging

from hostelguard.sim.interfaces import AttackBase, AttackResult, SystemContainer
from hostelguard.sim.messages import MessageEnvelope
from hostelguard import config

logger = logging.getLogger(__name__)


class SpoofingAttack(AttackBase):
    """Forge a command message from a device the attacker does not own."""

    @property
    def name(self) -> str:
        return "Spoofing Attack"

    def run(self, system: SystemContainer) -> AttackResult:
        """Inject a fake 'unlock' command pretending to be from the warden."""
        # Pick the first RFID lock as the target
        target_device_id = "rfid_main_gate"

        # Craft a fake command envelope impersonating a warden command
        fake_payload = json.dumps({"action": "unlock", "attacker": True}).encode()
        spoofed_env = MessageEnvelope(
            device_id="warden",           # attacker pretends to be the warden
            topic=config.make_topic(target_device_id, config.TOPIC_COMMAND),
            payload=fake_payload,
            timestamp=system.clock.now(),
            counter=0,
            nonce=b"",
            mac=b"",          # no valid MAC — broker won't check in insecure mode
            signature=b"",    # no valid signature
            encrypted=False,
        )

        # Inject the spoofed message directly onto the wire
        before_len = len(system.wire.transcript)
        system.wire.inject(spoofed_env)
        after_len = len(system.wire.transcript)

        delivered = after_len > before_len
        logger.warning(
            "Spoofing attack: fake command for %s delivered=%s", target_device_id, delivered
        )

        return AttackResult(
            name=self.name,
            mode=system.mode,
            succeeded=delivered,
            detail=(
                "Spoofed unlock command delivered to door lock (no signature check)"
                if delivered
                else "Spoofed command was blocked"
            ),
            metrics={"delivered": int(delivered)},
        )
