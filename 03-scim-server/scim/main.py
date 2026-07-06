import asyncio
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from scim import db


load_dotenv()

DATABASE_PATH = os.getenv("DATABASE_PATH", db.DATABASE_PATH)

app = FastAPI(
    title="FinFlow SCIM Server",
    description="SCIM server for FinFlow",
    version="0.1.0",
)


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


# 1. Initialize the HTTPBearer security scheme
security_scheme = HTTPBearer()

# 2. Use the SCIM_BEARER_TOKEN environment variable to validate the token
API_BEARER_TOKEN = os.getenv("SCIM_BEARER_TOKEN", "")

# 3. Create a dependency function to validate the token
def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security_scheme)):
    # credentials.credentials contains the parsed string token
    if credentials.credentials != API_BEARER_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials

# 4. Apply the dependency to protect specific routes
@app.get("/scim/v2/ServiceProviderConfig")
def get_service_provider_config(token: str = Depends(verify_token)):
    return {

  "schemas": ["urn:ietf:params:scim:schemas:core:2.0:ServiceProviderConfig"],
  "patch": { "supported": True },
  "filter": { "supported": True, "maxResults": 200 },
  "bulk": { "supported": False },
  "authenticationSchemes": [{
    "type": "oauthbearertoken",
    "name": "OAuth Bearer Token",
    "primary": True
  }]
}
    