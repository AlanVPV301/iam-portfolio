import asyncio
import json
import os
from pathlib import Path
import uuid
from datetime import datetime, timezone
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from scim import db, patch
from scim.filter import parse_filter
from scim.models import SCIMUser, ScimMeta, ScimPatchPayload


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

def row_to_scim_user(row: dict) -> SCIMUser:
    return SCIMUser(
        id=row["id"],
        userName=row["user_name"],
        externalId=row["external_id"],
        name={"givenName": row["given_name"], "familyName": row["family_name"]},
        emails=[{"value": row["user_name"], "primary": True}],
        active=bool(row["active"]),
        roles=json.loads(row["roles_json"]),
        meta=ScimMeta(
            resourceType="User",
            created=datetime.fromisoformat(row["created_at"]),
            lastModified=datetime.fromisoformat(row["updated_at"]),
            location=f"http://127.0.0.1:8000/scim/v2/Users/{row['id']}",
        ),
    )

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
    
@app.get("/scim/v2/Users/{user_id}")
def get_user(user_id: str, token: str = Depends(verify_token)):
    with db.get_connection(DATABASE_PATH) as conn:
        user = db.get_user_by_id(conn, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        return row_to_scim_user(user)

#Get users with filters in Entra format, username or external ID
@app.get("/scim/v2/Users")
def list_users(
    filter: str | None = None,
    startIndex: int = 1,
    count: int = 100,
    token: str = Depends(verify_token),
):
    with db.get_connection(DATABASE_PATH) as conn:
        if filter is None:
            # optional: return all users, or empty list
            rows = []
        else:
            attr, value = parse_filter(filter)
            if attr == "userName":
                row = db.get_user_by_user_name(conn, value)
            elif attr == "externalId":
                row = db.get_user_by_external_id(conn, value)
            else:
                raise HTTPException(400, detail=f"unsupported filter attribute: {attr}")
            rows = [row] if row else []

    #Loop through the results, format in SCIM response
    resources = [row_to_scim_user(r).model_dump(mode="json") for r in rows]
    return {
        "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
        "totalResults": len(resources),
        "startIndex": startIndex,
        "itemsPerPage": len(resources),
        "Resources": resources,
    }

@app.post("/scim/v2/Users", status_code=201)
def create_user(user: SCIMUser, token: str = Depends(verify_token)):
    with db.get_connection(DATABASE_PATH) as conn:
        existing_user = db.get_user_by_external_id(conn, user.externalId)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already exists",
            )

        user.id = str(uuid.uuid4())
        user.meta = ScimMeta(
            resourceType="User",
            created=datetime.now(timezone.utc),
            lastModified=datetime.now(timezone.utc),
            location=f"http://127.0.0.1:8000/scim/v2/Users/{user.id}",
)

        db.create_user(conn, user)   # DB stores created_at/updated_at, not meta blob


    return user.model_dump(mode="json")
 

@app.patch("/scim/v2/Users/{user_id}")
def update_user(user_id: str, patch_payload: ScimPatchPayload, token: str = Depends(verify_token)):
    with db.get_connection(DATABASE_PATH) as conn:
        row = db.get_user_by_id(conn, user_id)
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        row = patch.apply_patch_to_row(dict(row), patch_payload.Operations)
        db.update_user_row(conn, row)

    return row_to_scim_user(row).model_dump(mode="json")
