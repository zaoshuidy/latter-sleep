from __future__ import annotations

import copy
import hashlib
import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from ai.book_component_kb.build import build_library
from ai.book_component_kb.paths import sha256_file
from ai.book_component_kb.validate import validate_library


FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "component-kb"
CATEGORY_NAMES = (
    "by-visual-strategy",
    "by-composition",
    "by-title-zone",
    "by-publication-year",
)
CATEGORY_PATHS = tuple(f"categories/{name}.json" for name in CATEGORY_NAMES)
MANIFEST_DERIVED_NAMES = (
    *CATEGORY_PATHS,
    "catalog.json",
    "retrieval-index.json",
)
DERIVED_NAMES = (
    *MANIFEST_DERIVED_NAMES,
    "manifest.json",
)


def load_fixture(name: str) -> dict[str, object]:
    return json.loads((FIXTURE_ROOT / name).read_text(encoding="utf-8"))


def json_file(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def file_hashes(paths: list[Path]) -> dict[str, str]:
    return {path.as_posix(): sha256_file(path) for path in paths}


class ComponentKnowledgeBaseBuildTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.library_root = Path(self.temp_dir.name) / "library"
        self.cover_root = self.library_root / "cover"
        self.records_root = self.cover_root / "records"
        self.assets_root = self.cover_root / "assets"
        self.records_root.mkdir(parents=True)
        self.assets_root.mkdir()
        self.registry = self.library_root / "source-registry.json"
        self.registry.write_text(
            json.dumps(load_fixture("source-registry.json"), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    def _make_png_bytes(self, seed: str) -> bytes:
        digest = hashlib.sha256(seed.encode("utf-8")).digest()
        pixels = (digest * 21)[: 12 * 18 * 3]
        output = io.BytesIO()
        Image.frombytes("RGB", (12, 18), pixels).save(output, format="PNG")
        return output.getvalue()

    def _add_record(
        self,
        record_id: str,
        *,
        filename: str | None = None,
        asset_name: str | None = None,
        asset_bytes: bytes | None = None,
        asset_seed: str | None = None,
        book_case_id: str | None = None,
        year: int = 2024,
        visual_strategy: str = "illustration",
        composition: str = "whitespace",
        title_zone: str = "top",
        evidence_marker: str = "NEVER_INDEX_EVIDENCE",
        lifecycle: str = "accumulation",
    ) -> tuple[Path, Path]:
        asset_name = asset_name or f"{record_id}.png"
        asset_bytes = asset_bytes or self._make_png_bytes(asset_seed or asset_name)
        asset_path = self.assets_root / asset_name
        asset_path.write_bytes(asset_bytes)
        record = copy.deepcopy(load_fixture("cover-record.json"))
        record["record_id"] = record_id
        record["identity"]["book_case_id"] = book_case_id or f"BOOK-CN-{record_id.rsplit('-', 1)[-1]}"
        record["identity"]["publication_year"] = year
        registry = json_file(self.registry)
        source = next(item for item in registry["sources"] if item["publication_year"] == year)
        record["source"] = {
            field: source[field]
            for field in (
                "source_registry_id",
                "source_url",
                "platform",
                "collected_at",
                "publication_year",
                "publication_year_source_url",
            )
        }
        record["asset"] = {
            "relative_path": f"cover/assets/{asset_name}",
            "sha256": hashlib.sha256(asset_bytes).hexdigest(),
            "mime_type": "image/png",
            "width": 12,
            "height": 18,
        }
        record["component_profile"]["visual_strategy"] = visual_strategy
        record["component_profile"]["composition"] = composition
        record["component_profile"]["title_zone"] = title_zone
        record["visual_decomposition"]["overall_strategy"] = evidence_marker
        record["visual_decomposition"]["observations"][0]["evidence"] = evidence_marker
        record["reference_transfer"]["transferable"] = [evidence_marker]
        record["lifecycle"]["status"] = lifecycle
        record_path = self.records_root / (filename or f"{record_id}.json")
        record_path.write_text(
            json.dumps(record, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return record_path, asset_path

    def _add_unique_records(self, count: int = 50) -> None:
        for index in range(count, 0, -1):
            self._add_record(f"COV-CN-{index:04d}")

    def test_builder_derives_closed_files_without_editing_inputs(self) -> None:
        record, asset = self._add_record("COV-CN-0001")
        before = file_hashes([record, asset, self.registry])

        result = build_library(self.cover_root, self.registry)

        self.assertEqual(before, file_hashes([record, asset, self.registry]))
        self.assertEqual(
            {
                "status": "building",
                "valid_record_count": 1,
                "invalid_record_count": 0,
                "required_count": 50,
                "errors": [],
            },
            {
                key: result[key]
                for key in ("status", "valid_record_count", "invalid_record_count", "required_count", "errors")
            },
        )
        for name in DERIVED_NAMES:
            self.assertTrue((self.cover_root / name).is_file(), name)
        self.assertEqual([], list(self.cover_root.rglob("*.tmp")))

    def test_outputs_are_sorted_closed_and_exclude_free_form_evidence(self) -> None:
        self._add_record(
            "COV-CN-0002",
            year=2023,
            visual_strategy="photography",
            composition="centered",
            title_zone="bottom",
        )
        first_record, _ = self._add_record(
            "COV-CN-0001",
            evidence_marker="SECRET_FREE_FORM_REPORT_TEXT",
        )

        (self.cover_root / "categories.json").write_text('{"legacy": true}\n', encoding="utf-8")
        build_library(self.cover_root, self.registry)

        self.assertFalse((self.cover_root / "categories.json").exists())
        self.assertEqual(
            sorted(f"{name}.json" for name in CATEGORY_NAMES),
            sorted(path.name for path in (self.cover_root / "categories").iterdir()),
        )
        visual_strategy = json_file(self.cover_root / "categories" / "by-visual-strategy.json")
        publication_year = json_file(self.cover_root / "categories" / "by-publication-year.json")
        self.assertEqual(
            {
                "illustration": ["COV-CN-0001"],
                "photography": ["COV-CN-0002"],
            },
            visual_strategy["entries"],
        )
        self.assertEqual(
            {"2023": ["COV-CN-0002"], "2024": ["COV-CN-0001"]},
            publication_year["entries"],
        )
        for category_name in CATEGORY_NAMES:
            category = json_file(self.cover_root / "categories" / f"{category_name}.json")
            self.assertEqual(category_name, category["category"])
            self.assertEqual(["category", "component", "entries", "schema_version"], sorted(category))

        catalog = json_file(self.cover_root / "catalog.json")
        self.assertEqual(["COV-CN-0001", "COV-CN-0002"], [item["record_id"] for item in catalog["entries"]])
        self.assertEqual(
            {
                "record_id",
                "book_case_id",
                "source_registry_id",
                "asset_path",
                "asset_sha256",
                "component",
                "publication_year",
                "lifecycle",
                "record_sha256",
            },
            set(catalog["entries"][0]),
        )
        self.assertEqual(sha256_file(first_record), catalog["entries"][0]["record_sha256"])

        retrieval = json_file(self.cover_root / "retrieval-index.json")
        retrieval_text = json.dumps(retrieval, ensure_ascii=False)
        self.assertNotIn("SECRET_FREE_FORM_REPORT_TEXT", retrieval_text)
        self.assertEqual(
            {
                "record_id",
                "book_case_id",
                "source_registry_id",
                "component",
                "publication_year",
                "lifecycle",
                "visual_strategy",
                "composition",
                "title_zone",
                "style_tags",
                "content_tags",
                "color_tags",
                "mood_tags",
            },
            set(retrieval["entries"][0]),
        )

    def test_manifest_binds_registry_every_record_asset_and_non_manifest_derivative(self) -> None:
        record_two, asset_two = self._add_record("COV-CN-0002")
        record_one, asset_one = self._add_record("COV-CN-0001")

        build_library(self.cover_root, self.registry)

        manifest = json_file(self.cover_root / "manifest.json")
        self.assertEqual(
            {"path": "source-registry.json", "sha256": sha256_file(self.registry)},
            manifest["registry"],
        )
        self.assertEqual(
            [
                {"record_id": "COV-CN-0001", "path": "records/COV-CN-0001.json", "sha256": sha256_file(record_one)},
                {"record_id": "COV-CN-0002", "path": "records/COV-CN-0002.json", "sha256": sha256_file(record_two)},
            ],
            manifest["records"],
        )
        self.assertEqual(
            [
                {"path": "assets/COV-CN-0001.png", "sha256": sha256_file(asset_one)},
                {"path": "assets/COV-CN-0002.png", "sha256": sha256_file(asset_two)},
            ],
            manifest["assets"],
        )
        self.assertEqual(
            list(MANIFEST_DERIVED_NAMES),
            [item["path"] for item in manifest["derived"]],
        )
        self.assertNotIn("manifest.json", [item["path"] for item in manifest["derived"]])
        for item in manifest["derived"]:
            self.assertEqual(sha256_file(self.cover_root / item["path"]), item["sha256"])

    def test_second_build_is_byte_identical(self) -> None:
        self._add_record("COV-CN-0002")
        self._add_record("COV-CN-0001")
        build_library(self.cover_root, self.registry)
        first = file_hashes([self.cover_root / name for name in DERIVED_NAMES])

        build_library(self.cover_root, self.registry)

        self.assertEqual(first, file_hashes([self.cover_root / name for name in DERIVED_NAMES]))

    def test_status_becomes_available_at_fifty_valid_records(self) -> None:
        self._add_unique_records()

        result = build_library(self.cover_root, self.registry)

        self.assertEqual("available", result["status"])
        self.assertEqual(50, result["valid_record_count"])
        self.assertEqual([], result["errors"])
        catalog = json_file(self.cover_root / "catalog.json")
        self.assertEqual(50, len({item["book_case_id"] for item in catalog["entries"]}))
        self.assertEqual(50, len({item["asset_sha256"] for item in catalog["entries"]}))
        self.assertEqual("available", json_file(self.cover_root / "catalog.json")["status"])

    def test_archived_record_is_manifest_bound_but_excluded_from_active_outputs(self) -> None:
        self._add_unique_records(count=49)
        archived_record, archived_asset = self._add_record(
            "COV-CN-0050",
            lifecycle="archived",
        )

        result = build_library(self.cover_root, self.registry)

        self.assertEqual("building", result["status"])
        self.assertEqual(49, result["valid_record_count"])
        catalog = json_file(self.cover_root / "catalog.json")
        retrieval = json_file(self.cover_root / "retrieval-index.json")
        self.assertNotIn("COV-CN-0050", [item["record_id"] for item in catalog["entries"]])
        self.assertNotIn("COV-CN-0050", [item["record_id"] for item in retrieval["entries"]])
        manifest = json_file(self.cover_root / "manifest.json")
        self.assertIn(
            {
                "record_id": "COV-CN-0050",
                "path": "records/COV-CN-0050.json",
                "sha256": sha256_file(archived_record),
            },
            manifest["records"],
        )
        self.assertIn(
            {"path": "assets/COV-CN-0050.png", "sha256": sha256_file(archived_asset)},
            manifest["assets"],
        )

    def _assert_source_binding_conflict(self, field: str, value: str) -> None:
        self._add_unique_records()
        record_path = self.records_root / "COV-CN-0001.json"
        record = json_file(record_path)
        record["source"][field] = value
        record_path.write_text(
            json.dumps(record, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

        result = build_library(self.cover_root, self.registry)

        self.assertEqual("building", result["status"])
        self.assertEqual(49, result["valid_record_count"])
        self.assertEqual(1, result["invalid_record_count"])
        self.assertIn(
            field.replace("_", " "),
            result["invalid_records"][0]["reason"].replace("_", " "),
        )

    def test_builder_rejects_source_url_binding_conflict(self) -> None:
        self._assert_source_binding_conflict("source_url", "https://example.com/different")

    def test_builder_rejects_platform_binding_conflict(self) -> None:
        self._assert_source_binding_conflict("platform", "不同平台")

    def test_builder_rejects_collected_at_binding_conflict(self) -> None:
        self._assert_source_binding_conflict("collected_at", "2026-08-11")

    def test_builder_rejects_publication_year_binding_conflict(self) -> None:
        self._assert_source_binding_conflict("publication_year", 2023)

    def test_builder_rejects_publication_year_source_url_binding_conflict(self) -> None:
        self._assert_source_binding_conflict(
            "publication_year_source_url",
            "https://example.com/different-bibliography",
        )

    def test_builder_rejects_identity_year_that_disagrees_with_bound_evidence(self) -> None:
        self._add_unique_records()
        record_path = self.records_root / "COV-CN-0001.json"
        record = json_file(record_path)
        record["identity"]["publication_year"] = 2023
        record_path.write_text(
            json.dumps(record, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

        result = build_library(self.cover_root, self.registry)

        self.assertEqual("building", result["status"])
        self.assertEqual(49, result["valid_record_count"])
        self.assertEqual(1, result["invalid_record_count"])
        self.assertIn("publication year evidence", result["invalid_records"][0]["reason"])

    def test_non_json_record_inputs_are_manifest_bound_and_block_availability(self) -> None:
        self._add_unique_records()
        (self.records_root / ".DS_Store").write_bytes(b"finder metadata")
        nested = self.records_root / "cache"
        nested.mkdir()
        (nested / "notes.bin").write_bytes(b"not a record")

        result = build_library(self.cover_root, self.registry)

        self.assertEqual("building", result["status"])
        self.assertEqual(2, result["invalid_record_count"])
        self.assertEqual(
            ["records/.DS_Store", "records/cache/notes.bin"],
            [item["path"] for item in result["invalid_records"]],
        )
        manifest = json_file(self.cover_root / "manifest.json")
        rejected = [item for item in manifest["records"] if item["record_id"] is None]
        self.assertEqual(
            ["records/.DS_Store", "records/cache/notes.bin"],
            [item["path"] for item in rejected],
        )

    def test_wrong_record_filename_and_noncontiguous_ids_are_rejected(self) -> None:
        wrong_file, _ = self._add_record("COV-CN-0001", filename="wrong.json")

        wrong_result = build_library(self.cover_root, self.registry)

        self.assertEqual(1, wrong_result["invalid_record_count"])
        self.assertIn("filename", wrong_result["invalid_records"][0]["reason"])
        wrong_file.unlink()
        (self.assets_root / "COV-CN-0001.png").unlink()
        self._add_record("COV-CN-0002")

        gap_result = build_library(self.cover_root, self.registry)

        self.assertEqual("building", gap_result["status"])
        self.assertIn("non_contiguous_record_ids", [item["code"] for item in gap_result["errors"]])

    def test_source_and_book_case_ids_must_each_form_a_contiguous_prefix(self) -> None:
        record_path, _ = self._add_record("COV-CN-0001", book_case_id="BOOK-CN-0002")
        book_gap_result = build_library(self.cover_root, self.registry)
        self.assertIn(
            "non_contiguous_book_case_ids",
            [item["code"] for item in book_gap_result["errors"]],
        )

        registry = json_file(self.registry)
        registry["sources"] = [registry["sources"][1]]
        self.registry.write_text(
            json.dumps(registry, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        record = json_file(record_path)
        source = registry["sources"][0]
        record["identity"]["book_case_id"] = "BOOK-CN-0001"
        record["source"] = {
            "source_registry_id": source["source_registry_id"],
            "source_url": source["source_url"],
            "platform": source["platform"],
            "collected_at": source["collected_at"],
        }
        record_path.write_text(
            json.dumps(record, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

        source_gap_result = build_library(self.cover_root, self.registry)

        self.assertIn(
            "non_contiguous_source_ids",
            [item["code"] for item in source_gap_result["errors"]],
        )
        report = validate_library(self.cover_root, self.registry, required_count=1)
        self.assertFalse(report["valid"])
        self.assertIn("non_contiguous_source_ids", " ".join(report["errors"]))

    def test_fifty_valid_plus_one_invalid_record_stays_building(self) -> None:
        self._add_unique_records()
        invalid_record, _ = self._add_record("COV-CN-0051")
        invalid = json_file(invalid_record)
        invalid["asset"]["sha256"] = "0" * 64
        invalid_record.write_text(json.dumps(invalid, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        result = build_library(self.cover_root, self.registry)

        self.assertEqual(50, result["valid_record_count"])
        self.assertEqual(1, result["invalid_record_count"])
        self.assertEqual(
            [
                {
                    "code": "unreferenced_assets",
                    "paths": ["assets/COV-CN-0051.png"],
                    "record_ids": [],
                }
            ],
            result["errors"],
        )
        self.assertEqual("building", result["status"])
        self.assertEqual("building", json_file(self.cover_root / "manifest.json")["status"])

    def test_duplicate_asset_hash_is_a_library_error_and_blocks_availability(self) -> None:
        self._add_unique_records()
        duplicate_bytes = (self.assets_root / "COV-CN-0001.png").read_bytes()
        self._add_record("COV-CN-0051", asset_bytes=duplicate_bytes)

        result = build_library(self.cover_root, self.registry)

        duplicate_hash = hashlib.sha256(duplicate_bytes).hexdigest()
        self.assertEqual("building", result["status"])
        self.assertEqual(51, result["valid_record_count"])
        self.assertIn(
            {
                "code": "duplicate_asset_sha256",
                "value": duplicate_hash,
                "paths": ["assets/COV-CN-0001.png", "assets/COV-CN-0051.png"],
                "record_ids": ["COV-CN-0001", "COV-CN-0051"],
            },
            result["errors"],
        )

    def test_unreferenced_duplicate_asset_is_diagnosed_from_entire_asset_tree(self) -> None:
        self._add_unique_records()
        duplicate_bytes = (self.assets_root / "COV-CN-0001.png").read_bytes()
        extra_asset = self.assets_root / "unreferenced-duplicate.png"
        extra_asset.write_bytes(duplicate_bytes)

        result = build_library(self.cover_root, self.registry)

        duplicate_hash = hashlib.sha256(duplicate_bytes).hexdigest()
        expected_errors = [
            {
                "code": "duplicate_asset_sha256",
                "value": duplicate_hash,
                "paths": ["assets/COV-CN-0001.png", "assets/unreferenced-duplicate.png"],
                "record_ids": ["COV-CN-0001"],
            },
            {
                "code": "unreferenced_assets",
                "paths": ["assets/unreferenced-duplicate.png"],
                "record_ids": [],
            },
        ]
        self.assertEqual("building", result["status"])
        self.assertEqual(50, result["valid_record_count"])
        self.assertEqual(expected_errors, result["errors"])
        manifest = json_file(self.cover_root / "manifest.json")
        self.assertEqual("building", manifest["status"])
        self.assertEqual(expected_errors, manifest["errors"])
        self.assertEqual(51, len(manifest["assets"]))
        self.assertEqual(50, len(json_file(self.cover_root / "catalog.json")["entries"]))

    def test_unreferenced_unique_asset_blocks_availability(self) -> None:
        self._add_unique_records()
        extra_asset = self.assets_root / "unreferenced-unique.png"
        extra_asset.write_bytes(self._make_png_bytes("unreferenced-unique"))

        result = build_library(self.cover_root, self.registry)

        expected_error = {
            "code": "unreferenced_assets",
            "paths": ["assets/unreferenced-unique.png"],
            "record_ids": [],
        }
        self.assertEqual("building", result["status"])
        self.assertEqual([expected_error], result["errors"])
        self.assertEqual([expected_error], json_file(self.cover_root / "manifest.json")["errors"])

    def test_one_asset_path_referenced_by_multiple_records_is_diagnosed(self) -> None:
        self._add_unique_records()
        shared_bytes = (self.assets_root / "COV-CN-0001.png").read_bytes()
        self._add_record(
            "COV-CN-0051",
            asset_name="COV-CN-0001.png",
            asset_bytes=shared_bytes,
        )

        result = build_library(self.cover_root, self.registry)

        expected_error = {
            "code": "asset_referenced_by_multiple_records",
            "paths": ["assets/COV-CN-0001.png"],
            "record_ids": ["COV-CN-0001", "COV-CN-0051"],
        }
        self.assertEqual("building", result["status"])
        self.assertIn(expected_error, result["errors"])
        self.assertIn(expected_error, json_file(self.cover_root / "manifest.json")["errors"])

    def test_duplicate_book_case_id_is_a_library_error_and_blocks_availability(self) -> None:
        self._add_unique_records()
        self._add_record("COV-CN-0051", book_case_id="BOOK-CN-0001")

        result = build_library(self.cover_root, self.registry)

        self.assertEqual("building", result["status"])
        self.assertIn(
            {
                "code": "duplicate_book_case_id",
                "value": "BOOK-CN-0001",
                "record_ids": ["COV-CN-0001", "COV-CN-0051"],
            },
            result["errors"],
        )

    def test_second_physical_record_with_duplicate_id_is_rejected_by_filename(self) -> None:
        self._add_unique_records()
        self._add_record(
            "COV-CN-0001",
            filename="duplicate-record-id.json",
            asset_name="duplicate-record-id.png",
            book_case_id="BOOK-CN-0051",
        )

        result = build_library(self.cover_root, self.registry)

        self.assertEqual("building", result["status"])
        self.assertEqual(1, result["invalid_record_count"])
        self.assertIn("filename", result["invalid_records"][0]["reason"])
        self.assertIn(
            {
                "code": "unreferenced_assets",
                "paths": ["assets/duplicate-record-id.png"],
                "record_ids": [],
            },
            result["errors"],
        )

    def test_atomic_replace_failure_preserves_inputs_target_and_cleans_sibling_temp(self) -> None:
        record, asset = self._add_record("COV-CN-0001")
        catalog = self.cover_root / "catalog.json"
        original_catalog = b'{"previous": true}\n'
        catalog.write_bytes(original_catalog)
        before = file_hashes([record, asset, self.registry])
        original_replace = Path.replace

        def fail_catalog_replace(source: Path, target: Path) -> Path:
            if Path(target) == catalog:
                raise OSError("injected catalog replace failure")
            return original_replace(source, target)

        with patch("ai.book_component_kb.build.Path.replace", new=fail_catalog_replace):
            with self.assertRaisesRegex(OSError, "injected catalog replace failure"):
                build_library(self.cover_root, self.registry)

        self.assertEqual(original_catalog, catalog.read_bytes())
        self.assertEqual(before, file_hashes([record, asset, self.registry]))
        self.assertEqual([], list(self.cover_root.rglob("*.tmp")))
        for name in CATEGORY_PATHS:
            self.assertTrue((self.cover_root / name).is_file(), name)

    def test_categories_cleanup_removes_only_direct_stale_json_and_links(self) -> None:
        self._add_record("COV-CN-0001")
        categories_root = self.cover_root / "categories"
        categories_root.mkdir()
        (categories_root / "stale.json").write_text('{"stale": true}\n', encoding="utf-8")
        outside = self.library_root / "outside.txt"
        outside.write_bytes(b"outside remains")
        (categories_root / "stale-link").symlink_to(outside)

        build_library(self.cover_root, self.registry)

        self.assertEqual(
            sorted(f"{name}.json" for name in CATEGORY_NAMES),
            sorted(path.name for path in categories_root.iterdir()),
        )
        self.assertEqual(b"outside remains", outside.read_bytes())
        manifest = json_file(self.cover_root / "manifest.json")
        self.assertEqual(list(CATEGORY_PATHS), [item["path"] for item in manifest["derived"][:4]])

    def test_categories_cleanup_fails_closed_on_unknown_directory_or_non_json_file(self) -> None:
        record, asset = self._add_record("COV-CN-0001")
        categories_root = self.cover_root / "categories"
        categories_root.mkdir()
        before = file_hashes([record, asset, self.registry])
        cases = (
            ("unknown directory", categories_root / "manual", True),
            ("non-JSON file", categories_root / "notes.txt", False),
        )
        for message, unexpected, is_directory in cases:
            with self.subTest(message=message):
                if is_directory:
                    unexpected.mkdir()
                else:
                    unexpected.write_text("manual content\n", encoding="utf-8")
                with self.assertRaisesRegex(ValueError, message):
                    build_library(self.cover_root, self.registry)
                self.assertTrue(unexpected.exists())
                self.assertFalse((self.cover_root / "catalog.json").exists())
                self.assertEqual(before, file_hashes([record, asset, self.registry]))
                if is_directory:
                    unexpected.rmdir()
                else:
                    unexpected.unlink()

    def test_cli_help_requires_explicit_paths(self) -> None:
        script = Path(__file__).parents[1] / "scripts" / "book_component_kb" / "build_library.py"
        completed = subprocess.run(
            [str(Path(__file__).parents[1] / ".venv" / "bin" / "python"), str(script), "--help"],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)
        self.assertIn("--component-root", completed.stdout)
        self.assertIn("--registry", completed.stdout)
        self.assertIn("required", completed.stdout)
        self.assertNotIn("Desktop", completed.stdout)


if __name__ == "__main__":
    unittest.main()
