from __future__ import annotations

from typing import Any, Iterable


ACTIVE_LIFECYCLES = frozenset({"accumulation", "confirmed"})
SOURCE_BINDING_FIELDS = (
    "source_url",
    "platform",
    "collected_at",
    "publication_year",
    "publication_year_source_url",
)


def source_binding_mismatches(
    record_source: dict[str, Any],
    registry_source: dict[str, Any],
) -> list[str]:
    return [
        field
        for field in SOURCE_BINDING_FIELDS
        if record_source.get(field) != registry_source.get(field)
    ]


def publication_year_matches_evidence(record: dict[str, Any]) -> bool:
    return record["identity"]["publication_year"] == record["source"]["publication_year"]


def contiguous_id_diagnostic(
    values: Iterable[str],
    *,
    prefix: str,
    code: str,
) -> dict[str, object] | None:
    ids = sorted(set(values))
    if not ids:
        return None
    numbers = sorted(int(value.removeprefix(prefix)) for value in ids)
    expected = list(range(1, numbers[-1] + 1))
    if numbers == expected:
        return None
    missing = [f"{prefix}{number:04d}" for number in expected if number not in numbers]
    return {
        "code": code,
        "ids": ids,
        "missing": missing,
    }


def canonical_sequence_diagnostics(
    records: list[dict[str, Any]],
    source_ids: Iterable[str],
    *,
    record_prefix: str = "COV-CN-",
    require_contiguous_books: bool = True,
) -> list[dict[str, object]]:
    diagnostics = []
    sequences = [
        (source_ids, "SRC-CN-", "non_contiguous_source_ids"),
        (
            (record["record_id"] for record in records),
            record_prefix,
            "non_contiguous_record_ids",
        ),
    ]
    if require_contiguous_books:
        sequences.append((
            (record["identity"]["book_case_id"] for record in records),
            "BOOK-CN-",
            "non_contiguous_book_case_ids",
        ))
    for values, prefix, code in sequences:
        diagnostic = contiguous_id_diagnostic(values, prefix=prefix, code=code)
        if diagnostic is not None:
            diagnostics.append(diagnostic)
    return diagnostics


__all__ = [
    "ACTIVE_LIFECYCLES",
    "SOURCE_BINDING_FIELDS",
    "canonical_sequence_diagnostics",
    "contiguous_id_diagnostic",
    "publication_year_matches_evidence",
    "source_binding_mismatches",
]
