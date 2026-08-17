from __future__ import annotations

import hashlib
import json
import os
import unicodedata
from pathlib import Path
from typing import Any

from ai.contracts import validate_data

from .paths import _open_regular_file, safe_relative_file
from .record_contracts import ACTIVE_LIFECYCLES
from .validate import validate_library


COVER_WEIGHTS = {
    "visual_strategy": 0.20,
    "composition": 0.20,
    "title_zone": 0.15,
    "color": 0.15,
    "material": 0.10,
    "mood": 0.10,
    "cover_scope": 0.05,
    "book_category": 0.05,
}
CHAPTER_OPENER_WEIGHTS = {
    "opening_mode": 0.15,
    "visual_strategy": 0.15,
    "chapter_number_zone": 0.15,
    "chapter_title_zone": 0.20,
    "image_role": 0.15,
    "text_image_relationship": 0.10,
    "whitespace": 0.10,
}
COMPONENT_WEIGHTS = {
    "cover": COVER_WEIGHTS,
    "chapter-opener": CHAPTER_OPENER_WEIGHTS,
}

_OBSERVATION_ASPECTS = {
    "material": {"material", "材质", "材料", "纸张材质"},
    "book_category": {"book_category", "book category", "图书类别", "书籍类别", "品类"},
}
_MANIFEST_KEYS = {
    "schema_version",
    "component",
    "status",
    "required_count",
    "valid_record_count",
    "invalid_record_count",
    "errors",
    "registry",
    "records",
    "assets",
    "derived",
}


def _normalize(value: str) -> str:
    return unicodedata.normalize("NFKC", value).strip().lower()


def _normalized_values(values: list[str]) -> set[str]:
    return {normalized for value in values if (normalized := _normalize(value))}


def _observation_values(record: dict[str, Any], field: str) -> set[str]:
    aliases = {_normalize(value) for value in _OBSERVATION_ASPECTS[field]}
    values: set[str] = set()
    for observation in record["visual_decomposition"]["observations"]:
        if _normalize(observation["aspect"]) not in aliases:
            continue
        if observation["visibility"] == "uncertain":
            continue
        values.update(_normalized_values([observation["value"]]))
        values.update(_normalized_values(observation["content_tags"]))
    return values


def _field_value_sets(record: dict[str, Any], weights: dict[str, float]) -> dict[str, set[str]]:
    profile = record["component_profile"]
    features = record["retrieval_features"]
    values = {
        "visual_strategy": _normalized_values([profile["visual_strategy"]]),
        "color": _normalized_values(features["color_tags"]),
        "mood": _normalized_values(features["mood_tags"]),
    }
    for field in weights:
        if field in profile:
            values[field] = _normalized_values([profile[field]])
        elif field in _OBSERVATION_ASPECTS:
            values[field] = _observation_values(record, field)
    return values


def _query_value_sets(query: dict[str, Any], weights: dict[str, float]) -> dict[str, set[str]]:
    targets = query["field_targets"]
    return {
        field: _normalized_values(targets.get(field, []))
        for field in weights
    }


def _score_candidate(
    entry: dict[str, Any],
    record: dict[str, Any],
    query_values: dict[str, set[str]],
    weights: dict[str, float] = COVER_WEIGHTS,
) -> dict[str, Any]:
    candidate_values = _field_value_sets(record, weights)
    field_scores: dict[str, float] = {}
    explanation_parts: list[str] = []
    observation_fields = {"material", "book_category"}
    for field, weight in weights.items():
        matches = sorted(candidate_values[field] & query_values[field])
        score = weight if matches else 0.0
        field_scores[field] = score
        if matches:
            reason = f"matched [{', '.join(matches)}]"
        elif not candidate_values[field] and field in observation_fields:
            reason = "no certain indexed observation"
        elif not candidate_values[field]:
            reason = "missing indexed value"
        else:
            reason = "no normalized match"
        explanation_parts.append(f"{field}={score:.2f}/{weight:.2f} {reason}")

    total_score = round(sum(field_scores.values()), 10)
    explanation_parts.append(f"total={total_score:.2f}")
    return {
        "record_id": entry["record_id"],
        "book_case_id": entry["book_case_id"],
        "field_scores": field_scores,
        "total_score": total_score,
        "match_explanation": "; ".join(explanation_parts),
    }


def _select_diverse_candidates(
    candidates: list[dict[str, Any]],
    limit: int,
) -> list[dict[str, Any]]:
    ordered = sorted(
        candidates,
        key=lambda item: (-item["total_score"], item["record_id"]),
    )
    selected: list[dict[str, Any]] = []
    seen_books: set[str] = set()
    for candidate in ordered:
        book_case_id = candidate["book_case_id"]
        if book_case_id in seen_books:
            continue
        seen_books.add(book_case_id)
        selected.append(candidate)
        if len(selected) == limit:
            break
    return selected


def _limit_label(limit: int) -> str:
    return "five" if limit == 5 else str(limit)


def _reject_nonstandard_json_constant(constant: str) -> None:
    raise ValueError(f"nonstandard JSON constant: {constant}")


def _read_json_snapshot(path: Path) -> tuple[dict[str, Any], bytes, str]:
    """Parse and hash the exact raw bytes read once from one safely opened FD."""
    file_fd = _open_regular_file(path)
    with os.fdopen(file_fd, "rb") as file:
        raw = file.read()
    digest = hashlib.sha256(raw).hexdigest()
    try:
        data = json.loads(
            raw.decode("utf-8"),
            parse_constant=_reject_nonstandard_json_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        raise ValueError(f"invalid JSON snapshot: {error}") from error
    if not isinstance(data, dict):
        raise ValueError("JSON snapshot must be an object")
    return data, raw, digest


def _manifest_bindings(
    manifest: dict[str, Any],
    component: str,
) -> tuple[list[dict[str, str]], str]:
    if set(manifest) != _MANIFEST_KEYS:
        raise ValueError("manifest snapshot has an unexpected key shape")
    if (
        manifest["schema_version"] != "1.0"
        or manifest["component"] != component
        or manifest["status"] != "available"
        or manifest["required_count"] != 50
        or not isinstance(manifest["valid_record_count"], int)
        or isinstance(manifest["valid_record_count"], bool)
        or manifest["valid_record_count"] < 50
        or manifest["invalid_record_count"] != 0
        or manifest["errors"] != []
    ):
        raise ValueError(f"manifest snapshot is not an available {component} library")

    records = manifest["records"]
    derived = manifest["derived"]
    if not isinstance(records, list) or not isinstance(derived, list):
        raise ValueError("manifest snapshot inventories must be arrays")
    record_bindings: list[dict[str, str]] = []
    seen_record_ids: set[str] = set()
    for item in records:
        if not isinstance(item, dict) or set(item) != {"record_id", "path", "sha256"}:
            raise ValueError("manifest snapshot record binding is malformed")
        if not all(isinstance(item[field], str) for field in ("record_id", "path", "sha256")):
            raise ValueError("manifest snapshot record binding is malformed")
        if item["record_id"] in seen_record_ids:
            raise ValueError("manifest snapshot has duplicate record bindings")
        seen_record_ids.add(item["record_id"])
        record_bindings.append(item)

    index_hashes = [
        item.get("sha256")
        for item in derived
        if isinstance(item, dict) and item.get("path") == "retrieval-index.json"
    ]
    if len(index_hashes) != 1 or not isinstance(index_hashes[0], str):
        raise ValueError("manifest snapshot retrieval-index binding is malformed")
    return record_bindings, index_hashes[0]


def retrieve(
    component_root: Path,
    registry_path: Path,
    query: dict[str, Any],
    limit: int = 5,
) -> dict[str, Any]:
    """Retrieve a deterministic, explainable set of different component books."""
    query_errors = validate_data(query, "book-component-retrieval-query")
    if query_errors:
        raise ValueError(f"query schema validation failed: {'; '.join(query_errors)}")
    component = query["component_type"]
    if component not in COMPONENT_WEIGHTS:
        if Path(component_root).name == "cover":
            raise ValueError("cover retrieval only accepts component_type=cover")
        raise ValueError(f"retrieval does not support component_type={component}")
    if Path(component_root).name != component:
        raise ValueError(
            f"component root mismatch: expected {component}, got {Path(component_root).name}"
        )
    weights = COMPONENT_WEIGHTS[component]
    if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= 5:
        raise ValueError("limit must be an integer from 1 through 5")
    if limit > query["selection_policy"]["max_results"]:
        raise ValueError("limit cannot exceed query selection_policy.max_results")

    component_root = Path(component_root)
    registry_path = Path(registry_path)
    library_report = validate_library(component_root, registry_path)
    if not library_report["valid"]:
        detail = library_report["errors"][0] if library_report["errors"] else "unknown integrity error"
        raise ValueError(f"component library is invalid: {detail}")
    if library_report["status"] != "available":
        book_count = library_report["counts"]["books"]
        if book_count < limit:
            raise ValueError(
                f"component library cannot provide {_limit_label(limit)} different books: "
                f"found {book_count}, need {limit}; status=building"
            )
        raise ValueError(
            f"component library must be available before retrieval; "
            f"status={library_report['status']}"
        )

    manifest_path = safe_relative_file(component_root, "manifest.json")
    try:
        manifest, manifest_raw, manifest_hash = _read_json_snapshot(manifest_path)
        record_bindings, expected_index_hash = _manifest_bindings(manifest, component)
    except ValueError as error:
        raise ValueError(f"manifest snapshot is invalid: {error}") from error

    retrieval_index, _, index_hash = _read_json_snapshot(
        safe_relative_file(component_root, "retrieval-index.json")
    )
    if index_hash != expected_index_hash:
        raise ValueError("retrieval-index hash mismatch after library validation")
    if retrieval_index.get("component") != component:
        raise ValueError("component library is invalid: cross-component derivative")

    records_by_id: dict[str, dict[str, Any]] = {}
    for item in record_bindings:
        record, _, record_hash = _read_json_snapshot(
            safe_relative_file(component_root, item["path"])
        )
        if record_hash != item["sha256"]:
            raise ValueError(
                f"record hash mismatch after library validation: {item['record_id']}"
            )
        if record.get("record_id") != item["record_id"]:
            raise ValueError("component library is invalid: manifest record ID mismatch")
        records_by_id[record["record_id"]] = record

    query_values = _query_value_sets(query, weights)
    scored: list[dict[str, Any]] = []
    for entry in retrieval_index["entries"]:
        if entry.get("component") != component:
            raise ValueError("component library is invalid: cross-component retrieval entry")
        if entry.get("lifecycle") not in ACTIVE_LIFECYCLES:
            raise ValueError("component library is invalid: archived retrieval entry")
        record = records_by_id.get(entry["record_id"])
        if record is None or record.get("component_type") != component:
            raise ValueError("component library is invalid: retrieval entry record mismatch")
        if record.get("lifecycle", {}).get("status") not in ACTIVE_LIFECYCLES:
            raise ValueError("component library is invalid: archived record is indexed")
        scored.append(_score_candidate(entry, record, query_values, weights))

    candidates = _select_diverse_candidates(scored, limit)
    if len(candidates) != limit:
        raise ValueError(
            f"component library cannot provide {_limit_label(limit)} different books: "
            f"found {len(candidates)}, need {limit}"
        )
    try:
        _, final_manifest_raw, final_manifest_hash = _read_json_snapshot(manifest_path)
    except ValueError as error:
        raise ValueError("manifest changed during retrieval") from error
    if final_manifest_raw != manifest_raw or final_manifest_hash != manifest_hash:
        raise ValueError("manifest changed during retrieval")
    result = {
        "schema_version": "1.0",
        "query_id": query["query_id"],
        "component_type": component,
        "status": "available",
        "candidates": candidates,
    }
    result_errors = validate_data(result, "book-component-retrieval-result")
    if result_errors:
        raise ValueError(f"retrieval result schema validation failed: {'; '.join(result_errors)}")
    return result


__all__ = ["CHAPTER_OPENER_WEIGHTS", "COVER_WEIGHTS", "COMPONENT_WEIGHTS", "retrieve"]
