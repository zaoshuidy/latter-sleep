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


def _is_junction(path: Path) -> bool:
    is_junction = getattr(path, "is_junction", None)
    if callable(is_junction):
        return bool(is_junction())
    return False


def _path_uses_links(path: Path) -> bool:
    try:
        path.lstat()
    except FileNotFoundError:
        return False
    return path.is_symlink() or _is_junction(path)


def _reject_links(path: Path) -> None:
    if _path_uses_links(path):
        raise ValueError("original path must not include symlink or junction links")


def verify_original(root: Path, record: dict[str, Any]) -> Path:
    relative = Path(record["original"]["relative_path"])
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("original path must stay under root")

    lexical_root = Path(root)
    _reject_links(lexical_root)

    lexical_path = lexical_root
    for part in relative.parts:
        lexical_path = lexical_path / part
        _reject_links(lexical_path)

    root = lexical_root.resolve()
    path = (lexical_root / relative).resolve()
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
