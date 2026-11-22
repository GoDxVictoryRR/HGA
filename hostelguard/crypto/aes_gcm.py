"""
hostelguard/crypto/aes_gcm.py
AES-256-GCM authenticated encryption.

AES-GCM provides both confidentiality (no one can read the payload) and
integrity (any modification is detected).  We use 256-bit keys and 96-bit
(12-byte) random nonces.

Key management: keys are stored in and retrieved from the KeyStore.
Cryptographic randomness always comes from os.urandom, never from the
seeded simulation RNG.
"""

import os
import logging

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from hostelguard import config
from hostelguard.exceptions import EncryptionError

logger = logging.getLogger(__name__)


class AesGcmCipher:
    """Encrypt and decrypt bytes using AES-256-GCM.

    Usage::

        cipher = AesGcmCipher(key_bytes)   # key must be 32 bytes
        nonce, ciphertext = cipher.encrypt(plaintext, associated_data)
        plaintext = cipher.decrypt(nonce, ciphertext, associated_data)
    """

    def __init__(self, key: bytes) -> None:
        if len(key) != config.AES_KEY_SIZE:
            raise EncryptionError(
                f"AES key must be {config.AES_KEY_SIZE} bytes, got {len(key)}"
            )
        self._aesgcm = AESGCM(key)

    @staticmethod
    def generate_key() -> bytes:
        """Generate a fresh 256-bit AES key using OS randomness."""
        return os.urandom(config.AES_KEY_SIZE)

    @staticmethod
    def generate_nonce() -> bytes:
        """Generate a fresh 96-bit nonce using OS randomness."""
        return os.urandom(config.AES_NONCE_SIZE)

    def encrypt(self, plaintext: bytes, associated_data: bytes = b"") -> tuple:
        """Encrypt plaintext and return (nonce, ciphertext_with_tag).

        The nonce must be stored alongside the ciphertext and passed to
        decrypt().  The associated_data is authenticated but not encrypted.

        Returns
        -------
        (nonce, ciphertext) : (bytes, bytes)
        """
        nonce = self.generate_nonce()
        try:
            ciphertext = self._aesgcm.encrypt(nonce, plaintext, associated_data or None)
        except Exception as exc:
            raise EncryptionError(f"AES-GCM encryption failed: {exc}") from exc
        logger.debug("AES-GCM encrypted %d bytes -> %d bytes", len(plaintext), len(ciphertext))
        return nonce, ciphertext

    def decrypt(self, nonce: bytes, ciphertext: bytes, associated_data: bytes = b"") -> bytes:
        """Decrypt and verify ciphertext.

        Raises EncryptionError if the tag does not match (i.e., the data was
        tampered with or the wrong key was used).
        """
        try:
            plaintext = self._aesgcm.decrypt(nonce, ciphertext, associated_data or None)
        except Exception as exc:
            raise EncryptionError(f"AES-GCM decryption failed (possible tampering): {exc}") from exc
        logger.debug("AES-GCM decrypted %d bytes -> %d bytes", len(ciphertext), len(plaintext))
        return plaintext
