import os

import requests
from dotenv import load_dotenv


load_dotenv()

SCIM_BASE_URL = os.getenv("SCIM_BASE_URL", "http://127.0.0.1:8001").rstrip("/")
SCIM_BEARER_TOKEN = os.getenv("SCIM_BEARER_TOKEN", "")

def _headers() -> dict:
    return {"Authorization": f"Bearer {SCIM_BEARER_TOKEN}"}

def hr_to_scim_user(incoming: dict, roles: list[str]) -> dict:
    active = incoming["status"].lower() != "terminated"
    return {
        "userName": incoming["email"],
        "externalId": incoming["employee_id"],
        "name": {
            "givenName": incoming["first_name"],
            "familyName": incoming["last_name"],
        },
        "emails": [{"value": incoming["email"], "primary": True}],
        "active": active,
        "roles": roles,
    }

def create_user(payload: dict) -> dict:
    url = f"{SCIM_BASE_URL}/scim/v2/Users"
    response = requests.post(url, json=payload, headers=_headers(), timeout=30)
    response.raise_for_status()   # 201 expected
    return response.json()        # SCIM User with "id"

#Get user utilizing Entra-style filter
def find_user_by_external_id(employee_id: str) -> dict | None:
    url = f"{SCIM_BASE_URL}/scim/v2/Users"
    params = {"filter": f'externalId eq "{employee_id}"'}
    response = requests.get(url, params=params, headers=_headers(), timeout=30)
    response.raise_for_status()
    body = response.json()
    resources = body.get("Resources", [])
    return resources[0] if resources else None

def patch_user(scim_id: str, operations: list[dict]) -> dict:
    url = f"{SCIM_BASE_URL}/scim/v2/Users/{scim_id}"
    payload = {
        "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"],
        "Operations": operations,
    }
    response = requests.patch(url, json=payload, headers=_headers(), timeout=30)
    response.raise_for_status()
    return response.json()

def provision_scim(event_type: str, incoming: dict, plan: dict) -> dict:
    if event_type == "NOOP":
        return {"skipped": True, "reason": "noop"}

    add_roles = plan["add"]["scim_roles"]
    remove_roles = plan["remove"]["scim_roles"]

    if event_type == "JOINER":
        payload = hr_to_scim_user(incoming, add_roles)
        user = create_user(payload)
        return {"action": "created", "scim_id": user["id"]}

    # MOVER or LEAVER — need existing SCIM user
    existing = find_user_by_external_id(incoming["employee_id"])
    if not existing:
        # Skip - Do not accept request for non existing users
        return {"skipped": True, "reason": "scim_user_not_found"}

    scim_id = existing["id"]

    if event_type == "LEAVER":
        ops = [
            {"op": "replace", "path": "active", "value": False},
            {"op": "replace", "path": "roles", "value": []},
        ]
    else:  # MOVER
        # final roles = new dept roles (from plan add side, or recompute)
        existing_roles = existing.get("roles") or []
        final_roles = sorted(set(add_roles) | (set(existing_roles) - set(remove_roles)))
        ops = [
            {"op": "replace", "path": "roles", "value": final_roles},
            {"op": "replace", "path": "name.familyName", "value": incoming["last_name"]},
            {"op": "replace", "path": "name.givenName", "value": incoming["first_name"]},
            {"op": "replace", "path": "userName", "value": incoming["email"]},
        ]

    user = patch_user(scim_id, ops)
    return {"action": "updated", "scim_id": user["id"]}