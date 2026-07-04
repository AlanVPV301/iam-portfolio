#!/usr/bin/env python3
"""POST each row from an HR events CSV to POST /hr/events."""

import argparse
import csv
import json
import sys
from pathlib import Path

import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CSV = PROJECT_ROOT / "hr" / "demo-events.csv"
DEFAULT_URL = "http://127.0.0.1:8000/hr/events"


def row_to_payload(row: dict) -> dict:
    payload = {
        "event_id": row["event_id"].strip(),
        "employee_id": row["employee_id"].strip(),
        "email": row["email"].strip(),
        "first_name": row["first_name"].strip(),
        "last_name": row["last_name"].strip(),
        "department": row["department"].strip(),
        "job_title": row.get("job_title", "").strip() or None,
        "status": row["status"].strip(),
        "manager_id": row.get("manager_id", "").strip() or None,
    }
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Import HR lifecycle events from CSV")
    parser.add_argument(
        "csv_path",
        nargs="?",
        default=str(DEFAULT_CSV),
        help=f"Path to events CSV (default: {DEFAULT_CSV})",
    )
    parser.add_argument(
        "--url",
        default=DEFAULT_URL,
        help=f"Orchestrator ingest URL (default: {DEFAULT_URL})",
    )
    args = parser.parse_args()

    csv_path = Path(args.csv_path)
    if not csv_path.exists():
        print(f"CSV not found: {csv_path}", file=sys.stderr)
        return 1

    with csv_path.open(newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    if not rows:
        print("CSV has no data rows.", file=sys.stderr)
        return 1

    print(f"Importing {len(rows)} event(s) from {csv_path}\n")

    for index, row in enumerate(rows, start=1):
        payload = row_to_payload(row)
        response = requests.post(args.url, json=payload, timeout=30)

        try:
            body = response.json()
        except requests.JSONDecodeError:
            body = response.text

        print(f"[{index}/{len(rows)}] {payload['event_id']}")
        print(f"  HTTP {response.status_code}")
        print(f"  {json.dumps(body, indent=2) if isinstance(body, dict) else body}\n")

        if response.status_code >= 400:
            return 1

    print("Import complete.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
