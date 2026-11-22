"""
hostelguard/crypto/keystore.py
Secure key store: manages AES keys, HMAC keys and ECDSA key pairs.

Keys are stored as a JSON file under outputs/.  In a real system this would
be a hardware security module or a cloud key management service; here it is
a file for demonstration purposes.

Key generation always uses os.urandom (OS secure random source).
The seeded simulation RNG is never used for cryptographic material.
"""

import json
import logging
import os
import pathlib
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# Key type constants used as keys in the JSON store
KEY_AES = "aes"
KEY_HMAC = "hmac"
KEY_ECDSA_PRIVATE = "ecdsa_private"
KEY_ECDSA_PUBLIC = "ecdsa_public"
KEY_JWT_SECRET = "jwt_secret"


class KeyStore:
    """Simple file-backed key store.

    Keys are stored as hex strings (for byte keys) or PEM strings (for EC
    keys) in a JSON file.  The file is created if it does not exist.

    Usage::

        ks = KeyStore(pathlib.Path("outputs/keystore.json"))
        ks.set("device1", KEY_AES, AesGcmCipher.generate_key())
        key = ks.get("device1", KEY_AES)   # returns bytes
    """

    def __init__(self, path: pathlib.Path) -> None:
        self._path = path
        self._data: Dict[str, Dict[str, str]] = {}
        self._load()

    def _load(self) -> None:
        """Load the key store from disk if it exists."""
        if self._path.exists():
            try:
                with open(self._path, "r", encoding="utf-8") as fh:
                    self._data = json.load(fh)
                logger.debug("KeyStore loaded from %s", self._path)
            except Exception as exc:
                logger.warning("Could not load keystore: %s — starting empty", exc)
                self._data = {}
        else:
            self._data = {}

    def _save(self) -> None:
        """Persist the key store to disk."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._path, "w", encoding="utf-8") as fh:
            json.dump(self._data, fh, indent=2)

    def set(self, entity_id: str, key_type: str, value: bytes) -> None:
        """Store a key.  value must be bytes; stored as hex."""
        if entity_id not in self._data:
            self._data[entity_id] = {}
        if isinstance(value, bytes):
            self._data[entity_id][key_type] = value.hex()
        else:
            # PEM strings are stored as-is
            self._data[entity_id][key_type] = value
        self._save()

    def set_str(self, entity_id: str, key_type: str, value: str) -> None:
        """Store a string value (e.g., PEM keys)."""
        if entity_id not in self._data:
            self._data[entity_id] = {}
        self._data[entity_id][key_type] = value
        self._save()

    def get(self, entity_id: str, key_type: str) -> Optional[bytes]:
        """Retrieve a key as bytes, or None if not found."""
        entry = self._data.get(entity_id, {}).get(key_type)
        if entry is None:
            return None
        if isinstance(entry, str) and all(c in "0123456789abcdef" for c in entry) and len(entry) % 2 == 0:
            return bytes.fromhex(entry)
        return entry.encode("utf-8") if isinstance(entry, str) else entry

    def get_str(self, entity_id: str, key_type: str) -> Optional[str]:
        """Retrieve a string value (e.g., PEM keys)."""
        return self._data.get(entity_id, {}).get(key_type)

    def has(self, entity_id: str, key_type: str) -> bool:
        """Return True if the key exists in the store."""
        return key_type in self._data.get(entity_id, {})

    def reset(self) -> None:
        """Delete the keystore file and clear in-memory data."""
        self._data = {}
        if self._path.exists():
            self._path.unlink()
        logger.info("KeyStore reset")

    def provision_device(self, device_id: str) -> None:
        """Generate and store AES and HMAC keys for a device.

        Called during device registration.  Keys are generated with OS
        randomness.
        """
        from hostelguard.crypto.aes_gcm import AesGcmCipher
        from hostelguard.crypto.hmac_integrity import HmacIntegrity
        from hostelguard.crypto.ecdsa_signatures import generate_ec_keypair

        if not self.has(device_id, KEY_AES):
            self.set(device_id, KEY_AES, AesGcmCipher.generate_key())
        if not self.has(device_id, KEY_HMAC):
            self.set(device_id, KEY_HMAC, HmacIntegrity.generate_key())
        if not self.has(device_id, KEY_ECDSA_PRIVATE):
            priv_pem, pub_pem = generate_ec_keypair()
            self.set_str(device_id, KEY_ECDSA_PRIVATE, priv_pem.decode("utf-8"))
            self.set_str(device_id, KEY_ECDSA_PUBLIC, pub_pem.decode("utf-8"))
        logger.info("KeyStore: provisioned keys for %s", device_id)

    def get_jwt_secret(self) -> bytes:
        """Return the JWT signing secret, generating it if not present."""
        if not self.has("system", KEY_JWT_SECRET):
            secret = os.urandom(32)
            self.set("system", KEY_JWT_SECRET, secret)
        return self.get("system", KEY_JWT_SECRET)
