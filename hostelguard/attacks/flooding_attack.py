"""
hostelguard/attacks/flooding_attack.py
Simulated flooding / denial-of-service attack.

The attacker injects a large number of messages in a short time to
overwhelm the broker.  Against the insecure broker there is no rate
limiter, so all messages are accepted.

This module is educational only and operates entirely in-process.
"""

import json
import logging

from hostelguard.sim.interfaces import AttackBase, AttackResult, SystemContainer
from hostelguard.sim.messages import MessageEnvelope
from hostelguard import config

logger = logging.getLogger(__name__)


class FloodingAttack(AttackBase):
    """Flood the broker with fake messages from a spoofed device."""

    @property
    def name(self) -> str:
        return "Flooding (DoS) Attack"

    def run(self, system: SystemContainer) -> AttackResult:
        """Inject ATTACK_FLOOD_SIZE messages as fast as possible."""
        flood_device_id = "attacker_flooder"
        topic = config.make_topic("temp_room_101", config.TOPIC_TELEMETRY)
        payload = json.dumps({"temperature_c": 99.9, "attacker": True}).encode()

        before_len = len(system.wire.transcript)

        for i in range(config.ATTACK_FLOOD_SIZE):
            env = MessageEnvelope(
                device_id=flood_device_id,
                topic=topic,
                payload=payload,
                timestamp=system.clock.now(),
                counter=i,
                nonce=b"",
                mac=b"",
                signature=b"",
                encrypted=False,
            )
            system.wire.inject(env)

        after_len = len(system.wire.transcript)
        injected = after_len - before_len

        logger.warning("Flooding attack: injected %d messages", injected)

        return AttackResult(
            name=self.name,
            mode=system.mode,
            succeeded=injected == config.ATTACK_FLOOD_SIZE,
            detail=(
                f"Injected {injected}/{config.ATTACK_FLOOD_SIZE} messages (no rate limit)"
                if system.mode == "insecure"
                else f"Injected {injected}/{config.ATTACK_FLOOD_SIZE} messages"
            ),
            metrics={"injected": injected, "target_count": config.ATTACK_FLOOD_SIZE},
        )
