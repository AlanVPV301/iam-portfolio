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
#Query for inserting an user
create_user_query = """
    INSERT INTO users (id, username, display_name)
    VALUES (?, ?, ?)
"""

insert_credential_query = """
    INSERT INTO credentials (credential_id, user_id, public_key, sign_count, transports)
    VALUES (?, ?, ?, ?, ?)    
"""

update_sign_count_query = """
    UPDATE credentials SET sign_count = ? WHERE credential_id = ?
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

def create_user(conn, user_id: str, username: str, display_name: str) -> None:
    conn.execute(create_user_query, (user_id, username, display_name))
    conn.commit()

def get_user_by_username(conn, username:str) -> dict | None:
    cursor = conn.execute("SELECT * FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    #Converts the row to a dict if it exists, otherwise returns None
    return dict(row) if row else None


def get_credentials_for_user(conn, user_id) -> dict | None:  
    cursor = conn.execute("SELECT * FROM credentials WHERE user_id = ?", (user_id,))
    rows = cursor.fetchall()
    return [dict(row) for row in rows]

def get_credential_by_id(conn, credential_id) -> dict | None:
    cursor = conn.execute("SELECT * FROM credentials WHERE credential_id = ?", (credential_id,))
    row = cursor.fetchone()
    #Converts the row to a dict if it exists, otherwise returns None
    return dict(row) if row else None


 # --- CREDENTIAL OPERATIONS ---
def save_credential(conn, credential_id: bytes, user_id: str, public_key: bytes, sign_count: int, transports: list):
    transports_json = json.dumps(transports)
    conn.execute(insert_credential_query, (credential_id, user_id,          public_key, sign_count, transports_json))
    conn.commit()

def update_sign_count(conn, credential_id, sign_count):
    conn.execute(update_sign_count_query, (sign_count, credential_id))
    conn.commit()
