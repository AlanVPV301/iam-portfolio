from pathlib import Path
from orchestrator.config import BIRTHRIGHT_RULES_PATH

import yaml


EMPTY_ENTITLEMENTS = {"entra_groups": [], "scim_roles": []}


def load_birthright_rules(path: Path | None = None) -> dict:
    rules_file = path or BIRTHRIGHT_RULES_PATH
    with open(rules_file, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data


def get_entitlements(department: str, rules: dict | None = None) -> dict:
    """Return birthright entitlements for a department."""
    rules = rules if rules is not None else load_birthright_rules()

    dept_rules = rules.get(department)
    if dept_rules is None:
        return EMPTY_ENTITLEMENTS.copy()

    return {
        "entra_groups": list(dept_rules.get("entra_groups", [])),
        "scim_roles": list(dept_rules.get("scim_roles", [])),
    }