"""
hostelguard/sim/messages.py
Message envelope used throughout the simulated network.

Every message on the simulated wire is a MessageEnvelope.  The envelope
carries the payload plus security fields that are added by the crypto and
access layers.  It can be serialized to bytes (for the wire) and back.

Fields
------
device_id   : str   - ID of the originating device
topic       : str   - routing topic, e.g. "rfid_main_gate/telemetry"
payload     : bytes - the actual data (may be ciphertext if encrypted=True)
timestamp   : float - UNIX timestamp set by the sender
counter     : int   - monotonically increasing per-device counter for replay
                      protection; zero in the insecure mode
nonce       : bytes - AES-GCM nonce; empty bytes if not encrypted
mac         : bytes - HMAC-SHA256 of the envelope fields; empty if not set
signature   : bytes - ECDSA signature; empty if not set
encrypted   : bool  - True if payload is ciphertext
"""

import json
import struct
from dataclasses import dataclass, field


@dataclass
class MessageEnvelope:
    """One message travelling across the simulated wire."""

    device_id: str
    topic: str
    payload: bytes
    timestamp: float
    counter: int = 0
    nonce: bytes = field(default_factory=bytes)
    mac: bytes = field(default_factory=bytes)
    signature: bytes = field(default_factory=bytes)
    encrypted: bool = False

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    def to_bytes(self) -> bytes:
        """Serialize the envelope to a compact byte string.

        Format: a JSON dict where bytes fields are stored as hex strings.
        A 4-byte big-endian length prefix allows framing on the wire.
        """
        d = {
            "device_id": self.device_id,
            "topic": self.topic,
            "payload": self.payload.hex(),
            "timestamp": self.timestamp,
            "counter": self.counter,
            "nonce": self.nonce.hex(),
            "mac": self.mac.hex(),
            "signature": self.signature.hex(),
            "encrypted": self.encrypted,
        }
        body = json.dumps(d, separators=(",", ":")).encode("utf-8")
        # Prefix with 4-byte big-endian length for easy parsing
        return struct.pack(">I", len(body)) + body

    @staticmethod
    def from_bytes(data: bytes) -> "MessageEnvelope":
        """Deserialize an envelope produced by to_bytes().

        The 4-byte length prefix is consumed automatically.
        """
        # Strip the length prefix if present
        if len(data) >= 4:
            length = struct.unpack(">I", data[:4])[0]
            body = data[4:4 + length]
        else:
            body = data
        d = json.loads(body.decode("utf-8"))
        return MessageEnvelope(
            device_id=d["device_id"],
            topic=d["topic"],
            payload=bytes.fromhex(d["payload"]),
            timestamp=d["timestamp"],
            counter=d["counter"],
            nonce=bytes.fromhex(d["nonce"]),
            mac=bytes.fromhex(d["mac"]),
            signature=bytes.fromhex(d["signature"]),
            encrypted=d["encrypted"],
        )

    def copy(self) -> "MessageEnvelope":
        """Return a shallow copy of this envelope."""
        return MessageEnvelope(
            device_id=self.device_id,
            topic=self.topic,
            payload=bytes(self.payload),
            timestamp=self.timestamp,
            counter=self.counter,
            nonce=bytes(self.nonce),
            mac=bytes(self.mac),
            signature=bytes(self.signature),
            encrypted=self.encrypted,
        )
