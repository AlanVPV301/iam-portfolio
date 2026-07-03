from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATABASE_PATH = PROJECT_ROOT / "data" / "orchestrator.db"
BIRTHRIGHT_RULES_PATH = PROJECT_ROOT / "rules" / "birthright.yaml"