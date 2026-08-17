from __future__ import annotations

import copy
import hashlib
import io
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from ai.book_component_kb.build import DERIVED_NAMES, build_library
from ai.book_component_kb.paths import sha256_file
from ai.book_component_kb.validate import validate_library


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "component-kb"


def load_fixture(name: str) -> dict[str, object]:
    return json.loads((FIXTURE_ROOT / name).read_text(encoding="utf-8"))


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value: dict[str, object]) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


class ComponentKnowledgeBaseValidateTests(unittest.TestCase):
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
        write_json(self.registry, load_fixture("source-registry.json"))

    def _png_bytes(self, seed: str) -> bytes:
        digest = hashlib.sha256(seed.encode("utf-8")).digest()
        pixels = (digest * 21)[: 12 * 18 * 3]
        output = io.BytesIO()
        Image.frombytes("RGB", (12, 18), pixels).save(output, format="PNG")
        return output.getvalue()

    def _add_record(
        self,
        record_id: str,
        *,
        book_case_id: str | None = None,
        asset_name: str | None = None,
        asset_bytes: bytes | None = None,
        lifecycle: str = "accumulation",
    ) -> tuple[Path, Path]:
        asset_name = asset_name or f"{record_id}.png"
        asset_bytes = asset_bytes or self._png_bytes(asset_name)
        asset_path = self.assets_root / asset_name
        asset_path.write_bytes(asset_bytes)
        record = copy.deepcopy(load_fixture("cover-record.json"))
        record["record_id"] = record_id
        record["identity"]["book_case_id"] = book_case_id or f"BOOK-CN-{record_id.rsplit('-', 1)[-1]}"
        record["asset"] = {
            "relative_path": f"cover/assets/{asset_name}",
            "sha256": hashlib.sha256(asset_bytes).hexdigest(),
            "mime_type": "image/png",
            "width": 12,
            "height": 18,
        }
        record["lifecycle"]["status"] = lifecycle
        record_path = self.records_root / f"{record_id}.json"
        write_json(record_path, record)
        return record_path, asset_path

    def _build_one(self) -> tuple[Path, Path]:
        record, asset = self._add_record("COV-CN-0001")
        build_library(self.cover_root, self.registry)
        return record, asset

    def _rehash_derived_in_manifest(self, relative_path: str) -> None:
        manifest_path = self.cover_root / "manifest.json"
        manifest = load_json(manifest_path)
        for item in manifest["derived"]:
            if item["path"] == relative_path:
                item["sha256"] = sha256_file(self.cover_root / relative_path)
                break
        else:
            self.fail(f"missing manifest derived entry: {relative_path}")
        write_json(manifest_path, manifest)

    def _tree_hashes(self) -> dict[str, str]:
        return {
            path.relative_to(self.library_root).as_posix(): sha256_file(path)
            for path in sorted(self.library_root.rglob("*"))
            if path.is_file() and not path.is_symlink()
        }

    def test_valid_library_reports_fixed_shape_and_caller_threshold(self) -> None:
        self._build_one()

        report = validate_library(self.cover_root, self.registry, required_count=1)

        self.assertEqual(
            {"valid", "status", "record_count", "errors", "warnings", "counts"},
            set(report),
        )
        self.assertTrue(report["valid"])
        self.assertEqual("available", report["status"])
        self.assertEqual(1, report["record_count"])
        self.assertEqual([], report["errors"])
        self.assertEqual([], report["warnings"])
        self.assertEqual(
            {"records": 1, "assets": 1, "books": 1, "categories": 4, "derived": 6},
            report["counts"],
        )

    def test_modified_asset_breaks_hash_chain(self) -> None:
        _, asset = self._build_one()
        asset.write_bytes(self._png_bytes("changed"))

        report = validate_library(self.cover_root, self.registry, required_count=1)

        self.assertFalse(report["valid"])
        self.assertNotEqual("available", report["status"])
        self.assertIn("asset hash mismatch", " ".join(report["errors"]))

    def test_real_image_decode_is_rechecked(self) -> None:
        _, asset = self._build_one()
        corrupt = b"not a decodable image"
        asset.write_bytes(corrupt)
        record = load_json(self.records_root / "COV-CN-0001.json")
        record["asset"]["sha256"] = hashlib.sha256(corrupt).hexdigest()
        write_json(self.records_root / "COV-CN-0001.json", record)

        report = validate_library(self.cover_root, self.registry, required_count=1)

        self.assertFalse(report["valid"])
        self.assertIn("not a decodable image", " ".join(report["errors"]))

    def test_modified_record_breaks_hash_chain(self) -> None:
        record_path, _ = self._build_one()
        record = load_json(record_path)
        record["identity"]["book_title"] = "tampered title"
        write_json(record_path, record)

        report = validate_library(self.cover_root, self.registry, required_count=1)

        self.assertFalse(report["valid"])
        self.assertIn("record hash mismatch", " ".join(report["errors"]))

    def test_source_registry_binding_is_recomputed(self) -> None:
        record_path, _ = self._build_one()
        record = load_json(record_path)
        record["source"]["source_url"] = "https://example.com/different"
        write_json(record_path, record)

        report = validate_library(self.cover_root, self.registry, required_count=1)

        self.assertFalse(report["valid"])
        self.assertIn("source registry binding mismatch", " ".join(report["errors"]))

    def test_builder_and_validator_agree_on_source_binding_conflict(self) -> None:
        for index in range(1, 51):
            self._add_record(f"COV-CN-{index:04d}")
        record_path = self.records_root / "COV-CN-0001.json"
        record = load_json(record_path)
        record["source"]["platform"] = "不同平台"
        write_json(record_path, record)

        build_result = build_library(self.cover_root, self.registry)
        report = validate_library(self.cover_root, self.registry, required_count=50)

        self.assertEqual("building", build_result["status"])
        self.assertEqual(49, build_result["valid_record_count"])
        self.assertFalse(report["valid"])
        self.assertEqual("invalid", report["status"])
        self.assertIn("source registry binding mismatch", " ".join(report["errors"]))

    def test_builder_and_validator_reject_identity_year_without_matching_evidence(self) -> None:
        record_path, _ = self._add_record("COV-CN-0001")
        record = load_json(record_path)
        record["identity"]["publication_year"] = 2023
        write_json(record_path, record)

        build_result = build_library(self.cover_root, self.registry)
        report = validate_library(self.cover_root, self.registry, required_count=1)

        self.assertEqual("building", build_result["status"])
        self.assertEqual(0, build_result["valid_record_count"])
        self.assertFalse(report["valid"])
        self.assertIn("publication year evidence", " ".join(report["errors"]))

    def test_archived_record_is_audited_but_not_counted_as_active(self) -> None:
        for index in range(1, 50):
            self._add_record(f"COV-CN-{index:04d}")
        self._add_record("COV-CN-0050", lifecycle="archived")
        build_library(self.cover_root, self.registry)

        report = validate_library(self.cover_root, self.registry, required_count=50)

        self.assertTrue(report["valid"])
        self.assertEqual("building", report["status"])
        self.assertEqual(49, report["record_count"])
        self.assertEqual(49, report["counts"]["books"])
        self.assertEqual(50, report["counts"]["records"])

    def test_non_json_record_inventory_is_bound_and_rejected_consistently(self) -> None:
        self._add_record("COV-CN-0001")
        (self.records_root / ".DS_Store").write_bytes(b"finder metadata")

        build_result = build_library(self.cover_root, self.registry)
        report = validate_library(self.cover_root, self.registry, required_count=1)

        self.assertEqual("building", build_result["status"])
        self.assertEqual(1, build_result["invalid_record_count"])
        self.assertFalse(report["valid"])
        self.assertIn("record input must be JSON", " ".join(report["errors"]))
        manifest = load_json(self.cover_root / "manifest.json")
        self.assertIn("records/.DS_Store", [item["path"] for item in manifest["records"]])

    def test_malformed_registry_returns_a_fixed_invalid_report_and_cli_exit_one(self) -> None:
        self._build_one()
        registry = load_json(self.registry)
        del registry["sources"][0]["platform"]
        write_json(self.registry, registry)

        report = validate_library(self.cover_root, self.registry, required_count=1)
        completed = subprocess.run(
            [
                str(PROJECT_ROOT / ".venv" / "bin" / "python"),
                str(PROJECT_ROOT / "scripts" / "book_component_kb" / "validate_library.py"),
                "--component-root",
                str(self.cover_root),
                "--registry",
                str(self.registry),
                "--required-count",
                "1",
            ],
            cwd=PROJECT_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(
            {"valid", "status", "record_count", "errors", "warnings", "counts"},
            set(report),
        )
        self.assertFalse(report["valid"])
        self.assertEqual("invalid", report["status"])
        self.assertEqual(1, completed.returncode, completed.stderr)
        self.assertEqual(report, json.loads(completed.stdout))

    def test_category_catalog_and_index_tamper_are_independently_rejected(self) -> None:
        tamper_cases = (
            ("categories/by-composition.json", lambda data: data["entries"].clear()),
            ("catalog.json", lambda data: data["entries"][0].update({"book_case_id": "FAKE"})),
            ("retrieval-index.json", lambda data: data["entries"][0].update({"title_zone": "bottom"})),
        )
        for relative_path, mutate in tamper_cases:
            with self.subTest(relative_path=relative_path):
                self._build_one()
                target = self.cover_root / relative_path
                data = load_json(target)
                mutate(data)
                write_json(target, data)
                self._rehash_derived_in_manifest(relative_path)

                report = validate_library(self.cover_root, self.registry, required_count=1)

                self.assertFalse(report["valid"])
                self.assertIn("derived agreement mismatch", " ".join(report["errors"]))
                for child in self.cover_root.iterdir():
                    if child.is_dir():
                        for nested in child.iterdir():
                            if nested.is_file() or nested.is_symlink():
                                nested.unlink()
                        child.rmdir()
                    else:
                        child.unlink()
                self.records_root.mkdir()
                self.assets_root.mkdir()

    def test_manifest_tamper_is_rejected_without_an_outer_hash(self) -> None:
        self._build_one()
        manifest_path = self.cover_root / "manifest.json"
        manifest = load_json(manifest_path)
        manifest["records"][0]["sha256"] = "0" * 64
        write_json(manifest_path, manifest)

        report = validate_library(self.cover_root, self.registry, required_count=1)

        self.assertFalse(report["valid"])
        self.assertIn("manifest records mismatch", " ".join(report["errors"]))

    def test_manifest_schema_version_and_component_constants_are_rejected_when_tampered(self) -> None:
        for field, tampered_value in (
            ("schema_version", "9.9"),
            ("component", "toc"),
        ):
            with self.subTest(field=field):
                self._build_one()
                manifest_path = self.cover_root / "manifest.json"
                manifest = load_json(manifest_path)
                manifest[field] = tampered_value
                write_json(manifest_path, manifest)

                report = validate_library(self.cover_root, self.registry, required_count=1)

                self.assertFalse(report["valid"])
                self.assertEqual("invalid", report["status"])
                self.assertIn(
                    f"manifest {field} mismatch",
                    " ".join(report["errors"]),
                )
                for child in self.cover_root.iterdir():
                    if child.is_dir():
                        for nested in child.iterdir():
                            if nested.is_file() or nested.is_symlink():
                                nested.unlink()
                        child.rmdir()
                    else:
                        child.unlink()
                self.records_root.mkdir()
                self.assets_root.mkdir()

    def test_duplicate_books_are_rejected(self) -> None:
        self._add_record("COV-CN-0001", book_case_id="BOOK-CN-0001")
        self._add_record("COV-CN-0002", book_case_id="BOOK-CN-0001")
        build_library(self.cover_root, self.registry)

        report = validate_library(self.cover_root, self.registry, required_count=2)

        self.assertFalse(report["valid"])
        self.assertIn("duplicate book_case_id", " ".join(report["errors"]))

    def test_duplicate_asset_content_is_rejected(self) -> None:
        shared = self._png_bytes("shared")
        self._add_record("COV-CN-0001", asset_bytes=shared)
        self._add_record("COV-CN-0002", asset_bytes=shared)
        build_library(self.cover_root, self.registry)

        report = validate_library(self.cover_root, self.registry, required_count=2)

        self.assertFalse(report["valid"])
        self.assertIn("duplicate asset sha256", " ".join(report["errors"]))

    def test_missing_and_extra_assets_break_exact_closure(self) -> None:
        for corruption in ("missing", "extra"):
            with self.subTest(corruption=corruption):
                _, asset = self._build_one()
                if corruption == "missing":
                    asset.unlink()
                else:
                    (self.assets_root / "extra.png").write_bytes(self._png_bytes("extra"))

                report = validate_library(self.cover_root, self.registry, required_count=1)

                self.assertFalse(report["valid"])
                self.assertIn(f"{corruption} asset", " ".join(report["errors"]))
                for child in self.cover_root.iterdir():
                    if child.is_dir():
                        for nested in child.iterdir():
                            if nested.is_file() or nested.is_symlink():
                                nested.unlink()
                        child.rmdir()
                    else:
                        child.unlink()
                self.records_root.mkdir()
                self.assets_root.mkdir()

    def test_year_and_component_are_rechecked(self) -> None:
        for field, value, expected in (
            (("identity", "publication_year"), 2016, "publication year out of range"),
            (("component_type",), "toc", "component mismatch"),
        ):
            with self.subTest(field=field):
                record_path, _ = self._build_one()
                record = load_json(record_path)
                target = record
                for key in field[:-1]:
                    target = target[key]
                target[field[-1]] = value
                write_json(record_path, record)

                report = validate_library(self.cover_root, self.registry, required_count=1)

                self.assertFalse(report["valid"])
                self.assertIn(expected, " ".join(report["errors"]))
                for child in self.cover_root.iterdir():
                    if child.is_dir():
                        for nested in child.iterdir():
                            if nested.is_file() or nested.is_symlink():
                                nested.unlink()
                        child.rmdir()
                    else:
                        child.unlink()
                self.records_root.mkdir()
                self.assets_root.mkdir()

    def test_status_and_count_mismatch_are_rejected_even_when_rehashed(self) -> None:
        for corruption in ("count", "status"):
            with self.subTest(corruption=corruption):
                self._build_one()
                catalog_path = self.cover_root / "catalog.json"
                manifest_path = self.cover_root / "manifest.json"
                catalog = load_json(catalog_path)
                manifest = load_json(manifest_path)
                if corruption == "count":
                    catalog["valid_record_count"] = 2
                    manifest["valid_record_count"] = 2
                else:
                    catalog["status"] = "available"
                    manifest["status"] = "available"
                write_json(catalog_path, catalog)
                for item in manifest["derived"]:
                    if item["path"] == "catalog.json":
                        item["sha256"] = sha256_file(catalog_path)
                write_json(manifest_path, manifest)

                report = validate_library(self.cover_root, self.registry, required_count=1)

                self.assertFalse(report["valid"])
                self.assertIn(f"{corruption} mismatch", " ".join(report["errors"]))
                for child in self.cover_root.iterdir():
                    if child.is_dir():
                        for nested in child.iterdir():
                            if nested.is_file() or nested.is_symlink():
                                nested.unlink()
                        child.rmdir()
                    else:
                        child.unlink()
                self.records_root.mkdir()
                self.assets_root.mkdir()

    def test_missing_derivatives_are_not_rebuilt_or_repaired(self) -> None:
        self._add_record("COV-CN-0001")
        before = self._tree_hashes()

        report = validate_library(self.cover_root, self.registry, required_count=1)

        self.assertFalse(report["valid"])
        self.assertNotEqual("available", report["status"])
        self.assertIn("missing derived file", " ".join(report["errors"]))
        self.assertEqual(before, self._tree_hashes())
        self.assertFalse(any((self.cover_root / name).exists() for name in (*DERIVED_NAMES, "manifest.json")))

    def test_validation_is_read_only_and_cli_building_exits_two(self) -> None:
        self._build_one()
        before = self._tree_hashes()

        report = validate_library(self.cover_root, self.registry, required_count=50)
        completed = subprocess.run(
            [
                str(PROJECT_ROOT / ".venv" / "bin" / "python"),
                str(PROJECT_ROOT / "scripts" / "book_component_kb" / "validate_library.py"),
                "--component-root",
                str(self.cover_root),
                "--registry",
                str(self.registry),
                "--required-count",
                "50",
            ],
            cwd=PROJECT_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertTrue(report["valid"])
        self.assertEqual("building", report["status"])
        self.assertEqual(1, report["record_count"])
        self.assertEqual(2, completed.returncode, completed.stderr)
        self.assertEqual(report, json.loads(completed.stdout))
        self.assertEqual(before, self._tree_hashes())


if __name__ == "__main__":
    unittest.main()
