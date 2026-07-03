import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DATABASE_PATH = "./data/orchestrator.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS persons (
    employee_id TEXT PRIMARY KEY,
    email         TEXT NOT NULL UNIQUE,
    first_name    TEXT NOT NULL,
    last_name     TEXT NOT NULL,
    department    TEXT NOT NULL,
    job_title     TEXT,
    status        TEXT NOT NULL,
    manager_id    TEXT,
    updated_at    TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS jobs (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id    TEXT NOT NULL UNIQUE,
    employee_id TEXT NOT NULL,
    event_type  TEXT NOT NULL,
    status      TEXT NOT NULL,
    plan_json   TEXT NOT NULL DEFAULT '{}',
    created_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id      INTEGER,
    employee_id TEXT,
    action      TEXT NOT NULL,
    detail_json TEXT NOT NULL DEFAULT '{}',
    created_at  TEXT NOT NULL
);
"""
#Query for inserting or updating a person (Employee)
upsert_query = """
    INSERT INTO persons (employee_id, email, first_name, last_name, department, job_title, status, manager_id, updated_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(employee_id) DO UPDATE SET
        email = excluded.email,
        first_name = excluded.first_name,
        last_name = excluded.last_name,
        department = excluded.department,
        job_title = excluded.job_title,
        status = excluded.status,
        manager_id = excluded.manager_id,
        updated_at = excluded.updated_at
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

def get_person_by_id(conn, employee_id) -> dict | None:  
    cursor = conn.execute("SELECT * FROM persons WHERE employee_id = ?", (employee_id,))
    row = cursor.fetchone()
    #Converts the row to a dict if it exists, otherwise returns None
    return dict(row) if row else None

def upsert_person(conn, person: dict) -> None:
    conn.execute(
        upsert_query,
        (
            person["employee_id"],
            person["email"],
            person["first_name"],
            person["last_name"],
            person["department"],
            person["job_title"],
            person["status"],
            person["manager_id"],
            utc_now(),
        ),
    )