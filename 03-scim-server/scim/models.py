#Incoming JSON data model validation and parsing

from pydantic import BaseModel, EmailStr, Field
from datetime import datetime

def default_user_schemas() -> list[str]:
    return ["urn:ietf:params:scim:schemas:core:2.0:User"]

class ScimName(BaseModel):
    givenName: str
    familyName: str

class ScimEmail(BaseModel):
    value: EmailStr
    type: str | None = None
    primary: bool | None = None

class ScimMeta(BaseModel):
    created: datetime | None = None
    lastModified: datetime | None = None
    resourceType: str | None = None
    location: str | None = None

class SCIMUser(BaseModel):
    schemas: list[str] = Field(default_factory=default_user_schemas)
    userName: str                
    externalId: str | None = None
    name: ScimName
    emails: list[ScimEmail]
    active: bool = True
    id: str | None = None            # server assigns on POST
    meta: ScimMeta | None = None
    roles: list[str] | None = None
