from orchestrator.rules import EMPTY_ENTITLEMENTS, get_entitlements

EventType = str  # "JOINER" | "MOVER" | "LEAVER" | "NOOP"

# Fields that trigger a MOVER when they change
MOVER_FIELDS = ("department", "job_title", "email")


def row_to_dict(row) -> dict | None:
    if row is None:
        return None
    return dict(row)


def detect_event_type(existing: dict | None, incoming: dict) -> EventType:
    incoming_status = incoming["status"].lower()
    existing_status = existing["status"].lower()


    #If no existing row, it's a JOINER if the status is not terminated, otherwise a LEAVER if the status is CHANGING to terminated
    if existing is None:
        return "LEAVER" if incoming_status == "terminated" else "JOINER"
    if existing_status != "terminated" and incoming_status == "terminated":
        return "LEAVER"

    #If the status is not terminated, check if any of the MOVER_FIELDS have changed
    for field in MOVER_FIELDS:
        old = (existing.get(field) or "").lower() if field == "email" or field == "status" else existing.get(field)
        new = (incoming.get(field) or "").lower() if field == "email" else incoming.get(field)
        if old != new:
            return "MOVER"

    return "NOOP"

#Helper function to compute the difference between old and new lists
def _list_diff(old: list[str], new: list[str]) -> tuple[list[str], list[str]]:
    old_set, new_set = set(old), set(new)
    return sorted(new_set - old_set), sorted(old_set - new_set)


def compute_plan(
    event_type: EventType,
    existing: dict | None,
    incoming: dict,
) -> dict:
    #Checks for existing department and new department, gets entitlements for each, if LEAVER, no entitlements are needed
    old_dept = existing["department"] if existing else None
    new_dept = incoming["department"]

    old_ent = get_entitlements(old_dept) if old_dept else EMPTY_ENTITLEMENTS
    new_ent = get_entitlements(new_dept) if event_type != "LEAVER" else EMPTY_ENTITLEMENTS

    if event_type == "JOINER":
        add_groups, remove_groups = new_ent["entra_groups"], []
        add_roles, remove_roles = new_ent["scim_roles"], []
    elif event_type == "LEAVER":
        add_groups, remove_groups = [], old_ent["entra_groups"]
        add_roles, remove_roles = [], old_ent["scim_roles"]
    elif event_type == "MOVER":
        add_groups, remove_groups = _list_diff(old_ent["entra_groups"], new_ent["entra_groups"])
        add_roles, remove_roles = _list_diff(old_ent["scim_roles"], new_ent["scim_roles"])
    else:  # NOOP
        add_groups = remove_groups = add_roles = remove_roles = []

    return {
        "event_type": event_type,
        "add": {"entra_groups": add_groups, "scim_roles": add_roles},
        "remove": {"entra_groups": remove_groups, "scim_roles": remove_roles},
    }


def process_hr_event(existing: dict | None, incoming: dict) -> dict:
    event_type = detect_event_type(existing, incoming)
    plan = compute_plan(event_type, existing, incoming)
    return {"event_type": event_type, "plan": plan}