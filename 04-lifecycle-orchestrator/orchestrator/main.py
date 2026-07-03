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

# HR event ingestion endpoint, goes through the model validation and parsing before upserting to the database
@app.post("/hr/events", status_code=201)
def ingest_hr_event(event: HREvent):
    #(model_dump() turns the Pydantic model into a dict for the person parameter.)
    incoming = event.model_dump()

    with db.get_connection(DATABASE_PATH) as conn:

        existing = db.get_person_by_id(conn, incoming["employee_id"])  # Row | None depending on if the employee exists
        result = engine.process_hr_event(existing, incoming)
        # result["event_type"], result["plan"]
        db.upsert_person(conn, incoming)
        conn.commit()

    return {"event_type": result["event_type"], "plan": result["plan"]}
