from __future__ import annotations

import json
import os
import tempfile
import unicodedata
from pathlib import Path
from typing import Any

from ai.contracts import validate_data

from .component_specs import component_spec, derived_names
from .paths import load_json, read_image_metadata, safe_relative_file, sha256_file
from .record_contracts import (
    ACTIVE_LIFECYCLES,
    canonical_sequence_diagnostics,
    publication_year_matches_evidence,
    source_binding_mismatches,
)


REQUIRED_RECORD_COUNT = 50
CATEGORY_NAMES = tuple(name for name, _ in component_spec("cover")["category_specs"])
CATEGORY_FIELDS = tuple(field for _, field in component_spec("cover")["category_specs"])
DERIVED_NAMES = derived_names("cover")


def _json_bytes(data: dict[str, Any]) -> bytes:
    return (json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _atomic_write_json(path: Path, data: dict[str, Any]) -> None:
    payload = _json_bytes(data)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as file:
            temporary = Path(file.name)
            file.write(payload)
            file.flush()
            os.fsync(file.fileno())
        temporary.replace(path)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _normalized_tags(values: list[str]) -> list[str]:
    normalized = {
        unicodedata.normalize("NFC", value).strip().casefold()
        for value in values
        if unicodedata.normalize("NFC", value).strip()
    }
    return sorted(normalized)


def _component_asset_relative(component_root: Path, declared_path: str) -> str:
    declared = Path(declared_path)
    if declared.is_absolute() or ".." in declared.parts:
        raise ValueError("Asset path must be component-relative without traversal")
    parts = declared.parts
    if parts and parts[0] == component_root.name:
        parts = parts[1:]
    if len(parts) < 2 or parts[0] != "assets":
        raise ValueError("Asset path must be inside the component assets directory")
    return Path(*parts).as_posix()


def _safe_files(root: Path) -> list[tuple[str, Path]]:
    files: list[tuple[str, Path]] = []

    def visit(directory: Path, relative_directory: Path) -> None:
        for entry in sorted(directory.iterdir(), key=lambda item: item.name):
            relative = relative_directory / entry.name
            if entry.is_symlink():
                raise ValueError(f"Linked input is not allowed: {relative.as_posix()}")
            if entry.is_dir():
                visit(entry, relative)
            elif entry.is_file():
                files.append((relative.as_posix(), safe_relative_file(root, relative.as_posix())))
            else:
                raise ValueError(f"Input must be a regular file: {relative.as_posix()}")

    visit(root, Path())
    return files


def _registry_sources(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    sources: dict[str, dict[str, Any]] = {}
    for source in registry["sources"]:
        source_id = source["source_registry_id"]
        if source_id in sources:
            raise ValueError(f"Duplicate source_registry_id: {source_id}")
        sources[source_id] = source
    return sources


def _record_error(
    record: dict[str, Any],
    record_relative: str,
    component_root: Path,
    registry_sources: dict[str, dict[str, Any]],
    component: str,
) -> str | None:
    schema_errors = validate_data(record, "book-component-reference-record")
    if schema_errors:
        return "; ".join(schema_errors)
    if record["component_type"] != component:
        return f"Component mismatch: expected {component}"
    if record_relative != f"{record['record_id']}.json":
        return f"Record filename must be {record['record_id']}.json at the records root"
    if not publication_year_matches_evidence(record):
        return "Identity publication year does not match bound publication year evidence"
    source_id = record["source"]["source_registry_id"]
    registry_source = registry_sources.get(source_id)
    if registry_source is None:
        return f"Unknown source_registry_id: {source_id}"
    mismatches = source_binding_mismatches(record["source"], registry_source)
    if mismatches:
        return f"Source registry binding mismatch: {', '.join(mismatches)}"
    try:
        asset_relative = _component_asset_relative(component_root, record["asset"]["relative_path"])
        asset_path = safe_relative_file(component_root, asset_relative)
        actual_hash = sha256_file(asset_path)
        actual_metadata = read_image_metadata(asset_path)
    except ValueError as error:
        return str(error)
    if actual_hash != record["asset"]["sha256"]:
        return "Asset SHA-256 does not match the record"
    expected_metadata = {
        "width": record["asset"]["width"],
        "height": record["asset"]["height"],
        "mime_type": record["asset"]["mime_type"],
    }
    if actual_metadata != expected_metadata:
        return "Asset metadata does not match the record"
    return None


def _category_map(records: list[dict[str, Any]], field: str) -> dict[str, list[str]]:
    groups: dict[str, list[str]] = {}
    for record in records:
        value = str(record["identity"]["publication_year"]) if field == "publication_year" else record["component_profile"][field]
        groups.setdefault(value, []).append(record["record_id"])
    return {value: groups[value] for value in sorted(groups)}


def _library_errors(
    records: list[dict[str, Any]],
    assets: list[dict[str, str]],
    component_root: Path,
    source_ids: list[str],
    record_prefix: str,
    require_contiguous_books: bool,
) -> list[dict[str, object]]:
    errors: list[dict[str, object]] = []
    fields = (
        ("duplicate_record_id", lambda record: record["record_id"]),
        ("duplicate_book_case_id", lambda record: record["identity"]["book_case_id"]),
    )
    for code, get_value in fields:
        groups: dict[str, list[str]] = {}
        for record in records:
            groups.setdefault(get_value(record), []).append(record["record_id"])
        for value in sorted(groups):
            record_ids = sorted(groups[value])
            if len(record_ids) > 1:
                errors.append({"code": code, "value": value, "record_ids": record_ids})

    record_ids_by_asset: dict[str, list[str]] = {}
    for record in records:
        asset_path = _component_asset_relative(component_root, record["asset"]["relative_path"])
        record_ids_by_asset.setdefault(asset_path, []).append(record["record_id"])

    assets_by_hash: dict[str, list[str]] = {}
    for asset in assets:
        assets_by_hash.setdefault(asset["sha256"], []).append(asset["path"])
    for asset_hash in sorted(assets_by_hash):
        paths = sorted(assets_by_hash[asset_hash])
        if len(paths) > 1:
            record_ids = sorted(
                record_id
                for path in paths
                for record_id in record_ids_by_asset.get(path, [])
            )
            errors.append(
                {
                    "code": "duplicate_asset_sha256",
                    "value": asset_hash,
                    "paths": paths,
                    "record_ids": record_ids,
                }
            )

    for path in sorted(record_ids_by_asset):
        record_ids = sorted(record_ids_by_asset[path])
        if len(record_ids) > 1:
            errors.append(
                {
                    "code": "asset_referenced_by_multiple_records",
                    "paths": [path],
                    "record_ids": record_ids,
                }
            )

    unreferenced_paths = sorted({asset["path"] for asset in assets} - set(record_ids_by_asset))
    if unreferenced_paths:
        errors.append(
            {
                "code": "unreferenced_assets",
                "paths": unreferenced_paths,
                "record_ids": [],
            }
        )
    errors.extend(
        canonical_sequence_diagnostics(
            records,
            source_ids,
            record_prefix=record_prefix,
            require_contiguous_books=require_contiguous_books,
        )
    )
    return errors


def _prepare_categories_root(component_root: Path, category_names: tuple[str, ...]) -> Path:
    categories_root = component_root / "categories"
    if categories_root.is_symlink():
        raise ValueError("Categories output directory must not be a link")
    categories_root.mkdir(exist_ok=True)
    allowed_names = {f"{name}.json" for name in category_names}
    entries = sorted(categories_root.iterdir(), key=lambda entry: entry.name)

    for entry in entries:
        if entry.is_symlink():
            continue
        if entry.is_dir():
            raise ValueError(f"categories contains unknown directory: {entry.name}")
        if not entry.is_file() or entry.suffix.lower() != ".json":
            raise ValueError(f"categories contains non-JSON file: {entry.name}")

    for entry in entries:
        if entry.is_symlink() or entry.name not in allowed_names:
            entry.unlink()
    return categories_root


def build_library(component_root: Path, registry_path: Path) -> dict[str, object]:
    """Derive deterministic component catalogues and a non-self-referential manifest."""
    component_root = Path(component_root)
    registry_path = Path(registry_path)
    component = component_root.name
    spec = component_spec(component)
    category_specs = spec["category_specs"]
    category_names = tuple(name for name, _ in category_specs)
    component_derived_names = derived_names(component)
    records_root = component_root / "records"
    assets_root = component_root / "assets"
    if not component_root.is_dir() or not records_root.is_dir() or not assets_root.is_dir():
        raise ValueError("Component root must contain records and assets directories")

    safe_registry = safe_relative_file(registry_path.parent, registry_path.name)
    registry = load_json(safe_registry)
    registry_errors = validate_data(registry, "book-component-source-registry")
    if registry_errors:
        raise ValueError("Invalid source registry: " + "; ".join(registry_errors))
    sources = _registry_sources(registry)

    record_files = _safe_files(records_root)
    asset_files = _safe_files(assets_root)
    assets_manifest = [
        {"path": f"assets/{relative}", "sha256": sha256_file(path)}
        for relative, path in asset_files
    ]
    record_inventory: list[dict[str, Any]] = []
    valid_items: list[tuple[dict[str, Any], str]] = []
    invalid_records: list[dict[str, str]] = []

    for relative, record_path in record_files:
        record_hash = sha256_file(record_path)
        if not relative.endswith(".json"):
            record_inventory.append(
                {"record_id": None, "path": f"records/{relative}", "sha256": record_hash}
            )
            invalid_records.append(
                {"path": f"records/{relative}", "reason": "Record input must be JSON"}
            )
            continue
        try:
            record = load_json(record_path)
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
            record_inventory.append({"record_id": None, "path": f"records/{relative}", "sha256": record_hash})
            invalid_records.append({"path": f"records/{relative}", "reason": str(error)})
            continue
        record_id = record.get("record_id") if isinstance(record.get("record_id"), str) else None
        record_inventory.append({"record_id": record_id, "path": f"records/{relative}", "sha256": record_hash})
        error = _record_error(record, relative, component_root, sources, component)
        if error is None:
            valid_items.append((record, record_hash))
        else:
            invalid_records.append({"path": f"records/{relative}", "reason": error})

    valid_items.sort(key=lambda item: item[0]["record_id"])
    records = [item[0] for item in valid_items]
    active_items = [
        item for item in valid_items if item[0]["lifecycle"]["status"] in ACTIVE_LIFECYCLES
    ]
    active_records = [item[0] for item in active_items]
    record_inventory.sort(key=lambda item: ((item["record_id"] or ""), item["path"]))
    valid_count = len(active_records)
    library_errors = _library_errors(
        records,
        assets_manifest,
        component_root,
        sorted(sources),
        spec["record_prefix"],
        spec["require_contiguous_books"],
    )
    status = (
        "available"
        if valid_count >= REQUIRED_RECORD_COUNT and not invalid_records and not library_errors
        else "building"
    )

    categories = [
        {
            "schema_version": "1.0",
            "component": component,
            "category": category_name,
            "entries": _category_map(active_records, field),
        }
        for category_name, field in category_specs
    ]

    catalog_entries = []
    retrieval_entries = []
    for record, record_hash in active_items:
        record_id = record["record_id"]
        catalog_entries.append(
            {
                "record_id": record_id,
                "book_case_id": record["identity"]["book_case_id"],
                "source_registry_id": record["source"]["source_registry_id"],
                "asset_path": record["asset"]["relative_path"],
                "asset_sha256": record["asset"]["sha256"],
                "component": record["component_type"],
                "publication_year": record["identity"]["publication_year"],
                "lifecycle": record["lifecycle"]["status"],
                "record_sha256": record_hash,
            }
        )
        retrieval_entry = {
                "record_id": record_id,
                "book_case_id": record["identity"]["book_case_id"],
                "source_registry_id": record["source"]["source_registry_id"],
                "component": record["component_type"],
                "publication_year": record["identity"]["publication_year"],
                "lifecycle": record["lifecycle"]["status"],
                "style_tags": _normalized_tags(record["retrieval_features"]["style_tags"]),
                "content_tags": _normalized_tags(record["retrieval_features"]["content_tags"]),
                "color_tags": _normalized_tags(record["retrieval_features"]["color_tags"]),
                "mood_tags": _normalized_tags(record["retrieval_features"]["mood_tags"]),
            }
        retrieval_entry.update(
            {field: record["component_profile"][field] for field in spec["retrieval_fields"]}
        )
        retrieval_entries.append(retrieval_entry)

    catalog = {
        "schema_version": "1.0",
        "component": component,
        "status": status,
        "required_count": REQUIRED_RECORD_COUNT,
        "valid_record_count": valid_count,
        "invalid_record_count": len(invalid_records),
        "error_count": len(library_errors),
        "entries": catalog_entries,
    }
    retrieval_index = {
        "schema_version": "1.0",
        "component": component,
        "entries": retrieval_entries,
    }

    _prepare_categories_root(component_root, category_names)
    for name, data in (
        *((f"categories/{name}.json", category) for name, category in zip(category_names, categories, strict=True)),
        ("catalog.json", catalog),
        ("retrieval-index.json", retrieval_index),
    ):
        _atomic_write_json(component_root / name, data)

    legacy_categories = component_root / "categories.json"
    if legacy_categories.is_file() or legacy_categories.is_symlink():
        legacy_categories.unlink()

    derived_manifest = [
        {"path": name, "sha256": sha256_file(component_root / name)}
        for name in component_derived_names
    ]
    manifest = {
        "schema_version": "1.0",
        "component": component,
        "status": status,
        "required_count": REQUIRED_RECORD_COUNT,
        "valid_record_count": valid_count,
        "invalid_record_count": len(invalid_records),
        "errors": library_errors,
        "registry": {"path": registry_path.name, "sha256": sha256_file(safe_registry)},
        "records": record_inventory,
        "assets": assets_manifest,
        "derived": derived_manifest,
    }
    _atomic_write_json(component_root / "manifest.json", manifest)

    return {
        "status": status,
        "valid_record_count": valid_count,
        "invalid_record_count": len(invalid_records),
        "required_count": REQUIRED_RECORD_COUNT,
        "invalid_records": invalid_records,
        "errors": library_errors,
        "outputs": {
            name: sha256_file(component_root / name)
            for name in (*component_derived_names, "manifest.json")
        },
    }
