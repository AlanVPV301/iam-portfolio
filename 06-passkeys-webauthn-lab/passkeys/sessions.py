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

serializer = URLSafeTimedSerializer(SESSION_SECRET, salt="webauthn-tx")
CHALLENGE_TTL_SECONDS = 300
COOKIE_NAME = "_webauthn_tx"


def bytes_to_base64url(value: bytes) -> str:
    return urlsafe_b64encode(value).rstrip(b"=").decode("ascii")

def save_registration_challenge(response: Response, challenge: bytes, user_name: str) -> None:
    payload = {
        "ceremony": "register",
        "challenge": bytes_to_base64url(challenge),
        "user_name": user_name,
    }
    token = serializer.dumps(payload)
    response.set_cookie(
        key="_webauthn_tx",
        value=token,
        max_age=300,
        httponly=True,
        samesite="lax",
    )
    


def pop_registration_challenge(request: Request) -> tuple[bytes, str]:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise ValueError("missing cookie")

    try:
        payload = serializer.loads(token, max_age=CHALLENGE_TTL_SECONDS)
    except (BadSignature, SignatureExpired) as err:
        raise ValueError("invalid or expired cookie") from err

    if payload.get("ceremony") != "register":
        raise ValueError("wrong ceremony type")

    challenge = base64url_to_bytes(payload["challenge"])
    user_name = payload["user_name"]
    return challenge, user_name
