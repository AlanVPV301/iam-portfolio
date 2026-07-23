import asyncio
import json
import os
from pathlib import Path
import uuid
from datetime import datetime, timezone
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, status, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates


from passkeys.sessions import save_registration_challenge, pop_registration_challenge
from passkeys import db
from passkeys.webauthn_helpers import begin_registration, finish_registration

load_dotenv()

DATABASE_PATH = os.getenv("DATABASE_PATH", db.DATABASE_PATH)
BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app = FastAPI(
    title="Passkeys LAB",
    description="WebAuthN lab",
    version="0.1.0",
)

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


@app.on_event("startup")
def startup() -> None:
    db.init_db(DATABASE_PATH)


# Health check endpoint, not protected, no authentication required
@app.get("/health")
def health():
    db_path = Path(DATABASE_PATH)
    return {
        "status": "ok",
        "database_path": str(db_path.resolve()),
        "database_exists": db_path.exists(),
    }


@app.get("/")
def home(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "rp_name": "FinFlow Passkeys Lab",
            "scenario": "happy",
            "rp_id": "localhost",
            "origin": "http://localhost:8002",
        },
    )

@app.post("/webauthn/register/options")
def register_options(request: Request, response: Response):
    options_json, challenge = begin_registration(user_name="alan")
    save_registration_challenge(response, challenge, user_name="alan")  # cookie or store
    return options_json


@app.post("/webauthn/register/verify")
def register_verify(request: Request, response: Response, credential: dict):
    challenge, user_name = pop_registration_challenge(request)
    response.delete_cookie("_webauthn_tx")

    result = finish_registration(credential, expected_challenge=challenge)
    if isinstance(result, dict):
        raise HTTPException(status_code=400, detail=result.get("msg"))

    conn = db.get_connection(DATABASE_PATH)

    user_id = "IDTEST1"
    db.create_user(conn, "alanvpv.test@test.com", "Alan VPV")

    transports = credential.get("response", {}).get("transports") or []

    db.save_credential(
        conn,
        result.credential_id,
        user_id,
        result.credential_public_key,
        result.sign_count,
        transports,
    )

    return {"ok": True, "credential_id_len": len(result.credential_id)}