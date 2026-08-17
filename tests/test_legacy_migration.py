import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "extract_legacy_sources.py"
BRAND = ROOT / "knowledge" / "brand-profiles" / "paper-boat.json"
REGISTRY = ROOT / "knowledge" / "indexes" / "legacy-reuse-registry.json"


def load_extract_selected():
    spec = importlib.util.spec_from_file_location("extract_legacy_sources", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load extract_legacy_sources.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.extract_selected


class LegacyMigrationTests(unittest.TestCase):
    def test_selective_extraction_handles_chinese_names_and_preserves_zip(self):
        extract_selected = load_extract_selected()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = root / "旧套件.zip"
            with ZipFile(archive, "w") as zf:
                zf.writestr("套件/目录设计/SKILL.md", "目录原件")
                zf.writestr("套件/封面设计/SKILL.md", "不应迁移")
            before = hashlib.sha256(archive.read_bytes()).hexdigest()
            target = root / "selected"
            result = extract_selected(
                archive,
                target,
                {"套件/目录设计/SKILL.md": "toc-design/SKILL.md"},
            )
            self.assertEqual(before, hashlib.sha256(archive.read_bytes()).hexdigest())
            self.assertEqual("目录原件", (target / "toc-design" / "SKILL.md").read_text(encoding="utf-8"))
            self.assertFalse((target / "封面设计").exists())
            self.assertEqual({"套件/目录设计/SKILL.md"}, set(result))

    def test_target_path_traversal_is_rejected(self):
        extract_selected = load_extract_selected()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = root / "suite.zip"
            with ZipFile(archive, "w") as zf:
                zf.writestr("safe.txt", "data")
            with self.assertRaisesRegex(ValueError, "unsafe target"):
                extract_selected(archive, root / "selected", {"safe.txt": "../escape.txt"})

    def test_paper_boat_profile_is_runtime_data_not_a_skill(self):
        profile = json.loads(BRAND.read_text(encoding="utf-8"))
        required = {
            "profile_id", "display_name", "positioning", "emotion_keywords",
            "required_elements", "forbidden_elements", "overridable_fields", "source_ref",
        }
        self.assertEqual(required, set(profile))
        self.assertIn("copyright-page-production", profile["forbidden_elements"])
        self.assertEqual("paper-boat", profile["profile_id"])

    def test_registry_has_only_necessary_migrations_and_one_deferred_indesign_index(self):
        registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
        migrated = [item for item in registry["entries"] if item["decision"] == "migrated-original"]
        deferred = [item for item in registry["entries"] if item["decision"] == "deferred"]
        self.assertEqual(6, len(migrated))
        self.assertEqual(["indesign-book-layout"], [item["id"] for item in deferred])
        self.assertTrue(all(set(["source_path", "sha256", "decision", "runtime_target", "notes"]).issubset(item) for item in registry["entries"]))
        self.assertFalse(any("cover" in item["id"] for item in migrated))
        self.assertIn("Windows COM", deferred[0]["notes"])
        self.assertIn("V1 不调用", deferred[0]["notes"])


if __name__ == "__main__":
    unittest.main()
