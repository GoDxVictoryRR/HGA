"""
tests/test_crypto.py
Tests for Module 2: AES-GCM, HMAC, ECDSA, KeyStore.
"""

import os
import pytest

from hostelguard.crypto.aes_gcm import AesGcmCipher
from hostelguard.crypto.hmac_integrity import HmacIntegrity
from hostelguard.crypto.ecdsa_signatures import EcdsaSigner, EcdsaVerifier, generate_ec_keypair
from hostelguard.crypto.keystore import KeyStore, KEY_AES, KEY_HMAC
from hostelguard.exceptions import EncryptionError, TamperError


# ---------------------------------------------------------------------------
# AES-GCM
# ---------------------------------------------------------------------------

def test_aes_gcm_encrypt_decrypt_roundtrip():
    key = AesGcmCipher.generate_key()
    cipher = AesGcmCipher(key)
    plaintext = b"Hello, HostelGuard!"
    nonce, ciphertext = cipher.encrypt(plaintext)
    recovered = cipher.decrypt(nonce, ciphertext)
    assert recovered == plaintext


def test_aes_gcm_ciphertext_different_from_plaintext():
    key = AesGcmCipher.generate_key()
    cipher = AesGcmCipher(key)
    plaintext = b"sensor_data_1234"
    nonce, ciphertext = cipher.encrypt(plaintext)
    assert ciphertext != plaintext


def test_aes_gcm_tamper_raises():
    key = AesGcmCipher.generate_key()
    cipher = AesGcmCipher(key)
    nonce, ciphertext = cipher.encrypt(b"original")
    tampered = ciphertext[:-1] + bytes([ciphertext[-1] ^ 0xFF])
    with pytest.raises(EncryptionError):
        cipher.decrypt(nonce, tampered)


def test_aes_gcm_wrong_key_raises():
    key1 = AesGcmCipher.generate_key()
    key2 = AesGcmCipher.generate_key()
    cipher1 = AesGcmCipher(key1)
    cipher2 = AesGcmCipher(key2)
    nonce, ciphertext = cipher1.encrypt(b"secret")
    with pytest.raises(EncryptionError):
        cipher2.decrypt(nonce, ciphertext)


def test_aes_gcm_associated_data_authenticated():
    key = AesGcmCipher.generate_key()
    cipher = AesGcmCipher(key)
    nonce, ct = cipher.encrypt(b"data", b"device1:topic")
    # Correct associated data works
    assert cipher.decrypt(nonce, ct, b"device1:topic") == b"data"
    # Wrong associated data fails
    with pytest.raises(EncryptionError):
        cipher.decrypt(nonce, ct, b"wrong:topic")


def test_aes_gcm_key_wrong_size():
    with pytest.raises(EncryptionError):
        AesGcmCipher(b"tooshort")


def test_aes_gcm_each_encryption_uses_fresh_nonce():
    key = AesGcmCipher.generate_key()
    cipher = AesGcmCipher(key)
    nonce1, _ = cipher.encrypt(b"data")
    nonce2, _ = cipher.encrypt(b"data")
    assert nonce1 != nonce2  # nonces must differ (OS randomness)


# ---------------------------------------------------------------------------
# HMAC
# ---------------------------------------------------------------------------

def test_hmac_compute_and_verify():
    key = HmacIntegrity.generate_key()
    h = HmacIntegrity(key)
    mac = h.compute("d1", "d1/telemetry", b"payload", 1.0, 1)
    h.verify(mac, "d1", "d1/telemetry", b"payload", 1.0, 1)  # must not raise


def test_hmac_modified_payload_raises():
    key = HmacIntegrity.generate_key()
    h = HmacIntegrity(key)
    mac = h.compute("d1", "d1/telemetry", b"original", 1.0, 1)
    with pytest.raises(TamperError):
        h.verify(mac, "d1", "d1/telemetry", b"tampered", 1.0, 1)


def test_hmac_wrong_key_raises():
    key1 = HmacIntegrity.generate_key()
    key2 = HmacIntegrity.generate_key()
    mac = HmacIntegrity(key1).compute("d1", "d1/t", b"data", 1.0, 1)
    with pytest.raises(TamperError):
        HmacIntegrity(key2).verify(mac, "d1", "d1/t", b"data", 1.0, 1)


def test_hmac_modified_counter_raises():
    key = HmacIntegrity.generate_key()
    h = HmacIntegrity(key)
    mac = h.compute("d1", "d1/t", b"data", 1.0, 1)
    with pytest.raises(TamperError):
        h.verify(mac, "d1", "d1/t", b"data", 1.0, 2)  # counter changed


# ---------------------------------------------------------------------------
# ECDSA
# ---------------------------------------------------------------------------

def test_ecdsa_sign_and_verify():
    priv_pem, pub_pem = generate_ec_keypair()
    signer = EcdsaSigner(priv_pem)
    verifier = EcdsaVerifier(pub_pem)
    data = b"message to sign"
    sig = signer.sign(data)
    verifier.verify(sig, data)  # must not raise


def test_ecdsa_tampered_data_raises():
    priv_pem, pub_pem = generate_ec_keypair()
    signer = EcdsaSigner(priv_pem)
    verifier = EcdsaVerifier(pub_pem)
    sig = signer.sign(b"original")
    with pytest.raises(TamperError):
        verifier.verify(sig, b"tampered")


def test_ecdsa_wrong_key_raises():
    priv1, pub1 = generate_ec_keypair()
    priv2, pub2 = generate_ec_keypair()
    sig = EcdsaSigner(priv1).sign(b"data")
    with pytest.raises(TamperError):
        EcdsaVerifier(pub2).verify(sig, b"data")


# ---------------------------------------------------------------------------
# KeyStore
# ---------------------------------------------------------------------------

def test_keystore_set_and_get(tmp_path):
    ks = KeyStore(tmp_path / "ks.json")
    key = os.urandom(32)
    ks.set("device1", KEY_AES, key)
    retrieved = ks.get("device1", KEY_AES)
    assert retrieved == key


def test_keystore_provision_device_creates_keys(tmp_path):
    ks = KeyStore(tmp_path / "ks.json")
    ks.provision_device("rfid_main_gate")
    assert ks.get("rfid_main_gate", KEY_AES) is not None
    assert ks.get("rfid_main_gate", KEY_HMAC) is not None


def test_keystore_reset_clears_keys(tmp_path):
    ks = KeyStore(tmp_path / "ks.json")
    ks.set("device1", KEY_AES, os.urandom(32))
    ks.reset()
    assert ks.get("device1", KEY_AES) is None


def test_keystore_persists_across_instances(tmp_path):
    path = tmp_path / "ks.json"
    key = os.urandom(32)
    ks1 = KeyStore(path)
    ks1.set("d1", KEY_AES, key)
    ks2 = KeyStore(path)
    assert ks2.get("d1", KEY_AES) == key


def test_keystore_jwt_secret_stable(tmp_path):
    ks = KeyStore(tmp_path / "ks.json")
    s1 = ks.get_jwt_secret()
    s2 = ks.get_jwt_secret()
    assert s1 == s2  # same secret each call
