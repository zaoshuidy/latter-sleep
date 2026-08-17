from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any


EVIDENCE_ERRORS = (
    "requires two Chinese published-book references",
    "requires one Adobe source",
    "requires one print or trim source",
    "requires reviewed field mapping",
)


def evaluate_evidence(record: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if len(record.get("chinese_book_references", [])) < 2:
        errors.append(EVIDENCE_ERRORS[0])
    if not record.get("adobe_sources"):
        errors.append(EVIDENCE_ERRORS[1])
    if not record.get("print_sources"):
        errors.append(EVIDENCE_ERRORS[2])
    if not record.get("field_mapping_path"):
        errors.append(EVIDENCE_ERRORS[3])
    return errors


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def verify_original(root: Path, record: dict[str, Any]) -> Path:
    root = root.resolve()
    relative = Path(record["original"]["relative_path"])
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("original path must stay under root")

    path = (root / relative).resolve()
    if root != path and root not in path.parents:
        raise ValueError("original path must stay under root")
    if not path.is_file():
        raise ValueError(f"original file must be a regular file under root: {relative.as_posix()}")

    actual_sha256 = _sha256_file(path)
    expected_sha256 = str(record["original"]["sha256"]).upper()
    if actual_sha256 != expected_sha256:
        raise ValueError(
            f"original SHA-256 mismatch: expected {expected_sha256}, got {actual_sha256}"
        )
    return path



def can_activate(root: Path, record: dict[str, Any]) -> bool:
    verify_original(root, record)
    return record.get("status") == "approved" and not evaluate_evidence(record)
