"""
hostelguard/access/_cloud_schema.py
SQL DDL strings for the SecureCloudService tables.

Separated here to keep secure_cloud.py under 250 lines.
"""

CREATE_TELEMETRY = """
CREATE TABLE IF NOT EXISTS secure_telemetry (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id   TEXT NOT NULL,
    topic       TEXT NOT NULL,
    payload_enc TEXT NOT NULL,
    nonce_hex   TEXT NOT NULL,
    timestamp   REAL NOT NULL
)
"""

CREATE_AUDIT = """
CREATE TABLE IF NOT EXISTS audit_log (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp REAL NOT NULL,
    actor     TEXT NOT NULL,
    action    TEXT NOT NULL,
    detail    TEXT NOT NULL,
    alert     INTEGER NOT NULL DEFAULT 0
)
"""

CREATE_LOCKOUTS = """
CREATE TABLE IF NOT EXISTS login_attempts (
    username      TEXT PRIMARY KEY,
    attempts      INTEGER NOT NULL DEFAULT 0,
    lockout_until REAL    NOT NULL DEFAULT 0
)
"""
