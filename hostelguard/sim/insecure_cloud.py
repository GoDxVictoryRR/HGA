"""
hostelguard/sim/insecure_cloud.py
Intentionally insecure cloud service implementation.

*** THIS MODULE IS INTENTIONALLY INSECURE AND FOR SIMULATION ONLY ***
*** Do not use this code in any real system. ***

The insecure cloud service:
- Stores telemetry in plaintext in SQLite.
- Performs no password hashing (passwords stored as-is).
- Issues no real tokens; any string is accepted as a valid token.
- Applies no RBAC; any logged-in user can query or admin anything.
- Has no audit log.
"""

import logging
from typing import Any, Dict, List

from hostelguard.db import Database
from hostelguard.sim.interfaces import CloudServiceBase
from hostelguard.sim.messages import MessageEnvelope

logger = logging.getLogger(__name__)

# DDL for the insecure cloud database tables
_CREATE_TELEMETRY = """
CREATE TABLE IF NOT EXISTS telemetry (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id TEXT NOT NULL,
    topic     TEXT NOT NULL,
    payload   TEXT NOT NULL,
    timestamp REAL NOT NULL
)
"""

_CREATE_USERS = """
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password TEXT NOT NULL,
    role     TEXT NOT NULL
)
"""


class InsecureCloudService(CloudServiceBase):
    """Cloud back-end with no security.

    Telemetry is stored as plaintext JSON.
    Passwords are stored as plaintext.
    Any non-empty string serves as a valid session token.
    """

    def __init__(self, db: Database) -> None:
        self._db = db
        self._setup_tables()
        self._seed_users()

    def _setup_tables(self) -> None:
        """Create database tables if they do not exist."""
        self._db.execute(_CREATE_TELEMETRY)
        self._db.execute(_CREATE_USERS)

    def _seed_users(self) -> None:
        """Add default users if the table is empty."""
        existing = self._db.fetchone("SELECT COUNT(*) as cnt FROM users")
        if existing and existing["cnt"] == 0:
            users = [
                ("warden", "warden123", "warden"),
                ("tech1", "tech1pass", "technician"),
                ("student1", "stu1pass", "student"),
            ]
            self._db.executemany(
                "INSERT OR IGNORE INTO users (username, password, role) VALUES (?,?,?)",
                users,
            )

    def ingest(self, envelope: MessageEnvelope) -> None:
        """Store a telemetry message as plaintext."""
        payload_str = envelope.payload.decode("utf-8", errors="replace")
        self._db.execute(
            "INSERT INTO telemetry (device_id, topic, payload, timestamp) VALUES (?,?,?,?)",
            (envelope.device_id, envelope.topic, payload_str, envelope.timestamp),
        )
        logger.debug("Cloud stored telemetry from %s", envelope.device_id)

    def login(self, username: str, password: str) -> str:
        """Return a trivial 'token' (the username) without real auth.

        In the insecure mode, ANY username:password pair where the password
        matches the plaintext stored value is accepted.  The returned token
        is simply the username string.
        """
        row = self._db.fetchone(
            "SELECT password FROM users WHERE username = ?", (username,)
        )
        if row and row["password"] == password:
            logger.info("Insecure login OK for %s (plaintext password match)", username)
            return username  # trivial token = username
        logger.warning("Insecure login FAILED for %s", username)
        raise ValueError(f"Invalid credentials for {username}")

    def query(self, token: str, query_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Return telemetry records; no RBAC check, any token accepted."""
        device_id = query_params.get("device_id")
        if device_id:
            rows = self._db.fetchall(
                "SELECT * FROM telemetry WHERE device_id = ? ORDER BY timestamp DESC LIMIT 50",
                (device_id,),
            )
        else:
            rows = self._db.fetchall(
                "SELECT * FROM telemetry ORDER BY timestamp DESC LIMIT 50"
            )
        return [dict(r) for r in rows]

    def admin(self, token: str, action: str, params: Dict[str, Any]) -> Any:
        """Perform admin actions without verifying the token is an admin."""
        if action == "add_user":
            self._db.execute(
                "INSERT OR REPLACE INTO users (username, password, role) VALUES (?,?,?)",
                (params["username"], params["password"], params.get("role", "student")),
            )
            return {"status": "user_added"}
        elif action == "list_users":
            rows = self._db.fetchall("SELECT username, role FROM users")
            return [dict(r) for r in rows]
        return {"status": "unknown_action"}
