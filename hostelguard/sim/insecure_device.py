"""
hostelguard/sim/insecure_device.py
Intentionally insecure device implementation.

*** THIS MODULE IS INTENTIONALLY INSECURE AND FOR SIMULATION ONLY ***
*** Do not use this code in any real system. ***

The insecure device:
- Sends plaintext payloads with no encryption.
- Sets counter=0 always (no replay protection).
- Attaches no MAC and no signature.
- Does not verify any incoming command.

This is the baseline that the attack modules target.
"""

import json
import logging
import random
from typing import Optional

from hostelguard import config
from hostelguard.clock import Clock
from hostelguard.sim.interfaces import DeviceBase
from hostelguard.sim.messages import MessageEnvelope

logger = logging.getLogger(__name__)

# Shared seeded RNG for reproducible sensor noise.
# Crypto material must NOT use this; use os.urandom instead.
_rng = random.Random(config.SIM_RANDOM_SEED)


def _make_payload(device_type: str, location: str) -> dict:
    """Generate a realistic sensor reading for the given device type."""
    if device_type == "rfid_door_lock":
        return {"status": _rng.choice(["locked", "unlocked"]), "location": location}
    elif device_type == "temperature_sensor":
        return {"temperature_c": round(_rng.uniform(20.0, 35.0), 2), "location": location}
    elif device_type == "energy_meter":
        return {"watts": round(_rng.uniform(50.0, 500.0), 1), "location": location}
    elif device_type == "motion_sensor":
        return {"motion_detected": _rng.choice([True, False]), "location": location}
    else:
        return {"raw": "unknown", "location": location}


class InsecureDevice(DeviceBase):
    """A device with no security measures.

    Uses a shared seeded RNG for sensor noise so runs are reproducible.
    """

    def __init__(
        self,
        device_id: str,
        device_type: str,
        location: str,
        clock: Optional[Clock] = None,
    ) -> None:
        self._id = device_id
        self._type = device_type
        self._location = location
        self._clock = clock or Clock()

    @property
    def device_id(self) -> str:
        return self._id

    def publish_telemetry(self) -> MessageEnvelope:
        """Create a plaintext telemetry envelope with no security fields."""
        reading = _make_payload(self._type, self._location)
        payload = json.dumps(reading).encode("utf-8")
        envelope = MessageEnvelope(
            device_id=self._id,
            topic=config.make_topic(self._id, config.TOPIC_TELEMETRY),
            payload=payload,
            timestamp=self._clock.now(),
            counter=0,        # no replay protection
            nonce=b"",        # no encryption
            mac=b"",          # no integrity check
            signature=b"",    # no authentication
            encrypted=False,
        )
        logger.debug("Device %s published telemetry (insecure)", self._id)
        return envelope

    def receive_command(self, envelope: MessageEnvelope) -> None:
        """Accept any command without verifying sender or integrity."""
        try:
            command = json.loads(envelope.payload.decode("utf-8"))
        except Exception:
            command = str(envelope.payload)
        logger.info(
            "Device %s received command (unverified): %s", self._id, command
        )
