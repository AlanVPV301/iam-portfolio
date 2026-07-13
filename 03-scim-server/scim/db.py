import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from scim.models import SCIMUser

DATABASE_PATH = "./data/scim.db"


SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    external_id         TEXT NOT NULL UNIQUE,
    user_name           TEXT UNIQUE,
    given_name          TEXT,
    family_name         TEXT,
    active              INTEGER NOT NULL,
    roles_json          TEXT NOT NULL,
    created_at          TEXT NOT NULL,
    updated_at          TEXT NOT NULL
);
"""

#Query for inserting or updating a person (Employee)
create_user_query = """
    INSERT INTO users (id, external_id, user_name, given_name, family_name, active, roles_json, created_at, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
"""
update_user_query = """
    UPDATE users SET external_id = ?, user_name = ?, given_name = ?, family_name = ?, active = ?, roles_json = ?, updated_at = ?
    WHERE id = ?
"""

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()

#Connection to the database, either via a specified path or the default path configured in the config.py file
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


def get_user_by_external_id(conn, external_id) -> dict | None:  
    cursor = conn.execute("SELECT * FROM users WHERE external_id = ?", (external_id,))
    row = cursor.fetchone()
    #Converts the row to a dict if it exists, otherwise returns None
    return dict(row) if row else None

def get_user_by_user_name(conn, user_name: str) -> dict | None:
    cursor = conn.execute(
        "SELECT * FROM users WHERE user_name = ?",
        (user_name,),
    )
    row = cursor.fetchone()
    return dict(row) if row else None

def get_user_by_id(conn, user_id) -> dict | None:  
    cursor = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    #Converts the row to a dict if it exists, otherwise returns None
    return dict(row) if row else None


def create_user(conn, SCIMUser: SCIMUser) -> None:
    conn.execute(create_user_query, (SCIMUser.id, SCIMUser.externalId, SCIMUser.userName, SCIMUser.name.givenName, SCIMUser.name.familyName, SCIMUser.active, json.dumps(SCIMUser.roles) if SCIMUser.roles else "[]", utc_now(), utc_now()))
    conn.commit()

def update_user_row(conn, row: dict) -> None:
    conn.execute(
        update_user_query,
        (
            row["external_id"],
            row["user_name"],
            row["given_name"],
            row["family_name"],
            int(row["active"]),
            row["roles_json"],
            utc_now(),
            row["id"],
        ),
    )
    conn.commit()