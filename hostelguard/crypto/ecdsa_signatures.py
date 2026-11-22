"""
hostelguard/crypto/ecdsa_signatures.py
ECDSA digital signatures using the P-256 (secp256r1) curve.

Digital signatures provide non-repudiation: only the device that holds the
private key can produce a valid signature, so the recipient knows the
message genuinely came from that device.

Each device has a key pair.  The private key stays on the device; the public
key is registered in the key store so the broker can verify signatures.
"""

import logging

from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.exceptions import InvalidSignature

from hostelguard.exceptions import TamperError

logger = logging.getLogger(__name__)


class EcdsaSigner:
    """Sign bytes with an ECDSA P-256 private key.

    Usage::

        signer = EcdsaSigner(private_key_pem_bytes)
        sig = signer.sign(data)
    """

    def __init__(self, private_key_pem: bytes) -> None:
        self._private_key = serialization.load_pem_private_key(
            private_key_pem, password=None
        )

    def sign(self, data: bytes) -> bytes:
        """Return a DER-encoded ECDSA signature over data."""
        signature = self._private_key.sign(data, ec.ECDSA(hashes.SHA256()))
        logger.debug("ECDSA signature produced (%d bytes)", len(signature))
        return signature

    def get_public_key_pem(self) -> bytes:
        """Return the public key as PEM bytes for sharing."""
        return self._private_key.public_key().public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )


class EcdsaVerifier:
    """Verify ECDSA P-256 signatures with a public key.

    Usage::

        verifier = EcdsaVerifier(public_key_pem_bytes)
        verifier.verify(sig, data)   # raises TamperError on failure
    """

    def __init__(self, public_key_pem: bytes) -> None:
        self._public_key = serialization.load_pem_public_key(public_key_pem)

    def verify(self, signature: bytes, data: bytes) -> None:
        """Verify signature over data.  Raises TamperError on failure."""
        try:
            self._public_key.verify(signature, data, ec.ECDSA(hashes.SHA256()))
        except InvalidSignature as exc:
            raise TamperError("ECDSA signature verification failed") from exc
        logger.debug("ECDSA signature verified OK")


def generate_ec_keypair() -> tuple:
    """Generate a fresh P-256 key pair.

    Returns
    -------
    (private_key_pem, public_key_pem) : (bytes, bytes)
    Both as PEM-encoded bytes.
    """
    private_key = ec.generate_private_key(ec.SECP256R1())
    private_pem = private_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    public_pem = private_key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return private_pem, public_pem
