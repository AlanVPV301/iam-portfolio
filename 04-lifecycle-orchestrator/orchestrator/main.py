import asyncio
import json
import os
import secrets
import subprocess
from pathlib import Path

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from orchestrator import db, engine, locks
from orchestrator.models import HREvent
from orchestrator.connectors import scim



load_dotenv()

DATABASE_PATH = os.getenv("DATABASE_PATH", db.DATABASE_PATH)

# Inbound credential for this API — distinct from SCIM_BEARER_TOKEN, which is sent outbound
ORCHESTRATOR_BEARER_TOKEN = os.getenv("ORCHESTRATOR_BEARER_TOKEN")
if not ORCHESTRATOR_BEARER_TOKEN:
    raise RuntimeError("ORCHESTRATOR_BEARER_TOKEN is missing from .env")

security_scheme = HTTPBearer()


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security_scheme)):
    if not secrets.compare_digest(credentials.credentials, ORCHESTRATOR_BEARER_TOKEN):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials


app = FastAPI(
    title="FinFlow Lifecycle Orchestrator",
    description="HR-driven joiner / mover / leaver orchestration (Phase 2b — SCIM connector)",
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
        "phase": 2,
        "database_path": str(db_path.resolve()),
        "database_exists": db_path.exists(),
    }


@app.get("/persons")
def persons(employee_id: str | None = None, token: str = Depends(verify_token)):
    with db.get_connection(DATABASE_PATH) as conn:
        if employee_id:
            return db.get_person_by_id(conn, employee_id)
        return db.get_persons(conn)


@app.get("/hr_events")
def hr_events(event_id: str | None = None, token: str = Depends(verify_token)):
    with db.get_connection(DATABASE_PATH) as conn:
        if event_id:
            return db.get_hr_event_by_event_id(conn, event_id)
        return db.get_hr_events(conn)


@app.get("/audit_events")
def audit_events(employee_id: str | None = None, token: str = Depends(verify_token)):
    with db.get_connection(DATABASE_PATH) as conn:
        if employee_id:
            return db.get_audit_events(conn, employee_id)
        return db.get_audit_events(conn)


# HR event ingestion endpoint, goes through the model validation and parsing before upserting to the database
@app.post("/hr/events", status_code=201)
async def ingest_hr_event(event: HREvent, token: str = Depends(verify_token)):
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

    lock = locks.lock_for(incoming["employee_id"])
    if lock.locked():
        raise HTTPException(
            status_code=409,
            detail={
                "error": "identity_locked",
                "employee_id": incoming["employee_id"],
                "retry_after_seconds": locks.PROCESSING_SECONDS,
            },
            headers={"Retry-After": str(locks.PROCESSING_SECONDS)},
        )

    async with lock:
        await asyncio.sleep(locks.PROCESSING_SECONDS)  # simulate slow Entra/SCIM work

        with db.get_connection(DATABASE_PATH) as conn:
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
            
            scim_result = scim.provision_scim(result["event_type"], incoming, result["plan"])
            if scim_result.get("skipped"):
                db.insert_audit_event(conn, hr_event_id, incoming["employee_id"], "scim_skipped", scim_result)
            elif scim_result.get("scim_id"):
                db.insert_audit_event(conn, hr_event_id, incoming["employee_id"], "scim_provisioned", scim_result)
            else:
                # malformed success — treat as failure
                raise ValueError(f"unexpected SCIM result: {scim_result}")

            #ENTRA GRAPH PROVISIONING
            ROOT = Path(__file__).resolve().parents[1]  # 04-lifecycle-orchestrator/
            joiner_script_path = str(ROOT / "scripts" / "finflow-joiner.ps1")
            mover_script_path = str(ROOT / "scripts" / "finflow-mover.ps1")
            leaver_script_path = str(ROOT / "scripts" / "finflow-leaver.ps1")


            add_groups = result["plan"]["add"]["entra_groups"]
            remove_groups = result["plan"]["remove"]["entra_groups"]


            
            if result["event_type"] == "JOINER":
                command = [
                    "pwsh",
                    "-ExecutionPolicy", "Bypass",
                    "-File", joiner_script_path,
                    "-Username", incoming["employee_id"],
                    "-FirstName", incoming["first_name"],
                    "-LastName", incoming["last_name"],
                    "-Department", incoming["department"],
                    "-Email", incoming["email"],
                    "-JobTitle", incoming["job_title"] or "",
                    "-TargetGroups", ",".join(add_groups),
                ]
            elif result["event_type"] == "MOVER":
                command = [
                    "pwsh",
                    "-ExecutionPolicy", "Bypass",
                    "-File", mover_script_path,
                    "-Username", incoming["employee_id"],
                    "-Department", incoming["department"],
                    "-Email", incoming["email"],
                    "-JobTitle", incoming["job_title"] or "",
                    "-AddGroups", ",".join(add_groups),
                    "-RemoveGroups", ",".join(remove_groups),
                ]
            elif result["event_type"] == "LEAVER":
                command = [
                    "pwsh",
                    "-ExecutionPolicy", "Bypass",
                    "-File", leaver_script_path,
                    "-Username", incoming["employee_id"],
                    "-RemoveGroups", ",".join(remove_groups),
                ]
            
            else:
                command = None

            if command:
                # Run the command and capture the output
                entra_result = subprocess.run(command, capture_output=True, text=True)

                print(entra_result.stdout)
                if entra_result.returncode != 0:
                    print(entra_result.stderr)
                    db.insert_audit_event(conn, hr_event_id, incoming["employee_id"], "entra_failed", {"stderr": entra_result.stderr})
                    raise RuntimeError("Entra provisioning process failed")
                db.insert_audit_event(conn, hr_event_id, incoming["employee_id"],"entra_provisioned", {"stdout": entra_result.stdout})

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
