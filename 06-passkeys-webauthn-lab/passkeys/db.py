import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DATABASE_PATH = "./data/passkeys.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,               -- Unique user ID (WebAuthn requires a random byte array, typically stored as a string/hex)
    username TEXT UNIQUE NOT NULL,     -- User-facing login identifier (e.g., email)
    display_name TEXT NOT NULL          -- Friendly name (e.g., "John Doe")
);

CREATE TABLE IF NOT EXISTS credentials (
    credential_id BLOB PRIMARY KEY,    -- Unique ID of the credential returned by the authenticator
    user_id TEXT NOT NULL,             -- Foreign key referencing users(id)
    public_key BLOB NOT NULL,          -- The public key used to verify assertions
    sign_count INTEGER NOT NULL,       -- Keeps track of signatures to prevent clone attacks
    transports TEXT,                   -- JSON-encoded array or CSV string (e.g., '["usb", "nfc", "internal"]')
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);
"""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()

#Connection to the database, either via a specified path or the default path configured in the ENV file
def get_connection(db_path: str | None = None) -> sqlite3.Connection:
    path = Path(db_path or DATABASE_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)
    conn.commit()
    return conn


def init_db(db_path: str | None = None) -> None:
    with get_connection(db_path):
        pass
