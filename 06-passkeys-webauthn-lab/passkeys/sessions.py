import os
from base64 import urlsafe_b64encode
from dotenv import load_dotenv
from fastapi import Request, Response
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from webauthn import base64url_to_bytes

load_dotenv()

SESSION_SECRET = os.getenv("SESSION_SECRET")
if not SESSION_SECRET:
    raise RuntimeError("SESSION_SECRET is missing from .env")

serializer_tx = URLSafeTimedSerializer(SESSION_SECRET, salt="webauthn-tx")
serializer_session = URLSafeTimedSerializer(SESSION_SECRET, salt="webauthn-session")
CHALLENGE_TTL_SECONDS = 300
SESSION_TTL_SECONDS = 28800
COOKIE_NAME = "_webauthn_tx"

# Browsers reject Secure cookies over plain HTTP, so follow the RP origin
ORIGIN = os.getenv("ORIGIN", "")
COOKIE_SECURE = ORIGIN.startswith("https://")


def bytes_to_base64url(value: bytes) -> str:
    return urlsafe_b64encode(value).rstrip(b"=").decode("ascii")

def save_challenge(
    ceremony: str,
    response: Response,
    challenge: bytes,
    user_name: str,
    scenario: str = "happy",
) -> None:
    payload = {
        "ceremony": ceremony,
        "challenge": bytes_to_base64url(challenge),
        "user_name": user_name,
        "scenario": scenario,
    }
    token = serializer_tx.dumps(payload)
    response.set_cookie(
        key="_webauthn_tx",
        value=token,
        max_age=CHALLENGE_TTL_SECONDS,
        httponly=True,
        samesite="lax",
        secure=COOKIE_SECURE,
    )
    
def save_session(response: Response, user_name: str, user_id: str) -> None:
    payload = {

        "user_name": user_name,
        "user_id": user_id,
    }
    token = serializer_session.dumps(payload)
    response.set_cookie(
        key="_webauthn_session",
        value=token,
        max_age=SESSION_TTL_SECONDS,
        httponly=True,
        samesite="lax",
        secure=COOKIE_SECURE,
    )

def load_session(request: Request) -> dict | None:
    token = request.cookies.get("_webauthn_session")
    if not token:
        return None

    try:
        return serializer_session.loads(token, max_age=SESSION_TTL_SECONDS)
    except (BadSignature, SignatureExpired):
        return None


def pop_challenge(request: Request, expected_ceremony: str) -> tuple[bytes, str, str]:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise ValueError("missing cookie")

    try:
        payload = serializer_tx.loads(token, max_age=CHALLENGE_TTL_SECONDS)
    except (BadSignature, SignatureExpired) as err:
        raise ValueError("invalid or expired cookie") from err

    if payload.get("ceremony") != expected_ceremony:
        raise ValueError("wrong ceremony type")

    challenge = base64url_to_bytes(payload["challenge"])
    user_name = payload["user_name"]
    scenario = payload.get("scenario") or "happy"
    if scenario == "expired_challenge":
        raise ValueError("invalid or expired cookie")
    return challenge, user_name, scenario


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(
        key="_webauthn_session",
        httponly=True,
        samesite="lax",
        secure=COOKIE_SECURE,
    )
