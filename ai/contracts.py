from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_ROOT = PROJECT_ROOT / "schemas"


def _schema_path(schema_name: str) -> Path:
    path = SCHEMA_ROOT / f"{schema_name}.schema.json"
    if not path.is_file():
        raise FileNotFoundError(f"Unknown schema: {schema_name}")
    return path


def validate_data(data: dict[str, Any], schema_name: str) -> list[str]:
    schema = json.loads(_schema_path(schema_name).read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(data), key=lambda item: list(item.absolute_path))
    return [error.message for error in errors]


def load_and_validate(path: Path, schema_name: str) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    errors = validate_data(data, schema_name)
    if errors:
        raise ValueError("\n".join(errors))
    return data
