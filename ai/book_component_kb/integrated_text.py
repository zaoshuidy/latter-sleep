from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Any

from ai.contracts import validate_data


INTEGRATED_MODE = "integrated-typography"
EDITABLE_MODE = "editable-overlay"

_SURFACE_ROLES = {
    "front": frozenset({"title", "subtitle", "author", "short-note"}),
    "back": frozenset({"back-cover-copy", "recommendation", "short-note"}),
    "spine": frozenset({"title", "author", "short-note"}),
}
_MACHINE_LABEL = re.compile(
    r"(?:\bisbn\b|条\s*码|\bbarcode\b|二\s*维\s*码|\bqr\s*code\b|"
    r"\bcip\b|书\s*号|发\s*行\s*编\s*号|机\s*器\s*码)",
    re.IGNORECASE,
)
_PRICE_LABEL = re.compile(
    r"(?:定\s*价|售\s*价|价\s*格|人\s*民\s*币|[￥¥]\s*\d|"
    r"\b(?:rmb|cny)\s*\d)",
    re.IGNORECASE,
)
_DIGIT_RUN = re.compile(r"(?<!\d)(?:\d[\s-]*){9,12}\d(?!\d)")


def _normalize(value: str) -> str:
    return unicodedata.normalize("NFKC", value).strip().casefold()


def contains_machine_identifier(value: str) -> bool:
    """Return true for publishing identifiers that must never be model pixels."""
    if not isinstance(value, str):
        return False
    normalized = _normalize(value)
    return bool(
        _MACHINE_LABEL.search(normalized)
        or _PRICE_LABEL.search(normalized)
        or _DIGIT_RUN.search(normalized)
    )


@dataclass(frozen=True)
class IntegratedTextEntry:
    text_id: str
    surface: str
    role: str
    value: str
    language: str

    def as_dict(self) -> dict[str, str]:
        return {
            "text_id": self.text_id,
            "surface": self.surface,
            "role": self.role,
            "value": self.value,
            "language": self.language,
        }


@dataclass(frozen=True)
class IntegratedTypographyPlan:
    mode: str
    entries: tuple[IntegratedTextEntry, ...]
    backup: tuple[tuple[str, str], ...]

    def entries_as_dicts(self) -> list[dict[str, str]]:
        return [entry.as_dict() for entry in self.entries]

    def backup_dict(self) -> dict[str, str]:
        return dict(self.backup)


def _registered_entry(project: dict[str, Any], entry: IntegratedTextEntry) -> bool:
    if entry.role in {"title", "subtitle", "author"}:
        return project.get(entry.role) == entry.value
    return any(
        all(candidate.get(field) == getattr(entry, field) for field in (
            "text_id",
            "surface",
            "role",
            "value",
            "language",
        ))
        for candidate in project.get("cover_text_registry", [])
    )


def validate_integrated_typography(
    project: dict[str, Any],
    component_type: str,
    output_spec: dict[str, Any],
) -> IntegratedTypographyPlan | None:
    """Validate the smallest stable cover-text contract and freeze its values."""
    mode = output_spec.get("text_rendering_mode", EDITABLE_MODE)
    if mode == EDITABLE_MODE:
        return None
    if mode != INTEGRATED_MODE:
        raise ValueError("unknown text rendering mode")
    if component_type != "cover":
        raise ValueError("integrated typography is available only for cover")

    raw_entries = output_spec.get("integrated_text")
    backup = output_spec.get("editable_text_backup")
    if not isinstance(raw_entries, list) or not raw_entries:
        raise ValueError("integrated text must be a non-empty list")
    if not isinstance(backup, dict) or not backup:
        raise ValueError("editable backup must be a non-empty mapping")

    entries: list[IntegratedTextEntry] = []
    seen_ids: set[str] = set()
    for raw in raw_entries:
        errors = validate_data(raw, "book-component-integrated-text-entry")
        if errors:
            raise ValueError("integrated text entry is invalid: " + "; ".join(errors))
        entry = IntegratedTextEntry(**raw)
        normalized_id = _normalize(entry.text_id)
        if normalized_id in seen_ids:
            raise ValueError("integrated text IDs must be unique")
        seen_ids.add(normalized_id)
        if entry.role not in _SURFACE_ROLES[entry.surface]:
            raise ValueError("integrated text surface and role do not match")
        if contains_machine_identifier(entry.value):
            raise ValueError("machine identifier is forbidden in generated cover text")
        if not _registered_entry(project, entry):
            raise ValueError("integrated text must match registered project text")
        entries.append(entry)

    expected_backup = {entry.text_id: entry.value for entry in entries}
    if backup != expected_backup:
        raise ValueError("editable backup must exactly match integrated text")
    if any(contains_machine_identifier(value) for value in backup.values()):
        raise ValueError("machine identifier is forbidden in editable backup")

    return IntegratedTypographyPlan(
        mode=INTEGRATED_MODE,
        entries=tuple(entries),
        backup=tuple(expected_backup.items()),
    )


__all__ = [
    "EDITABLE_MODE",
    "INTEGRATED_MODE",
    "IntegratedTextEntry",
    "IntegratedTypographyPlan",
    "contains_machine_identifier",
    "validate_integrated_typography",
]
