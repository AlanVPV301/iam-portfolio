import base64
import hashlib
import json
import os
import secrets
import time
from functools import wraps
from urllib.parse import urlencode

import requests
from dotenv import load_dotenv
from flask import Flask, redirect, render_template, request, session

load_dotenv()

# Flask app setup, mostly generated via Cursor/Claude and reviewed by me
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

    # Store tokens in session for Stage 3. Tracking oid as the "logged in" signal, and name/email so the profile page can display them without re-decoding the token on every request.
    session["refresh_token"] = tokens.get("refresh_token")
    session["expires_at"]    = time.time() + tokens["expires_in"]
    session["oid"]           = claims["oid"]
    session["name"]          = claims.get("name")
    session["email"]         = claims.get("email")

    return render_template("claims.html", claims=claims)

# ── Token refresh ─────────────────────────────────────────────────────────────

def refresh_access_token():
    token_url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"

    response = requests.post(token_url, data={
        "grant_type":    "refresh_token",
        "refresh_token": session["refresh_token"],
        "client_id":     CLIENT_ID,
        "client_secret": os.environ["ENTRA_CLIENT_SECRET"],
        "scope":         "openid profile email offline_access",
    })

    tokens = response.json()

    if "error" in tokens:
        return False

    session["expires_at"]   = time.time() + tokens["expires_in"]
    if tokens.get("refresh_token"):
        session["refresh_token"] = tokens["refresh_token"]

    return True


# ── login_required decorator ──────────────────────────────────────────────────
# This decorator is used to protect routes that require authentication.
# It checks if the user is logged in and if the access token is expired.
# If the access token is expired, it refreshes the access token, as long as the refresh token is valid.
# If the access token is not expired, the user is allowed to access the protected route. 
# If the refresh token is invalid, the user is logged out and redirected to the login page.

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "oid" not in session:
            return redirect("/login")

        if time.time() > session.get("expires_at", 0):
            if not refresh_access_token():
                session.clear()
                return redirect("/login")

        return f(*args, **kwargs)
    return decorated


# ── Protected route ───────────────────────────────────────────────────────────

@app.route("/profile")
@login_required
def profile():
    return render_template("profile.html",
        name=session["name"],
        email=session["email"],
        oid=session["oid"],
        expires_at=time.strftime(
            "%Y-%m-%d %H:%M:%S UTC",
            time.gmtime(session["expires_at"])
        )
    )


# ── Logout ────────────────────────────────────────────────────────────────────

@app.route("/logout")
def logout():
    session.clear()
    logout_url = (
        f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/logout"
        f"?post_logout_redirect_uri=http://localhost:5000/"
    )
    return redirect(logout_url)

if __name__ == "__main__":
    app.run(debug=True, port=5000)