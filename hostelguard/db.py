"""
hostelguard/db.py
Database helper wrapping sqlite3 for the whole project.

Rules:
- All queries use parameterized statements (no string formatting of user data).
- Each module adds its own tables by calling create_tables() with its DDL.
- The database file lives under outputs/ and is re-created on reset().
- Connections are closed explicitly (important on Windows file locking).
"""

import sqlite3
import pathlib
import logging
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)


class Database:
    """Thin wrapper around a SQLite database file.

    Usage::

        db = Database(path)
        db.execute("CREATE TABLE IF NOT EXISTS t (id TEXT PRIMARY KEY)")
        db.execute("INSERT INTO t VALUES (?)", ("hello",))
        rows = db.fetchall("SELECT * FROM t")
        db.close()
    """

    def __init__(self, path: pathlib.Path) -> None:
        self._path = path
        # Ensure the parent directory exists
        path.parent.mkdir(parents=True, exist_ok=True)
        self._conn: Optional[sqlite3.Connection] = None
        self._connect()

    def _connect(self) -> None:
        """Open the database connection with safe settings."""
        self._conn = sqlite3.connect(str(self._path), check_same_thread=False)
        # Return rows as sqlite3.Row so columns are accessible by name
        self._conn.row_factory = sqlite3.Row
        # Enable WAL mode for better concurrency on Windows
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")

    def execute(self, sql: str, params: Tuple = ()) -> sqlite3.Cursor:
        """Execute a single parameterized SQL statement and commit."""
        cursor = self._conn.execute(sql, params)
        self._conn.commit()
        return cursor

    def executemany(self, sql: str, param_list: List[Tuple]) -> None:
        """Execute a parameterized statement for each tuple in param_list."""
        self._conn.executemany(sql, param_list)
        self._conn.commit()

    def fetchall(self, sql: str, params: Tuple = ()) -> List[sqlite3.Row]:
        """Return all rows for a SELECT query."""
        return self._conn.execute(sql, params).fetchall()

    def fetchone(self, sql: str, params: Tuple = ()) -> Optional[sqlite3.Row]:
        """Return the first row for a SELECT query, or None."""
        return self._conn.execute(sql, params).fetchone()

    def reset(self) -> None:
        """Drop the database file and reconnect with an empty database.

        Called at the start of each demo run so previous data does not bleed
        into new results.
        """
        self.close()
        if self._path.exists():
            self._path.unlink()
        self._connect()
        logger.info("Database reset: %s", self._path)

    def close(self) -> None:
        """Close the connection cleanly (required on Windows)."""
        if self._conn is not None:
            self._conn.close()
            self._conn = None
