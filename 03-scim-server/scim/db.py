import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DATABASE_PATH = "./data/scim.db"


SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    external_id         TEXT NOT NULL UNIQUE,
    user_name           TEXT UNIQUE,
    given_name          TEXT,
    family_name         TEXT,
    active              INTEGER NOT NULL,
    roles_json          TEXT NOT NULL
);
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
    return conn


def init_db(db_path: str | None = None) -> None:
    with get_connection(db_path) as conn:
        conn.executescript(SCHEMA)
        conn.commit()