"""
hostelguard/access/registry.py
Device and user registry with registration and revocation.

The registry keeps track of which devices and users are allowed to participate
in the system.  Registration provisions cryptographic keys; revocation removes
access and invalidates keys.

Stored in SQLite via the shared Database helper.
"""

import logging
from typing import List, Optional

import bcrypt

from hostelguard import config
from hostelguard.crypto.keystore import KeyStore
from hostelguard.db import Database
from hostelguard.exceptions import AuthenticationError, RegistrationError

logger = logging.getLogger(__name__)

_CREATE_DEVICES = """
CREATE TABLE IF NOT EXISTS registered_devices (
    device_id  TEXT PRIMARY KEY,
    device_type TEXT NOT NULL,
    location   TEXT NOT NULL,
    revoked    INTEGER NOT NULL DEFAULT 0
)
"""

_CREATE_USERS = """
CREATE TABLE IF NOT EXISTS registered_users (
    username    TEXT PRIMARY KEY,
    password_hash TEXT NOT NULL,
    role        TEXT NOT NULL,
    revoked     INTEGER NOT NULL DEFAULT 0
)
"""


class DeviceRegistry:
    """Manages device and user registration, revocation and authentication.

    Passwords are stored as bcrypt hashes (never plaintext).
    Device keys are provisioned in the KeyStore on registration.
    """

    # bcrypt work factor: use fast cost in test mode, normal cost in production.
    # The caller sets _bcrypt_cost before instantiation for tests.
    _bcrypt_cost: int = config.BCRYPT_COST_NORMAL

    def __init__(self, db: Database, keystore: KeyStore) -> None:
        self._db = db
        self._keystore = keystore
        self._db.execute(_CREATE_DEVICES)
        self._db.execute(_CREATE_USERS)
        self._seed_default_users()
        self._seed_default_devices()

    def _seed_default_users(self) -> None:
        """Add default users if the table is empty."""
        existing = self._db.fetchone(
            "SELECT COUNT(*) as cnt FROM registered_users"
        )
        if existing and existing["cnt"] == 0:
            defaults = [
                ("warden", "warden123", config.ROLE_WARDEN),
                ("tech1", "tech1pass", config.ROLE_TECHNICIAN),
                ("student1", "stu1pass", config.ROLE_STUDENT),
            ]
            for username, password, role in defaults:
                self.register_user(username, password, role)

    def _seed_default_devices(self) -> None:
        """Register all configured devices if not already registered."""
        for device_cfg in config.DEVICES:
            if not self.is_device_registered(device_cfg["id"]):
                self.register_device(
                    device_cfg["id"],
                    device_cfg["type"],
                    device_cfg["location"],
                )

    # --- Device management ---

    def register_device(self, device_id: str, device_type: str, location: str) -> None:
        """Register a device and provision its cryptographic keys."""
        try:
            self._db.execute(
                "INSERT INTO registered_devices (device_id, device_type, location) VALUES (?,?,?)",
                (device_id, device_type, location),
            )
        except Exception as exc:
            raise RegistrationError(f"Cannot register device {device_id}: {exc}") from exc
        self._keystore.provision_device(device_id)
        logger.info("Registered device: %s (%s @ %s)", device_id, device_type, location)

    def revoke_device(self, device_id: str) -> None:
        """Mark a device as revoked so it can no longer connect."""
        self._db.execute(
            "UPDATE registered_devices SET revoked = 1 WHERE device_id = ?",
            (device_id,),
        )
        logger.warning("Revoked device: %s", device_id)

    def is_device_registered(self, device_id: str) -> bool:
        """Return True if the device is registered and not revoked."""
        row = self._db.fetchone(
            "SELECT revoked FROM registered_devices WHERE device_id = ?",
            (device_id,),
        )
        return row is not None and row["revoked"] == 0

    # --- User management ---

    def register_user(self, username: str, password: str, role: str) -> None:
        """Register a user with a bcrypt-hashed password."""
        if role not in config.ALL_ROLES:
            raise RegistrationError(f"Unknown role: {role!r}")
        hashed = bcrypt.hashpw(
            password.encode("utf-8"),
            bcrypt.gensalt(rounds=self._bcrypt_cost),
        ).decode("utf-8")
        try:
            self._db.execute(
                "INSERT INTO registered_users (username, password_hash, role) VALUES (?,?,?)",
                (username, hashed, role),
            )
        except Exception as exc:
            raise RegistrationError(f"Cannot register user {username}: {exc}") from exc
        logger.info("Registered user: %s (role=%s)", username, role)

    def revoke_user(self, username: str) -> None:
        """Mark a user as revoked so they can no longer log in."""
        self._db.execute(
            "UPDATE registered_users SET revoked = 1 WHERE username = ?",
            (username,),
        )
        logger.warning("Revoked user: %s", username)

    def authenticate_user(self, username: str, password: str) -> str:
        """Verify credentials and return the user's role.

        Raises AuthenticationError on failure.
        """
        row = self._db.fetchone(
            "SELECT password_hash, role, revoked FROM registered_users WHERE username = ?",
            (username,),
        )
        if row is None:
            raise AuthenticationError(f"Unknown user: {username}")
        if row["revoked"]:
            raise AuthenticationError(f"User account revoked: {username}")
        if not bcrypt.checkpw(password.encode("utf-8"), row["password_hash"].encode("utf-8")):
            raise AuthenticationError("Invalid password")
        logger.info("User authenticated: %s (role=%s)", username, row["role"])
        return row["role"]

    def get_user_role(self, username: str) -> Optional[str]:
        """Return the role of a registered user, or None if not found."""
        row = self._db.fetchone(
            "SELECT role, revoked FROM registered_users WHERE username = ?",
            (username,),
        )
        if row is None or row["revoked"]:
            return None
        return row["role"]

    def list_devices(self) -> List[dict]:
        """Return a list of all registered (non-revoked) devices."""
        rows = self._db.fetchall(
            "SELECT device_id, device_type, location FROM registered_devices WHERE revoked = 0"
        )
        return [dict(r) for r in rows]

    def list_users(self) -> List[dict]:
        """Return a list of all registered (non-revoked) users."""
        rows = self._db.fetchall(
            "SELECT username, role FROM registered_users WHERE revoked = 0"
        )
        return [dict(r) for r in rows]
