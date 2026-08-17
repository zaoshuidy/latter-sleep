from __future__ import annotations

import json
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


BUILDER_REQUIRED_COUNT = 50
CATEGORY_SPECS = component_spec("cover")["category_specs"]
DERIVED_NAMES = derived_names("cover")
PHASES = (
    "schema",
    "safe paths",
    "decoded image facts",
    "source registry binding",
    "uniqueness and closure",
    "year and component",
    "derived agreement",
    "manifest hashes",
    "count and status",
)


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
        raise ValueError("asset path must be component-relative without traversal")
    parts = declared.parts
    if parts and parts[0] == component_root.name:
        parts = parts[1:]
    if len(parts) < 2 or parts[0] != "assets":
        raise ValueError("asset path must be inside the component assets directory")
    return Path(*parts).as_posix()


def _safe_files(root: Path, errors: list[str], label: str) -> list[tuple[str, Path]]:
    files: list[tuple[str, Path]] = []
    if root.is_symlink() or not root.is_dir():
        errors.append(f"{label} directory must be an existing directory without links")
        return files

    def visit(directory: Path, relative_directory: Path) -> None:
        try:
            entries = sorted(directory.iterdir(), key=lambda item: item.name)
        except OSError as error:
            errors.append(f"cannot inspect {label} directory {relative_directory.as_posix()}: {error}")
            return
        for entry in entries:
            relative = relative_directory / entry.name
            if entry.is_symlink():
                errors.append(f"linked {label} input is not allowed: {relative.as_posix()}")
                continue
            if entry.is_dir():
                visit(entry, relative)
                continue
            if not entry.is_file():
                errors.append(f"{label} input must be a regular file: {relative.as_posix()}")
                continue
            try:
                files.append((relative.as_posix(), safe_relative_file(root, relative.as_posix())))
            except ValueError as error:
                errors.append(f"unsafe {label} path {relative.as_posix()}: {error}")

    visit(root, Path())
    return files


def _read_json(path: Path, errors: list[str], label: str) -> dict[str, Any] | None:
    try:
        return load_json(path)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError, OSError) as error:
        errors.append(f"invalid {label} JSON: {error}")
        return None


def _category_map(records: list[dict[str, Any]], field: str) -> dict[str, list[str]]:
    groups: dict[str, list[str]] = {}
    for record in records:
        if field == "publication_year":
            value = str(record["identity"]["publication_year"])
        else:
            value = record["component_profile"][field]
        groups.setdefault(value, []).append(record["record_id"])
    return {value: groups[value] for value in sorted(groups)}


def _library_diagnostics(
    records: list[dict[str, Any]],
    assets: list[dict[str, str]],
    component_root: Path,
) -> list[dict[str, object]]:
    diagnostics: list[dict[str, object]] = []
    for code, get_value in (
        ("duplicate_record_id", lambda record: record["record_id"]),
        ("duplicate_book_case_id", lambda record: record["identity"]["book_case_id"]),
    ):
        groups: dict[str, list[str]] = {}
        for record in records:
            groups.setdefault(get_value(record), []).append(record["record_id"])
        for value in sorted(groups):
            record_ids = sorted(groups[value])
            if len(record_ids) > 1:
                diagnostics.append({"code": code, "value": value, "record_ids": record_ids})

    record_ids_by_asset: dict[str, list[str]] = {}
    for record in records:
        try:
            asset_path = _component_asset_relative(component_root, record["asset"]["relative_path"])
        except (KeyError, TypeError, ValueError):
            continue
        record_ids_by_asset.setdefault(asset_path, []).append(record["record_id"])

    assets_by_hash: dict[str, list[str]] = {}
    for asset in assets:
        assets_by_hash.setdefault(asset["sha256"], []).append(asset["path"])
    for asset_hash in sorted(assets_by_hash):
        paths = sorted(assets_by_hash[asset_hash])
        if len(paths) > 1:
            diagnostics.append(
                {
                    "code": "duplicate_asset_sha256",
                    "value": asset_hash,
                    "paths": paths,
                    "record_ids": sorted(
                        record_id
                        for path in paths
                        for record_id in record_ids_by_asset.get(path, [])
                    ),
                }
            )

    for path in sorted(record_ids_by_asset):
        record_ids = sorted(record_ids_by_asset[path])
        if len(record_ids) > 1:
            diagnostics.append(
                {
                    "code": "asset_referenced_by_multiple_records",
                    "paths": [path],
                    "record_ids": record_ids,
                }
            )

    unreferenced = sorted({asset["path"] for asset in assets} - set(record_ids_by_asset))
    if unreferenced:
        diagnostics.append(
            {"code": "unreferenced_assets", "paths": unreferenced, "record_ids": []}
        )
    return diagnostics


def _duplicate_values(
    records: list[dict[str, Any]],
    getter: Any,
) -> list[str]:
    counts: dict[str, int] = {}
    for record in records:
        value = getter(record)
        counts[value] = counts.get(value, 0) + 1
    return sorted(value for value, count in counts.items() if count > 1)


def validate_library(
    component_root: Path,
    registry_path: Path,
    required_count: int = 50,
) -> dict[str, object]:
    """Validate a prebuilt component library without writing or repairing it."""
    component_root = Path(component_root)
    registry_path = Path(registry_path)
    phase_errors = {phase: [] for phase in PHASES}
    warnings: list[str] = []
    component = component_root.name
    try:
        spec = component_spec(component)
    except ValueError as error:
        phase_errors["year and component"].append(str(error))
        spec = component_spec("cover")
    category_specs = spec["category_specs"]
    component_derived_names = derived_names(component) if component in ("cover", "chapter-opener") else DERIVED_NAMES

    if not isinstance(required_count, int) or isinstance(required_count, bool) or required_count < 1:
        phase_errors["count and status"].append("required_count must be a positive integer")

    registry: dict[str, Any] | None = None
    try:
        safe_registry = safe_relative_file(registry_path.parent, registry_path.name)
    except ValueError as error:
        phase_errors["safe paths"].append(f"unsafe registry path: {error}")
        safe_registry = None
    if safe_registry is not None:
        registry = _read_json(safe_registry, phase_errors["schema"], "source registry")
    registry_schema_valid = False
    if registry is not None:
        registry_schema_messages = validate_data(registry, "book-component-source-registry")
        for message in registry_schema_messages:
            phase_errors["schema"].append(f"source registry schema: {message}")
        registry_schema_valid = not registry_schema_messages

    records_root = component_root / "records"
    assets_root = component_root / "assets"
    record_files = _safe_files(records_root, phase_errors["safe paths"], "records")
    asset_files = _safe_files(assets_root, phase_errors["safe paths"], "assets")
    parsed_records: list[dict[str, Any]] = []
    record_inventory: list[dict[str, Any]] = []
    schema_valid_records: list[dict[str, Any]] = []
    record_hashes: dict[int, str] = {}
    record_paths: dict[int, str] = {}
    for relative, record_path in record_files:
        try:
            record_hash = sha256_file(record_path)
        except ValueError as error:
            phase_errors["safe paths"].append(f"cannot hash record records/{relative}: {error}")
            continue
        if not relative.endswith(".json"):
            record_inventory.append(
                {"record_id": None, "path": f"records/{relative}", "sha256": record_hash}
            )
            phase_errors["schema"].append(f"record input must be JSON: records/{relative}")
            continue
        record = _read_json(record_path, phase_errors["schema"], f"record records/{relative}")
        record_id = record.get("record_id") if isinstance(record, dict) and isinstance(record.get("record_id"), str) else None
        record_inventory.append(
            {"record_id": record_id, "path": f"records/{relative}", "sha256": record_hash}
        )
        if record is None:
            continue
        parsed_records.append(record)
        record_hashes[id(record)] = record_hash
        record_paths[id(record)] = f"records/{relative}"
        schema_messages = validate_data(record, "book-component-reference-record")
        for message in schema_messages:
            phase_errors["schema"].append(f"record records/{relative} schema: {message}")
        if not schema_messages:
            schema_valid_records.append(record)

    record_inventory.sort(key=lambda item: ((item["record_id"] or ""), item["path"]))

    sources: dict[str, dict[str, Any]] = {}
    if registry is not None and isinstance(registry.get("sources"), list):
        for source in registry["sources"]:
            if not isinstance(source, dict) or not isinstance(source.get("source_registry_id"), str):
                continue
            source_id = source["source_registry_id"]
            if source_id in sources:
                phase_errors["source registry binding"].append(
                    f"duplicate source_registry_id: {source_id}"
                )
            else:
                sources[source_id] = source

    assets_manifest: list[dict[str, str]] = []
    actual_asset_paths: dict[str, Path] = {}
    for relative, asset_path in asset_files:
        full_relative = f"assets/{relative}"
        try:
            asset_hash = sha256_file(asset_path)
        except ValueError as error:
            phase_errors["safe paths"].append(f"cannot hash asset {full_relative}: {error}")
            continue
        assets_manifest.append({"path": full_relative, "sha256": asset_hash})
        actual_asset_paths[full_relative] = asset_path
    assets_manifest.sort(key=lambda item: item["path"])

    builder_records: list[dict[str, Any]] = []
    declared_asset_paths: dict[str, list[str]] = {}
    for record in schema_valid_records:
        record_id = record["record_id"]
        builder_eligible = True
        inventory_path = record_paths[id(record)]
        if inventory_path != f"records/{record_id}.json":
            phase_errors["uniqueness and closure"].append(
                f"record filename mismatch for {record_id}: {inventory_path}"
            )
            builder_eligible = False
        if record["component_type"] != component:
            builder_eligible = False
        year = record["identity"]["publication_year"]
        if not 2017 <= year <= 2026:
            builder_eligible = False
        if not publication_year_matches_evidence(record):
            phase_errors["source registry binding"].append(
                f"publication year evidence mismatch for {record_id}: "
                f"identity={year}, evidence={record['source']['publication_year']}"
            )
            builder_eligible = False

        source_id = record["source"]["source_registry_id"]
        source = sources.get(source_id)
        if source is None:
            phase_errors["source registry binding"].append(
                f"unknown source_registry_id for {record_id}: {source_id}"
            )
            builder_eligible = False
        else:
            mismatched = source_binding_mismatches(record["source"], source)
            if mismatched:
                phase_errors["source registry binding"].append(
                    f"source registry binding mismatch for {record_id}: {', '.join(mismatched)}"
                )
                builder_eligible = False

        try:
            asset_relative = _component_asset_relative(
                component_root, record["asset"]["relative_path"]
            )
        except ValueError as error:
            phase_errors["safe paths"].append(f"unsafe asset declaration for {record_id}: {error}")
            builder_eligible = False
            continue
        declared_asset_paths.setdefault(asset_relative, []).append(record_id)
        asset_path = actual_asset_paths.get(asset_relative)
        if asset_path is None:
            builder_eligible = False
            continue
        actual_hash = next(
            item["sha256"] for item in assets_manifest if item["path"] == asset_relative
        )
        if actual_hash != record["asset"]["sha256"]:
            phase_errors["decoded image facts"].append(
                f"asset hash mismatch for {record_id}: {asset_relative}"
            )
            builder_eligible = False
        try:
            actual_metadata = read_image_metadata(asset_path)
        except ValueError as error:
            phase_errors["decoded image facts"].append(
                f"asset {asset_relative} is not a decodable image: {error}"
            )
            builder_eligible = False
        else:
            expected_metadata = {
                "width": record["asset"]["width"],
                "height": record["asset"]["height"],
                "mime_type": record["asset"]["mime_type"],
            }
            if actual_metadata != expected_metadata:
                phase_errors["decoded image facts"].append(
                    f"decoded image metadata mismatch for {record_id}: {asset_relative}"
                )
                builder_eligible = False
        if builder_eligible:
            builder_records.append(record)

    for value in _duplicate_values(schema_valid_records, lambda item: item["record_id"]):
        phase_errors["uniqueness and closure"].append(f"duplicate record_id: {value}")
    for value in _duplicate_values(
        schema_valid_records, lambda item: item["identity"]["book_case_id"]
    ):
        phase_errors["uniqueness and closure"].append(f"duplicate book_case_id: {value}")

    assets_by_hash: dict[str, list[str]] = {}
    for item in assets_manifest:
        assets_by_hash.setdefault(item["sha256"], []).append(item["path"])
    for asset_hash in sorted(assets_by_hash):
        paths = sorted(assets_by_hash[asset_hash])
        if len(paths) > 1:
            phase_errors["uniqueness and closure"].append(
                f"duplicate asset sha256 {asset_hash}: {', '.join(paths)}"
            )
    for path in sorted(declared_asset_paths):
        record_ids = sorted(declared_asset_paths[path])
        if len(record_ids) > 1:
            phase_errors["uniqueness and closure"].append(
                f"asset referenced by multiple records {path}: {', '.join(record_ids)}"
            )
    actual_paths = set(actual_asset_paths)
    declared_paths = set(declared_asset_paths)
    for path in sorted(declared_paths - actual_paths):
        phase_errors["uniqueness and closure"].append(f"missing asset: {path}")
    for path in sorted(actual_paths - declared_paths):
        phase_errors["uniqueness and closure"].append(f"extra asset: {path}")

    for record in parsed_records:
        record_id = record.get("record_id", "<unknown>")
        identity = record.get("identity")
        if isinstance(identity, dict):
            year = identity.get("publication_year")
            if not isinstance(year, int) or isinstance(year, bool) or not 2017 <= year <= 2026:
                phase_errors["year and component"].append(
                    f"publication year out of range for {record_id}: {year}"
                )
        component = record.get("component_type")
        if component != component_root.name:
            phase_errors["year and component"].append(
                f"component mismatch for {record_id}: expected {component_root.name}, got {component}"
            )

    builder_records.sort(key=lambda item: item["record_id"])
    active_records = [
        record
        for record in builder_records
        if record["lifecycle"]["status"] in ACTIVE_LIFECYCLES
    ]
    invalid_record_count = len(record_inventory) - len(builder_records)
    library_diagnostics = _library_diagnostics(builder_records, assets_manifest, component_root)
    if registry_schema_valid:
        sequence_diagnostics = canonical_sequence_diagnostics(
            builder_records,
            sorted(sources),
            record_prefix=spec["record_prefix"],
            require_contiguous_books=spec["require_contiguous_books"],
        )
        library_diagnostics.extend(sequence_diagnostics)
        for diagnostic in sequence_diagnostics:
            phase_errors["uniqueness and closure"].append(
                f"{diagnostic['code']}: missing {', '.join(diagnostic['missing'])}"
            )
    persisted_status = (
        "available"
        if len(active_records) >= BUILDER_REQUIRED_COUNT
        and invalid_record_count == 0
        and not library_diagnostics
        else "building"
    )

    expected_categories = {
        f"categories/{name}.json": {
            "schema_version": "1.0",
            "component": component_root.name,
            "category": name,
            "entries": _category_map(active_records, field),
        }
        for name, field in category_specs
    }
    catalog_entries = []
    retrieval_entries = []
    for record in active_records:
        record_hash = record_hashes[id(record)]
        catalog_entries.append(
            {
                "record_id": record["record_id"],
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
                "record_id": record["record_id"],
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
    expected_catalog = {
        "schema_version": "1.0",
        "component": component_root.name,
        "status": persisted_status,
        "required_count": BUILDER_REQUIRED_COUNT,
        "valid_record_count": len(active_records),
        "invalid_record_count": invalid_record_count,
        "error_count": len(library_diagnostics),
        "entries": catalog_entries,
    }
    expected_retrieval = {
        "schema_version": "1.0",
        "component": component_root.name,
        "entries": retrieval_entries,
    }
    expected_derived = {
        **expected_categories,
        "catalog.json": expected_catalog,
        "retrieval-index.json": expected_retrieval,
    }

    loaded_derived: dict[str, dict[str, Any]] = {}
    categories_root = component_root / "categories"
    if categories_root.is_symlink() or not categories_root.is_dir():
        phase_errors["safe paths"].append(
            "categories directory must be an existing directory without links"
        )
    else:
        expected_category_names = {f"{name}.json" for name, _ in category_specs}
        try:
            actual_category_names = {entry.name for entry in categories_root.iterdir()}
        except OSError as error:
            actual_category_names = set()
            phase_errors["safe paths"].append(f"cannot inspect categories directory: {error}")
        for name in sorted(actual_category_names - expected_category_names):
            phase_errors["derived agreement"].append(f"unexpected category entry: {name}")

    for relative in component_derived_names:
        try:
            derived_path = safe_relative_file(component_root, relative)
        except ValueError as error:
            phase_errors["safe paths"].append(f"missing derived file {relative}: {error}")
            continue
        data = _read_json(derived_path, phase_errors["derived agreement"], relative)
        if data is None:
            continue
        loaded_derived[relative] = data
        if data != expected_derived[relative]:
            phase_errors["derived agreement"].append(
                f"derived agreement mismatch: {relative}"
            )

    manifest: dict[str, Any] | None = None
    try:
        manifest_path = safe_relative_file(component_root, "manifest.json")
    except ValueError as error:
        phase_errors["safe paths"].append(f"missing derived file manifest.json: {error}")
    else:
        manifest = _read_json(manifest_path, phase_errors["manifest hashes"], "manifest.json")

    expected_registry = None
    if safe_registry is not None:
        try:
            expected_registry = {
                "path": registry_path.name,
                "sha256": sha256_file(safe_registry),
            }
        except ValueError as error:
            phase_errors["safe paths"].append(f"cannot hash source registry: {error}")
    actual_derived_hashes = []
    for relative in component_derived_names:
        try:
            actual_derived_hashes.append(
                {"path": relative, "sha256": sha256_file(safe_relative_file(component_root, relative))}
            )
        except ValueError:
            pass

    if manifest is not None:
        if manifest.get("schema_version") != "1.0":
            phase_errors["manifest hashes"].append("manifest schema_version mismatch")
        if manifest.get("component") != component_root.name:
            phase_errors["manifest hashes"].append("manifest component mismatch")
        if manifest.get("registry") != expected_registry:
            phase_errors["manifest hashes"].append("manifest registry mismatch")
        if manifest.get("records") != record_inventory:
            phase_errors["manifest hashes"].append("manifest records mismatch or record hash mismatch")
        if manifest.get("assets") != assets_manifest:
            phase_errors["manifest hashes"].append("manifest assets mismatch or asset hash mismatch")
        if manifest.get("derived") != actual_derived_hashes:
            phase_errors["manifest hashes"].append("manifest derived hash mismatch")
        expected_manifest_keys = {
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
        if set(manifest) != expected_manifest_keys:
            phase_errors["manifest hashes"].append("manifest structure mismatch")
        if manifest.get("errors") != library_diagnostics:
            phase_errors["manifest hashes"].append("manifest diagnostics mismatch")

        for section in ("records", "assets", "derived"):
            items = manifest.get(section)
            if not isinstance(items, list):
                continue
            for item in items:
                if not isinstance(item, dict) or not isinstance(item.get("path"), str):
                    continue
                try:
                    safe_relative_file(component_root, item["path"])
                except ValueError as error:
                    phase_errors["safe paths"].append(
                        f"unsafe manifest {section} path {item['path']}: {error}"
                    )

    if expected_catalog["valid_record_count"] != len(catalog_entries):
        phase_errors["count and status"].append("count mismatch: expected catalog entries")
    catalog = loaded_derived.get("catalog.json")
    if catalog is not None:
        if catalog.get("valid_record_count") != len(active_records):
            phase_errors["count and status"].append("count mismatch: catalog valid_record_count")
        if catalog.get("invalid_record_count") != invalid_record_count:
            phase_errors["count and status"].append("count mismatch: catalog invalid_record_count")
        if catalog.get("required_count") != BUILDER_REQUIRED_COUNT:
            phase_errors["count and status"].append("count mismatch: catalog required_count")
        if catalog.get("status") != persisted_status:
            phase_errors["count and status"].append("status mismatch: catalog")
    if manifest is not None:
        if manifest.get("valid_record_count") != len(active_records):
            phase_errors["count and status"].append("count mismatch: manifest valid_record_count")
        if manifest.get("invalid_record_count") != invalid_record_count:
            phase_errors["count and status"].append("count mismatch: manifest invalid_record_count")
        if manifest.get("required_count") != BUILDER_REQUIRED_COUNT:
            phase_errors["count and status"].append("count mismatch: manifest required_count")
        if manifest.get("status") != persisted_status:
            phase_errors["count and status"].append("status mismatch: manifest")

    errors = [
        f"{phase}: {message}"
        for phase in PHASES
        for message in phase_errors[phase]
    ]
    record_count = len(active_records)
    valid = not errors
    if valid and record_count >= required_count:
        status = "available"
    elif valid:
        status = "building"
        warnings.append(
            f"record count {record_count} is below required count {required_count}"
        )
    else:
        status = "invalid"

    return {
        "valid": valid,
        "status": status,
        "record_count": record_count,
        "errors": errors,
        "warnings": warnings,
        "counts": {
            "records": len(record_files),
            "assets": len(asset_files),
            "books": len(
                {
                    record["identity"]["book_case_id"]
                    for record in active_records
                }
            ),
            "categories": sum(
                1 for relative in loaded_derived if relative.startswith("categories/")
            ),
            "derived": len(loaded_derived),
        },
    }
