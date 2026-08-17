import subprocess
import sys
import tempfile
import unittest
import json
import os
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "install_personal.py"
SKILLS = (
    "book-production-router",
    "build-template-book",
    "plan-memorial-book",
    "design-book-editorial",
    "create-book-images",
    "review-book-production",
    "build-book-flipbook",
    "build-indesign-book",
    "evolve-book-skills",
)


class PersonalInstallTests(unittest.TestCase):
    def run_installer(
        self,
        runtime: Path,
        skill_home: Path,
        *extra: str,
        skip_dependencies: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        dependency_args = ["--skip-dependencies"] if skip_dependencies else []
        return subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "--source",
                str(ROOT),
                "--runtime",
                str(runtime),
                "--skill-home",
                str(skill_home),
                *dependency_args,
                *extra,
            ],
            text=True,
            capture_output=True,
        )

    def test_installs_shared_runtime_and_nine_skill_entries(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            runtime = base / "runtime"
            skill_home = base / "skills"
            result = self.run_installer(runtime, skill_home)
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual("1.2.0", (runtime / "VERSION").read_text(encoding="utf-8").strip())
            for name in SKILLS:
                entry = skill_home / name
                self.assertTrue(entry.exists(), name)
                self.assertEqual((runtime / "skills" / name).resolve(), entry.resolve())
            self.assertFalse(any(runtime.rglob("__pycache__")))
            self.assertFalse((runtime / ".venv").exists())

    def test_install_writes_machine_readable_skill_and_knowledge_location_index(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            runtime = base / "runtime"
            skill_home = base / "skills"
            result = self.run_installer(runtime, skill_home)
            self.assertEqual(0, result.returncode, result.stderr)
            install_result = json.loads(result.stdout)

            runtime_index_path = runtime / "LOCATION-INDEX.json"
            pointer_index_path = skill_home / "BOOK-PRODUCTION-LOCATION.json"
            self.assertTrue(runtime_index_path.is_file())
            self.assertTrue(pointer_index_path.is_file())
            runtime_index = json.loads(runtime_index_path.read_text(encoding="utf-8"))
            pointer_index = json.loads(pointer_index_path.read_text(encoding="utf-8"))
            self.assertEqual("book-production-skills-v1", runtime_index["suite"])
            self.assertEqual(str(ROOT.resolve()), runtime_index["locations"]["maintenance_source"])
            self.assertEqual(str(runtime.resolve()), runtime_index["locations"]["installed_runtime"])
            self.assertEqual(str(runtime.resolve() / "LOCATION-INDEX.json"), pointer_index["location_index"])
            self.assertEqual(pointer_index["location_index"], install_result["location_index"])
            self.assertEqual(set(SKILLS), set(runtime_index["skills"]))
            self.assertEqual(
                str(runtime.resolve() / "knowledge" / "indexes" / "design-case-index.json"),
                runtime_index["knowledge"]["design_cases"],
            )
            self.assertIn("approved_project_cases", runtime_index["knowledge"])
            self.assertEqual(
                str(
                    runtime.resolve()
                    / "knowledge"
                    / "indexes"
                    / "approved-project-case-index.json"
                ),
                runtime_index["knowledge"]["approved_project_cases"],
            )
            self.assertEqual(
                str(runtime.resolve() / "knowledge" / "maintenance" / "inbox"),
                runtime_index["knowledge"]["maintenance_inbox"],
            )
            self.assertEqual(
                str(runtime.resolve() / "knowledge" / "maintenance" / "reports"),
                runtime_index["knowledge"]["maintenance_reports"],
            )
            component_root = (
                runtime.resolve() / "knowledge" / "book-component-libraries"
            )
            expected_component_locations = {
                "component_source_registry": component_root / "source-registry.json",
                "cover_library_root": component_root / "cover",
                "cover_manifest": component_root / "cover" / "manifest.json",
                "cover_records": component_root / "cover" / "records",
                "cover_assets": component_root / "cover" / "assets",
                "chapter_opener_library_root": component_root / "chapter-opener",
                "chapter_opener_manifest": component_root / "chapter-opener" / "manifest.json",
                "chapter_opener_records": component_root / "chapter-opener" / "records",
                "chapter_opener_assets": component_root / "chapter-opener" / "assets",
            }
            for key, expected in expected_component_locations.items():
                with self.subTest(key=key):
                    self.assertEqual(str(expected), runtime_index["knowledge"][key])
                    self.assertTrue(expected.exists(), expected)
            for path in runtime_index["knowledge"].values():
                self.assertTrue(Path(path).exists(), path)

    def test_refuses_to_overwrite_an_unmanaged_skill(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            runtime = base / "runtime"
            skill_home = base / "skills"
            conflict = skill_home / "book-production-router"
            conflict.mkdir(parents=True)
            marker = conflict / "KEEP.txt"
            marker.write_text("personal", encoding="utf-8")
            result = self.run_installer(runtime, skill_home, "--replace")
            self.assertNotEqual(0, result.returncode)
            self.assertIn("unmanaged Skill entry", result.stderr)
            self.assertEqual("personal", marker.read_text(encoding="utf-8"))
            self.assertFalse(runtime.exists())

    def test_replace_is_allowed_for_entries_managed_by_this_runtime(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            runtime = base / "runtime"
            skill_home = base / "skills"
            first = self.run_installer(runtime, skill_home)
            self.assertEqual(0, first.returncode, first.stderr)
            second = self.run_installer(runtime, skill_home, "--replace")
            self.assertEqual(0, second.returncode, second.stderr)
            self.assertTrue((skill_home / "evolve-book-skills").exists())

    def test_default_install_creates_an_isolated_runnable_python(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            runtime = base / "runtime"
            skill_home = base / "skills"
            result = self.run_installer(runtime, skill_home, skip_dependencies=False)
            self.assertEqual(0, result.returncode, result.stderr)
            runtime_python = runtime / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
            self.assertTrue(runtime_python.is_file())
            imports = subprocess.run(
                [str(runtime_python), "-c", "import yaml, jsonschema, certifi"],
                text=True,
                capture_output=True,
            )
            self.assertEqual(0, imports.returncode, imports.stderr)


if __name__ == "__main__":
    unittest.main()
