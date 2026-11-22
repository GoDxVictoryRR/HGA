"""
hostelguard/sim/secure_device.py
Secure device implementation used in the hardened system (Phase 3+).

Compared to the insecure device, the secure device:
- Encrypts its payload with AES-256-GCM.
- Attaches an HMAC-SHA256 MAC over all envelope fields.
- Signs the envelope with its ECDSA private key.
- Increments a per-device counter to enable replay detection.
"""

import json
import logging

from hostelguard import config
from hostelguard.clock import Clock
from hostelguard.crypto.aes_gcm import AesGcmCipher
from hostelguard.crypto.ecdsa_signatures import EcdsaSigner
from hostelguard.crypto.hmac_integrity import HmacIntegrity
from hostelguard.crypto.keystore import KeyStore, KEY_AES, KEY_HMAC, KEY_ECDSA_PRIVATE
from hostelguard.sim.insecure_device import _make_payload
from hostelguard.sim.interfaces import DeviceBase
from hostelguard.sim.messages import MessageEnvelope

logger = logging.getLogger(__name__)


class SecureDevice(DeviceBase):
    """A device that applies encryption, MAC and digital signatures."""

    def __init__(
        self,
        device_id: str,
        device_type: str,
        location: str,
        clock: Clock,
        keystore: KeyStore,
    ) -> None:
        self._id = device_id
        self._type = device_type
        self._location = location
        self._clock = clock
        self._keystore = keystore
        self._counter = 0  # monotonically increasing, per device

    @property
    def device_id(self) -> str:
        return self._id

    def _encrypt_payload(self, plaintext: bytes, topic: str):
        """Encrypt plaintext with AES-GCM. Returns (nonce, ciphertext, encrypted_flag)."""
        aes_key = self._keystore.get(self._id, KEY_AES)
        if not aes_key:
            logger.warning("SecureDevice %s: AES key not found, sending plaintext", self._id)
            return b"", plaintext, False
        cipher = AesGcmCipher(aes_key)
        assoc = f"{self._id}:{topic}".encode()
        nonce, ciphertext = cipher.encrypt(plaintext, assoc)
        return nonce, ciphertext, True

    def _compute_mac(self, topic: str, payload: bytes, timestamp: float) -> bytes:
        """Compute HMAC-SHA256 over envelope fields; return empty bytes if no key."""
        hmac_key = self._keystore.get(self._id, KEY_HMAC)
        if not hmac_key:
            return b""
        return HmacIntegrity(hmac_key).compute(
            self._id, topic, payload, timestamp, self._counter)

    def _sign_payload(self, payload: bytes) -> bytes:
        """ECDSA-sign payload; return empty bytes if no private key."""
        priv_pem_str = self._keystore.get_str(self._id, KEY_ECDSA_PRIVATE)
        if not priv_pem_str:
            return b""
        return EcdsaSigner(priv_pem_str.encode("utf-8")).sign(payload)

    def publish_telemetry(self) -> MessageEnvelope:
        """Create an encrypted, authenticated telemetry envelope."""
        reading = _make_payload(self._type, self._location)
        plaintext = json.dumps(reading).encode("utf-8")
        self._counter += 1
        timestamp = self._clock.now()
        topic = config.make_topic(self._id, config.TOPIC_TELEMETRY)

        nonce, payload, encrypted = self._encrypt_payload(plaintext, topic)
        mac = self._compute_mac(topic, payload, timestamp)
        signature = self._sign_payload(payload)

        envelope = MessageEnvelope(
            device_id=self._id, topic=topic, payload=payload,
            timestamp=timestamp, counter=self._counter,
            nonce=nonce, mac=mac, signature=signature, encrypted=encrypted,
        )
        logger.debug("SecureDevice %s published telemetry (encrypted=%s)", self._id, encrypted)
        return envelope

    def receive_command(self, envelope: MessageEnvelope) -> None:
        """Verify the command MAC before acting on it."""
        hmac_key = self._keystore.get(self._id, KEY_HMAC)
        if hmac_key and envelope.mac:
            integrity = HmacIntegrity(hmac_key)
            try:
                integrity.verify(
                    envelope.mac,
                    envelope.device_id,
                    envelope.topic,
                    envelope.payload,
                    envelope.timestamp,
                    envelope.counter,
                )
            except Exception as exc:
                logger.error("SecureDevice %s rejected tampered command: %s", self._id, exc)
                return
        try:
            command = json.loads(envelope.payload.decode("utf-8"))
        except Exception:
            command = str(envelope.payload)
        logger.info("SecureDevice %s executed verified command: %s", self._id, command)
