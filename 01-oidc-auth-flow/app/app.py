import base64
import hashlib
import os
import secrets
import json
import requests
from urllib.parse import urlencode

from dotenv import load_dotenv
from flask import Flask, redirect, render_template, request, session

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ["FLASK_SECRET_KEY"]

TENANT_ID    = os.environ["ENTRA_TENANT_ID"]
CLIENT_ID    = os.environ["ENTRA_CLIENT_ID"]
REDIRECT_URI = os.environ["REDIRECT_URI"]

AUTHORIZATION_ENDPOINT = (
    f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/authorize"
)


def generate_pkce_pair():
    code_verifier = secrets.token_urlsafe(96)

    digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
    code_challenge = (
        base64.urlsafe_b64encode(digest)
        .rstrip(b"=")
        .decode("ascii")
    )

    return code_verifier, code_challenge


@app.route("/")
def home():
    return render_template("home.html")


@app.route("/login")
def login():
    code_verifier, code_challenge = generate_pkce_pair()
    state = secrets.token_urlsafe(32)

    session["pkce_verifier"] = code_verifier
    session["oauth_state"]   = state

    params = {
        "client_id":             CLIENT_ID,
        "response_type":         "code",
        "redirect_uri":          REDIRECT_URI,
        "scope":                 "openid profile email offline_access",
        "state":                 state,
        "code_challenge":        code_challenge,
        "code_challenge_method": "S256",
        "response_mode":         "query",
    }

    return redirect(f"{AUTHORIZATION_ENDPOINT}?{urlencode(params)}")


@app.route("/callback")
def callback():
    # ── Step 1: CSRF check ────────────────────────────────────────────────────
    if request.args.get("state") != session.get("oauth_state"):
        return "State mismatch — possible CSRF attack.", 400

    # ── Step 2: Check for errors from Entra ID ────────────────────────────────
    if "error" in request.args:
        return f"Auth error: {request.args['error']} — {request.args.get('error_description')}", 400

    code = request.args["code"]
    code_verifier = session["pkce_verifier"]

    # ── Step 3: Exchange code for tokens ─────────────────────────────────────
    token_url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"

    response = requests.post(token_url, data={
        "grant_type":    "authorization_code",
        "code":          code,
        "redirect_uri":  REDIRECT_URI,
        "client_id":     CLIENT_ID,
        "client_secret": os.environ["ENTRA_CLIENT_SECRET"],
        "code_verifier": code_verifier,
    })

    tokens = response.json()

    if "error" in tokens:
        return f"Token error: {tokens['error']} — {tokens.get('error_description')}", 400

    # ── Step 4: Decode the id_token payload ───────────────────────────────────
    # A JWT is three base64url segments: header.payload.signature
    # We decode the payload to read claims.
    # NOTE: we are NOT validating the signature here — that comes in Stage 3.
    id_token = tokens["id_token"]
    payload_segment = id_token.split(".")[1]

    # base64url may be missing padding — add it back before decoding
    padding = 4 - len(payload_segment) % 4
    payload_segment += "=" * (padding % 4)
    claims = json.loads(base64.b64decode(payload_segment))

    # Store tokens in session for Stage 3
    session["access_token"]  = tokens["access_token"]
    session["id_token"]      = id_token
    session["refresh_token"] = tokens.get("refresh_token")

    return render_template("claims.html", claims=claims)


if __name__ == "__main__":
    app.run(debug=True, port=5000)