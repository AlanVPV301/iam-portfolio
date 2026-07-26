import asyncio
import json
import os
from pathlib import Path
import uuid
from datetime import datetime, timezone
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Depends, HTTPException, status, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from webauthn import base64url_to_bytes
from webauthn.helpers.structs import AuthenticatorTransport, PublicKeyCredentialDescriptor
from webauthn.helpers.generate_user_handle import generate_user_handle
from webauthn.helpers.bytes_to_base64url import bytes_to_base64url
import logging
from pydantic import BaseModel
from passkeys.sessions import save_challenge, pop_challenge
from passkeys import db
from passkeys.webauthn_helpers import begin_registration, finish_registration, begin_authentication, finish_authentication
from passkeys.webauthn_helpers import RP_NAME, RP_ID, ORIGIN



DATABASE_PATH = os.getenv("DATABASE_PATH", db.DATABASE_PATH)
BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app = FastAPI(
    title="Passkeys LAB",
    description="WebAuthN lab",
    version="0.1.0",
)


# Configure basic formatting for your application console
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

# Force the py_webauthn logger to reveal deep structural insights
webauthn_logger = logging.getLogger("webauthn")
webauthn_logger.setLevel(logging.DEBUG)


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
            "rp_name": RP_NAME,
            "scenario": "happy",
            "rp_id": RP_ID,
            "origin": ORIGIN,
        },
    )

class OptionsBody(BaseModel):
    username: str
    display_name: str | None = None

@app.post("/webauthn/register/options")
def register_options(response: Response, body: OptionsBody):
    conn = db.get_connection(DATABASE_PATH) 
    row = db.get_user_by_username(conn, body.username)
    #Create user if not existing username, otherwise just load the user
    if row is None:
        user_id_bytes = generate_user_handle()
        db.create_user(conn, bytes_to_base64url(user_id_bytes), body.username, body.display_name)
    else:
        user_id_bytes = base64url_to_bytes(row["id"])

    options_json, challenge = begin_registration(body.username, user_id_bytes, body.display_name)
    save_challenge("register", response, challenge, user_name=body.username)
    return options_json


@app.post("/webauthn/register/verify")
def register_verify(request: Request, response: Response, credential: dict):
    challenge, user_name = pop_challenge(request, "register")
    response.delete_cookie("_webauthn_tx")

    result = finish_registration(credential, expected_challenge=challenge)
    if isinstance(result, dict):
        raise HTTPException(status_code=400, detail=result.get("msg"))

    conn = db.get_connection(DATABASE_PATH)

    row = db.get_user_by_username(conn, user_name)
    user_id = row["id"]   # already stored at options time

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

@app.post("/webauthn/login/options")
def login_options(response: Response, body: OptionsBody): 
    conn = db.get_connection(DATABASE_PATH)
    row = db.get_user_by_username(conn, body.username)
    if not row:
        raise HTTPException(404, "User not found, please register")
    user_id = row["id"]


    rows = db.get_credentials_for_user(conn, user_id)
    if not rows:
        raise HTTPException(404, "No passkeys for user")

    allow_credentials = []
    #convert the transport strings (internal, hybrid, etc) into typed enum values for the allowed credentials
    for row in rows:
        raw_transports = json.loads(row["transports"]) if row["transports"] else None
        transports = (
            [AuthenticatorTransport(t) for t in raw_transports]
            if raw_transports
            else None
        )
        allow_credentials.append(
            PublicKeyCredentialDescriptor(
                id=row["credential_id"],
                transports=transports,
            )
        )
    options_json, challenge = begin_authentication(user_id, allow_credentials)
    save_challenge("login", response, challenge, body.username)
    return options_json

@app.post("/webauthn/login/verify")
def login_verify(request: Request, response: Response, credential: dict):
    challenge, user_name = pop_challenge(request, "login")
    response.delete_cookie("_webauthn_tx")
    conn = db.get_connection(DATABASE_PATH)
    credential_id = base64url_to_bytes(credential["rawId"])
    
    row = db.get_credential_by_id(conn, credential_id)
    if not row:
        raise HTTPException(404, "Unknown passkey")

    verification = finish_authentication(
        credential,
        expected_challenge=challenge,
        public_key=row["public_key"],
        sign_count=row["sign_count"],
    )

    if isinstance(verification, dict):
        raise HTTPException(status_code=400, detail=verification.get("msg"))

    #Update the sign count based on the updated value from the VerifiedAuthentication result object
    db.update_sign_count(conn, verification.credential_id, verification.new_sign_count)


    return {"ok": True}