#Incoming JSON data model validation and parsing

from pydantic import BaseModel, EmailStr

class HREvent(BaseModel):
    event_id: str
    employee_id: str
    email: EmailStr
    first_name: str
    last_name: str
    department: str
    job_title: str | None = None
    status: str  # "active" | "terminated"
    manager_id: str | None = None