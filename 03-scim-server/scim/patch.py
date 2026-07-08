import json
from scim.models import ScimPatchOperation
from fastapi import HTTPException

#Handles SCIM PATCH operation logic, loops through all the operations and updates the affected rows only
def apply_patch_to_row(row: dict, operations: list[ScimPatchOperation]) -> dict:
    for op in operations:
        if op.op != "replace":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Operation not supported!",
            )
        if op.path == "active":
            row["active"] = 1 if op.value else 0
        elif op.path == "name.familyName":
            row["family_name"] = op.value
        elif op.path == "name.givenName":
            row["given_name"] = op.value
        elif op.path == "userName":
            row["user_name"] = op.value
        elif op.path == "externalId":
            row["external_id"] = op.value
        elif op.path == "roles":
            row["roles_json"] = json.dumps(op.value)
        
    return row