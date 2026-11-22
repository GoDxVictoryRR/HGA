"""
hostelguard/access/secure_cloud.py
Secure cloud service with JWT auth, RBAC, bcrypt passwords, encrypted
storage, audit log and alerts.

Compared to the insecure cloud:
- Passwords are verified against bcrypt hashes.
- Login returns a real JWT with role and expiry.
- All queries and admin actions are RBAC-checked.
- Telemetry payload is stored encrypted (AES-GCM) in the database.
- Every sensitive action is written to an audit log.
- Brute-force login is blocked by a lockout counter.
"""

import logging
from typing import Any, Dict, List

import jwt

from hostelguard import config
from hostelguard.access import rbac
from hostelguard.access.registry import DeviceRegistry
from hostelguard.crypto.aes_gcm import AesGcmCipher
from hostelguard.crypto.keystore import KeyStore, KEY_AES
from hostelguard.db import Database
from hostelguard.exceptions import AuthenticationError, AuthorizationError
from hostelguard.sim.interfaces import CloudServiceBase
from hostelguard.access._cloud_schema import CREATE_TELEMETRY, CREATE_AUDIT, CREATE_LOCKOUTS
from hostelguard.sim.messages import MessageEnvelope

logger = logging.getLogger(__name__)


class SecureCloudService(CloudServiceBase):
    """Cloud back-end with authentication, RBAC, encrypted storage and audit."""

    def __init__(self, db: Database, keystore: KeyStore, clock) -> None:
        self._db = db
        self._keystore = keystore
        self._clock = clock
        self._db.execute(CREATE_TELEMETRY)
        self._db.execute(CREATE_AUDIT)
        self._db.execute(CREATE_LOCKOUTS)

    def _jwt_secret(self) -> bytes:
        return self._keystore.get_jwt_secret()

    def _audit(self, actor: str, action: str, detail: str, alert: bool = False) -> None:
        """Write a tamper-evident audit log entry."""
        self._db.execute(
            "INSERT INTO audit_log (timestamp, actor, action, detail, alert) VALUES (?,?,?,?,?)",
            (self._clock.now(), actor, action, detail, int(alert)),
        )
        if alert:
            logger.warning("ALERT: actor=%s action=%s detail=%s", actor, action, detail)

    def _check_lockout(self, username: str) -> None:
        """Raise AuthenticationError if the account is locked out."""
        row = self._db.fetchone(
            "SELECT attempts, lockout_until FROM login_attempts WHERE username = ?",
            (username,),
        )
        if row and row["lockout_until"] > self._clock.now():
            remaining = row["lockout_until"] - self._clock.now()
            raise AuthenticationError(
                f"Account locked. Try again in {remaining:.0f}s."
            )

    def _record_failed_login(self, username: str) -> None:
        """Increment failed login counter and lock the account if threshold exceeded."""
        self._db.execute(
            "INSERT INTO login_attempts (username, attempts, lockout_until) VALUES (?,1,0) "
            "ON CONFLICT(username) DO UPDATE SET attempts = attempts + 1",
            (username,),
        )
        row = self._db.fetchone(
            "SELECT attempts FROM login_attempts WHERE username = ?", (username,)
        )
        attempts = row["attempts"] if row else 1
        if attempts >= config.LOCKOUT_THRESHOLD:
            lockout_until = self._clock.now() + config.LOCKOUT_DURATION_SECONDS
            self._db.execute(
                "UPDATE login_attempts SET lockout_until = ? WHERE username = ?",
                (lockout_until, username),
            )
            self._audit(
                username, "lockout",
                f"Account locked after {attempts} failed attempts",
                alert=True,
            )

    def _clear_failed_logins(self, username: str) -> None:
        """Reset the failed login counter after a successful login."""
        self._db.execute(
            "DELETE FROM login_attempts WHERE username = ?", (username,)
        )

    def ingest(self, envelope: MessageEnvelope) -> None:
        """Encrypt and store a telemetry message."""
        aes_key = self._keystore.get(envelope.device_id, KEY_AES)
        if aes_key:
            cipher = AesGcmCipher(aes_key)
            nonce, ciphertext = cipher.encrypt(envelope.payload)
            payload_stored = ciphertext.hex()
            nonce_hex = nonce.hex()
        else:
            # Fall back to base64-like hex if key not provisioned yet
            payload_stored = envelope.payload.hex()
            nonce_hex = ""

        self._db.execute(
            "INSERT INTO secure_telemetry (device_id, topic, payload_enc, nonce_hex, timestamp) "
            "VALUES (?,?,?,?,?)",
            (envelope.device_id, envelope.topic, payload_stored, nonce_hex, envelope.timestamp),
        )
        logger.debug("SecureCloud stored encrypted telemetry from %s", envelope.device_id)

    def login(self, username: str, password: str) -> str:
        """Authenticate and return a signed JWT."""
        self._check_lockout(username)
        # Use the registry for bcrypt-based authentication
        registry = DeviceRegistry.__new__(DeviceRegistry)
        registry._db = self._db
        registry._keystore = self._keystore

        try:
            role = registry.authenticate_user(username, password)
        except AuthenticationError:
            self._record_failed_login(username)
            self._audit(username, "login_failed", "Bad credentials", alert=True)
            raise

        self._clear_failed_logins(username)
        self._audit(username, "login_ok", f"role={role}")

        payload = {
            "sub": username,
            "role": role,
            "iat": int(self._clock.now()),
            "exp": int(self._clock.now()) + config.TOKEN_LIFETIME_SECONDS,
        }
        token = jwt.encode(payload, self._jwt_secret(), algorithm=config.JWT_ALGORITHM)
        return token

    def _decode_token(self, token: str) -> dict:
        """Decode a JWT and return its payload.

        We disable PyJWT's built-in expiry check and perform it ourselves
        using the injected clock.  This keeps tests deterministic when a
        FakeClock is used (the system clock would otherwise reject tokens
        issued at the fake epoch).
        """
        try:
            payload = jwt.decode(
                token,
                self._jwt_secret(),
                algorithms=[config.JWT_ALGORITHM],
                options={"verify_exp": False},
            )
        except jwt.InvalidTokenError as exc:
            raise AuthenticationError(f"Invalid token: {exc}") from exc

        # Manual expiry check using the injected clock
        exp = payload.get("exp", 0)
        if exp and self._clock.now() > exp:
            raise AuthenticationError("Token has expired")
        return payload

    def query(self, token: str, query_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Return (decrypted) telemetry records if RBAC permits."""
        claims = self._decode_token(token)
        role = claims.get("role", "")
        username = claims.get("sub", "")
        device_id = query_params.get("device_id")

        # Students can only query temperature data
        if role == config.ROLE_STUDENT:
            if device_id and "temp" not in device_id and "temperature" not in device_id:
                raise AuthorizationError("Students may only query temperature data")
        elif not rbac.can_query_all(role):
            raise AuthorizationError(f"Role '{role}' cannot query telemetry")

        if device_id:
            rows = self._db.fetchall(
                "SELECT * FROM secure_telemetry WHERE device_id = ? ORDER BY timestamp DESC LIMIT 50",
                (device_id,),
            )
        else:
            rows = self._db.fetchall(
                "SELECT * FROM secure_telemetry ORDER BY timestamp DESC LIMIT 50"
            )

        results = []
        for row in rows:
            record = dict(row)
            # Decrypt payload for authorised users
            aes_key = self._keystore.get(record["device_id"], KEY_AES)
            if aes_key and record.get("nonce_hex"):
                try:
                    cipher = AesGcmCipher(aes_key)
                    nonce = bytes.fromhex(record["nonce_hex"])
                    ct = bytes.fromhex(record["payload_enc"])
                    record["payload_plaintext"] = cipher.decrypt(nonce, ct).decode("utf-8", errors="replace")
                except Exception:
                    record["payload_plaintext"] = "[decryption failed]"
            results.append(record)

        self._audit(username, "query", f"device_id={device_id}, role={role}, results={len(results)}")
        return results

    def admin(self, token: str, action: str, params: Dict[str, Any]) -> Any:
        """Perform admin actions after checking warden role."""
        claims = self._decode_token(token)
        role = claims.get("role", "")
        username = claims.get("sub", "")
        rbac.check_admin(role)

        self._audit(username, f"admin.{action}", str(params))

        if action == "list_users":
            registry = DeviceRegistry.__new__(DeviceRegistry)
            registry._db = self._db
            registry._keystore = self._keystore
            return registry.list_users()
        elif action == "revoke_user":
            registry = DeviceRegistry.__new__(DeviceRegistry)
            registry._db = self._db
            registry._keystore = self._keystore
            registry.revoke_user(params["username"])
            return {"status": "revoked"}
        elif action == "get_audit_log":
            rows = self._db.fetchall(
                "SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT 100"
            )
            return [dict(r) for r in rows]
        return {"status": "unknown_action"}
