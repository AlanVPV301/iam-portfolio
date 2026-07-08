import re

FILTER_RE = re.compile(r'^(\w+) eq "([^"]*)"$')

SCIM_TO_DB = {
    "userName": ("user_name", "get_user_by_user_name"),
    "externalId": ("external_id", "get_user_by_external_id"),
}

def parse_filter(filter_str: str) -> tuple[str, str]:
    match = FILTER_RE.match(filter_str.strip())
    if not match:
        raise ValueError(f"unsupported filter: {filter_str}")
    return match.group(1), match.group(2)  # attr, value