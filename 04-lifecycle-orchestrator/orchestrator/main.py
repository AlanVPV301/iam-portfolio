import json
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI

from orchestrator import db, engine
from orchestrator.models import HREvent

load_dotenv()

DATABASE_PATH = os.getenv("DATABASE_PATH", db.DATABASE_PATH)

app = FastAPI(
    title="FinFlow Lifecycle Orchestrator",
    description="HR-driven joiner / mover / leaver orchestration (Phase 1)",
    version="0.1.0",
)


@app.on_event("startup")
def startup() -> None:
    db.init_db(DATABASE_PATH)


# Health check endpoint
@app.get("/health")
def health():
    db_path = Path(DATABASE_PATH)
    return {
        "status": "ok",
        "phase": 1,
        "database_path": str(db_path.resolve()),
        "database_exists": db_path.exists(),
    }

@app.get("/persons")
def persons(employee_id: str | None = None):
    with db.get_connection(DATABASE_PATH) as conn:
        if employee_id:
            return db.get_person_by_id(conn, employee_id)
        else:
            return db.get_persons(conn)    
@app.get("/hr_events")
def hr_events(event_id: str | None = None):
    with db.get_connection(DATABASE_PATH) as conn:
        if event_id:
            return db.get_hr_event_by_event_id(conn, event_id)
        else:
            return db.get_hr_events(conn)    

@app.get("/audit_events")
def audit_events(employee_id: str | None = None):
    with db.get_connection(DATABASE_PATH) as conn:
        if employee_id:
            return db.get_audit_events(conn, employee_id)
        else:
            return db.get_audit_events(conn)    


# HR event ingestion endpoint, goes through the model validation and parsing before upserting to the database
@app.post("/hr/events", status_code=201)
def ingest_hr_event(event: HREvent):
    #(model_dump() turns the Pydantic model into a dict for the person parameter.)
    incoming = event.model_dump()

    with db.get_connection(DATABASE_PATH) as conn:
        existing_hr_event = db.get_hr_event_by_event_id(conn, incoming["event_id"])
        if existing_hr_event: # Row | None depending on if the event exists
            return {
                "event_type": existing_hr_event["event_type"],
                "plan": json.loads(existing_hr_event["plan_json"]),
                "event_id": existing_hr_event["event_id"],
                "hr_event_id": existing_hr_event["id"],
                "idempotent_replay": True,   # optional — makes debugging obvious
            } # If the event has already been processed, return an error and the event data
        existing = db.get_person_by_id(conn, incoming["employee_id"])  # Row | None depending on if the employee exists
        result = engine.process_hr_event(existing, incoming) # result["event_type"], result["plan"]
        db.upsert_person(conn, incoming)
        hr_event_id = db.insert_hr_event(
            conn,
            incoming["event_id"],
            incoming["employee_id"],
            result["event_type"],
            result["plan"],
        )
        db.insert_audit_event(
            conn,
            hr_event_id,
            incoming["employee_id"],
            "jml_detected",
            {"event_type": result["event_type"]},
        )
        db.insert_audit_event(
            conn,
            hr_event_id,
            incoming["employee_id"],
            "plan_computed",
            result["plan"],
        )
        db.insert_audit_event(
            conn,
            hr_event_id,
            incoming["employee_id"],
            "person_upserted",
            {
                "employee_id": incoming["employee_id"],
                "department": incoming["department"],
                "email": incoming["email"],
                "status": incoming["status"],
            },
        )
        db.insert_audit_event(
            conn,
            hr_event_id,
            incoming["employee_id"],
            "hr_event_completed",
            {
                "hr_event_id": hr_event_id,
                "event_id": incoming["event_id"],
            },
        )
        conn.commit()

    return {
        "event_type": result["event_type"],
        "plan": result["plan"],
        "event_id": incoming["event_id"],
        "hr_event_id": hr_event_id,
    }
