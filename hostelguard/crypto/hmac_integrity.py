"""
hostelguard/crypto/hmac_integrity.py
HMAC-SHA256 message authentication.

HMAC provides integrity: the recipient can verify that the message was not
modified in transit and that it came from someone who holds the shared key.

We use HMAC-SHA256 (a keyed hash function).  The MAC covers all security-
relevant fields of the MessageEnvelope so that none can be altered without
detection.
"""

import hashlib
import hmac as _hmac
import logging
import struct

from hostelguard.exceptions import TamperError

logger = logging.getLogger(__name__)


def _envelope_to_bytes_for_mac(device_id: str, topic: str, payload: bytes,
                                 timestamp: float, counter: int) -> bytes:
    """Deterministically serialise the fields that the MAC must cover.

    The fields are length-prefixed so that concatenation is unambiguous
    (prevents length-extension and field-boundary attacks).
    """
    parts = []
    for s in [device_id.encode(), topic.encode()]:
        parts.append(struct.pack(">I", len(s)) + s)
    parts.append(struct.pack(">I", len(payload)) + payload)
    parts.append(struct.pack(">d", timestamp))   # 8-byte double
    parts.append(struct.pack(">Q", counter))     # 8-byte unsigned int
    return b"".join(parts)


class HmacIntegrity:
    """Compute and verify HMAC-SHA256 tags for message envelopes.

    Usage::

        h = HmacIntegrity(shared_key)
        mac = h.compute(device_id, topic, payload, timestamp, counter)
        h.verify(mac, device_id, topic, payload, timestamp, counter)
        # raises TamperError if mac does not match
    """

    def __init__(self, key: bytes) -> None:
        self._key = key

    @staticmethod
    def generate_key() -> bytes:
        """Generate a fresh 32-byte HMAC key using OS randomness."""
        import os
        return os.urandom(32)

    def compute(self, device_id: str, topic: str, payload: bytes,
                timestamp: float, counter: int) -> bytes:
        """Return the HMAC-SHA256 tag for the given fields."""
        message = _envelope_to_bytes_for_mac(device_id, topic, payload, timestamp, counter)
        tag = _hmac.new(self._key, message, hashlib.sha256).digest()
        return tag

    def verify(self, expected_mac: bytes, device_id: str, topic: str,
               payload: bytes, timestamp: float, counter: int) -> None:
        """Verify the MAC.  Raises TamperError if it does not match.

        Uses hmac.compare_digest to prevent timing attacks.
        """
        computed = self.compute(device_id, topic, payload, timestamp, counter)
        if not _hmac.compare_digest(computed, expected_mac):
            raise TamperError("HMAC verification failed: message may have been tampered")
        logger.debug("HMAC verified OK for device %s", device_id)
