from copy import deepcopy
from contextlib import ExitStack
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from ai.contracts import validate_data
from ai.indesign_templates import can_activate, evaluate_evidence, verify_original


ROOT = Path(__file__).resolve().parents[1]
LULU_EVIDENCE_PATH = ROOT / "references" / "templates" / "lulu-a5" / "evidence.json"
REGISTRY_PATH = ROOT / "references" / "templates" / "registry.json"
EXPECTED_EVIDENCE_ERRORS = [
    "requires two Chinese published-book references",
    "requires one Adobe source",
    "requires one print or trim source",
    "requires reviewed field mapping",
]


class TemplateEvidenceContractTests(unittest.TestCase):
    def valid_candidate_record(self):
        return {
            "schema_version": "1.0",
            "evidence_id": "EVD-LULU-A5-001",
            "template_id": "TPL-LULU-A5-INTERIOR",
            "status": "candidate",
            "original": {
                "provider": "Lulu",
                "source_url": "https://assets.lulu.com/media/templates/book/lulu-book-template-all-a5.zip",
                "relative_path": "research/reference-originals/lulu-book-template-all-a5.zip",
                "sha256": "B604553285B3C811350F34D499377D63E74B9ACFBBD7524FFA4D5871F304A243",
                "format": "zip-with-indd-idml",
            },
            "chinese_book_references": [],
            "adobe_sources": [],
            "print_sources": [],
            "field_mapping_path": None,
            "activation_errors": EXPECTED_EVIDENCE_ERRORS.copy(),
        }

    def valid_approved_record(self):
        record = self.valid_candidate_record()
        record["status"] = "approved"
        record["chinese_book_references"] = [
            "ISBN 9787100000001 / 某出版社 / 2022",
            "ISBN 9787100000002 / 某出版社 / 2024",
        ]
        record["adobe_sources"] = [
            "https://helpx.adobe.com/indesign/using/templates.html",
        ]
        record["print_sources"] = [
            "https://www.example.com/print-trim-guide",
        ]
        record["field_mapping_path"] = "references/templates/lulu-a5/field-mapping-reviewed.json"
        record["activation_errors"] = []
        return record

    def assertSchemaErrorsContain(self, payload, schema_name, *expected_fragments):
        errors = validate_data(payload, schema_name)
        self.assertTrue(errors, "expected schema errors")
        joined = "\n".join(errors)
        for fragment in expected_fragments:
            self.assertIn(fragment, joined)
        return errors

    def test_candidate_record_is_schema_valid(self):
        self.assertEqual([], validate_data(self.valid_candidate_record(), "template-evidence"))

    def test_approved_record_requires_closed_evidence_gate(self):
        record = self.valid_candidate_record()
        record["status"] = "approved"
        self.assertTrue(validate_data(record, "template-evidence"))

    def test_approved_record_is_schema_valid_once_gate_is_complete(self):
        self.assertEqual([], validate_data(self.valid_approved_record(), "template-evidence"))

    def test_approved_record_rejects_each_open_evidence_gate_independently(self):
        cases = [
            (
                "fewer than two chinese_book_references",
                lambda record: record.__setitem__("chinese_book_references", ["ISBN 9787100000001 / 某出版社 / 2022"]),
                ("too short",),
            ),
            (
                "empty adobe_sources",
                lambda record: record.__setitem__("adobe_sources", []),
                ("non-empty",),
            ),
            (
                "empty print_sources",
                lambda record: record.__setitem__("print_sources", []),
                ("non-empty",),
            ),
            (
                "null field_mapping_path",
                lambda record: record.__setitem__("field_mapping_path", None),
                ("not of type 'string'",),
            ),
            (
                "empty field_mapping_path",
                lambda record: record.__setitem__("field_mapping_path", ""),
                ("non-empty",),
            ),
            (
                "nonempty activation_errors",
                lambda record: record.__setitem__("activation_errors", ["still pending"]),
                ("expected to be empty",),
            ),
        ]

        for label, mutate, expected_fragments in cases:
            with self.subTest(label=label):
                record = deepcopy(self.valid_approved_record())
                mutate(record)
                self.assertSchemaErrorsContain(record, "template-evidence", *expected_fragments)

    def test_schema_is_closed_to_unexpected_properties(self):
        record = self.valid_candidate_record()
        record["unexpected"] = True
        self.assertSchemaErrorsContain(record, "template-evidence", "Additional properties are not allowed")


class EvidenceRuntimeTests(unittest.TestCase):
    def load_lulu_record(self):
        return json.loads(LULU_EVIDENCE_PATH.read_text(encoding="utf-8"))

    def make_record(self, relative_path, sha256):
        return {
            "original": {
                "relative_path": relative_path,
                "sha256": sha256,
            }
        }

    def create_file(self, path, content=b"original"):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return hashlib.sha256(content).hexdigest().upper()

    def create_symlink_or_skip(self, link_path, target, is_directory=False):
        try:
            if is_directory:
                link_path.symlink_to(target, target_is_directory=True)
            else:
                link_path.symlink_to(target)
        except (NotImplementedError, OSError) as exc:
            self.skipTest(f"symlink creation denied by OS: {exc}")

    def patch_link_flags(self, *, symlink_paths=(), junction_paths=()):
        symlink_values = {Path(path).resolve() for path in symlink_paths}
        junction_values = {Path(path).resolve() for path in junction_paths}
        original_is_junction = getattr(Path, "is_junction", None)

        def fake_is_symlink(path_obj):
            return path_obj.resolve() in symlink_values

        def fake_is_junction(path_obj):
            return path_obj.resolve() in junction_values

        patches = [mock.patch.object(Path, "is_symlink", autospec=True, side_effect=fake_is_symlink)]
        if original_is_junction is not None:
            patches.append(
                mock.patch.object(Path, "is_junction", autospec=True, side_effect=fake_is_junction)
            )
        return patches

    def test_evaluate_evidence_returns_exact_missing_requirements_in_order(self):
        errors = evaluate_evidence(
            {
                "chinese_book_references": [],
                "adobe_sources": [],
                "print_sources": [],
                "field_mapping_path": None,
            }
        )
        self.assertEqual(EXPECTED_EVIDENCE_ERRORS, errors)

    def test_verify_original_rejects_escape_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cases = [
                ("absolute", "C:/outside/original.idml"),
                ("traversal", "../outside/original.idml"),
            ]
            for label, relative_path in cases:
                with self.subTest(label=label):
                    record = {
                        "original": {
                            "relative_path": relative_path,
                            "sha256": "0" * 64,
                        }
                    }
                    with self.assertRaisesRegex(ValueError, "under root"):
                        verify_original(root, record)

    def test_verify_original_reports_sha256_on_hash_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact = root / "original.idml"
            artifact.write_bytes(b"original")
            record = {
                "original": {"relative_path": "original.idml", "sha256": "0" * 64}
            }
            with self.assertRaisesRegex(ValueError, "SHA-256"):
                verify_original(root, record)

    def test_verify_original_rejects_mocked_symlink_leaf(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            leaf = root / "original.idml"
            sha256 = self.create_file(leaf)

            with self.patch_link_flags(symlink_paths=[leaf])[0]:
                with self.assertRaisesRegex(ValueError, "symlink|links"):
                    verify_original(root, self.make_record("original.idml", sha256))

    def test_verify_original_rejects_mocked_symlinked_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sha256 = self.create_file(root / "original.idml")

            with self.patch_link_flags(symlink_paths=[root])[0]:
                with self.assertRaisesRegex(ValueError, "symlink|links"):
                    verify_original(root, self.make_record("original.idml", sha256))

    def test_verify_original_rejects_mocked_intermediate_symlink(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            intermediate = root / "nested"
            sha256 = self.create_file(intermediate / "original.idml")

            with self.patch_link_flags(symlink_paths=[intermediate])[0]:
                with self.assertRaisesRegex(ValueError, "symlink|links"):
                    verify_original(root, self.make_record("nested/original.idml", sha256))

    def test_verify_original_rejects_mocked_junction_leaf_when_supported(self):
        if not hasattr(Path, "is_junction"):
            self.skipTest("Path.is_junction is unavailable on this Python build")

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            leaf = root / "original.idml"
            sha256 = self.create_file(leaf)

            with self.patch_link_flags(junction_paths=[leaf])[0], self.patch_link_flags(
                junction_paths=[leaf]
            )[1]:
                with self.assertRaisesRegex(ValueError, "links"):
                    verify_original(root, self.make_record("original.idml", sha256))

    def test_verify_original_rejects_mocked_junction_root_when_supported(self):
        if not hasattr(Path, "is_junction"):
            self.skipTest("Path.is_junction is unavailable on this Python build")

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sha256 = self.create_file(root / "original.idml")
            patches = self.patch_link_flags(junction_paths=[root])

            with ExitStack() as stack:
                for patch in patches:
                    stack.enter_context(patch)
                with self.assertRaisesRegex(ValueError, "links"):
                    verify_original(root, self.make_record("original.idml", sha256))

    def test_verify_original_rejects_mocked_junction_intermediate_when_supported(self):
        if not hasattr(Path, "is_junction"):
            self.skipTest("Path.is_junction is unavailable on this Python build")

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            intermediate = root / "nested"
            sha256 = self.create_file(intermediate / "original.idml")
            patches = self.patch_link_flags(junction_paths=[intermediate])

            with ExitStack() as stack:
                for patch in patches:
                    stack.enter_context(patch)
                with self.assertRaisesRegex(ValueError, "links"):
                    verify_original(root, self.make_record("nested/original.idml", sha256))

    def test_verify_original_rejects_symlink_leaf(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target = root / "target.idml"
            sha256 = self.create_file(target)
            link = root / "leaf-link.idml"
            self.create_symlink_or_skip(link, target)

            with self.assertRaisesRegex(ValueError, "symlink|links"):
                verify_original(root, self.make_record("leaf-link.idml", sha256))

    def test_verify_original_rejects_symlinked_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            real_root = workspace / "real-root"
            real_root.mkdir()
            sha256 = self.create_file(real_root / "original.idml")
            linked_root = workspace / "linked-root"
            self.create_symlink_or_skip(linked_root, real_root, is_directory=True)

            with self.assertRaisesRegex(ValueError, "symlink|links"):
                verify_original(linked_root, self.make_record("original.idml", sha256))

    def test_verify_original_rejects_intermediate_symlink(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            target_dir = root / "actual"
            target_dir.mkdir()
            sha256 = self.create_file(target_dir / "original.idml")
            linked_dir = root / "linked-dir"
            self.create_symlink_or_skip(linked_dir, target_dir, is_directory=True)

            with self.assertRaisesRegex(ValueError, "symlink|links"):
                verify_original(root, self.make_record("linked-dir/original.idml", sha256))

    def test_registered_lulu_record_is_schema_valid_and_candidate_only(self):
        record = self.load_lulu_record()
        self.assertEqual([], validate_data(record, "template-evidence"))
        self.assertEqual("candidate", record["status"])
        self.assertEqual([], record["chinese_book_references"])
        self.assertEqual([], record["adobe_sources"])
        self.assertEqual([], record["print_sources"])
        self.assertIsNone(record["field_mapping_path"])
        self.assertEqual(EXPECTED_EVIDENCE_ERRORS, record["activation_errors"])

    def test_registered_lulu_record_hash_matches_real_zip_and_verifies(self):
        record = self.load_lulu_record()
        artifact = ROOT / record["original"]["relative_path"]
        digest = hashlib.sha256(artifact.read_bytes()).hexdigest().upper()
        self.assertEqual(record["original"]["sha256"], digest)
        self.assertEqual(artifact, verify_original(ROOT, record))

    def test_can_activate_is_false_for_candidate_lulu_record(self):
        self.assertFalse(can_activate(ROOT, self.load_lulu_record()))

    def test_registry_links_to_evidence_without_duplicating_record(self):
        registry = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
        self.assertEqual({"schema_version", "templates"}, set(registry))
        self.assertEqual("1.0", registry["schema_version"])
        self.assertEqual(1, len(registry["templates"]))

        entry = registry["templates"][0]
        self.assertEqual({"template_id", "status", "evidence_path"}, set(entry))
        self.assertEqual("TPL-LULU-A5-INTERIOR", entry["template_id"])
        self.assertEqual("candidate", entry["status"])
        self.assertEqual("references/templates/lulu-a5/evidence.json", entry["evidence_path"])
        self.assertNotIn("original", entry)
        self.assertEqual(self.load_lulu_record(), json.loads((ROOT / entry["evidence_path"]).read_text(encoding="utf-8")))


if __name__ == "__main__":
    unittest.main()
