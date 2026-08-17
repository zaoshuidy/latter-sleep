import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "fetch_upstream_skill.py"
INDEX = ROOT / "knowledge" / "indexes" / "upstream-skills.json"


def load_verify_snapshot():
    spec = importlib.util.spec_from_file_location("fetch_upstream_skill", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load fetch_upstream_skill.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.verify_snapshot


class UpstreamSnapshotTests(unittest.TestCase):
    def test_gc_upstream_is_complete_and_index_only(self):
        index = json.loads(INDEX.read_text(encoding="utf-8"))
        record = index["skills"][0]
        self.assertEqual("LiamGvchi/gc-minimal-zine-poster", record["repository"])
        self.assertGreaterEqual(record["stars_at_fetch"], 1000)
        self.assertEqual("MIT", record["license"])
        self.assertEqual("full-original-no-summary", record["preservation_mode"])
        self.assertRegex(record["commit"], r"^[0-9a-f]{40}$")

        snapshot = ROOT / record["snapshot_path"]
        actual = {path.relative_to(snapshot).as_posix() for path in snapshot.rglob("*") if path.is_file()}
        self.assertEqual(set(record["files"]), actual)
        for required in ["LICENSE", "README.md", "README.zh-CN.md", "SKILL.md", "examples/moon-tide.jpeg"]:
            self.assertIn(required, actual)

    def test_any_modified_upstream_file_is_detected(self):
        verify_snapshot = load_verify_snapshot()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "SKILL.md").write_text("original", encoding="utf-8")
            import hashlib
            expected = {"SKILL.md": hashlib.sha256(b"original").hexdigest()}
            self.assertEqual([], verify_snapshot(root, expected))
            (root / "SKILL.md").write_text("modified", encoding="utf-8")
            self.assertTrue(verify_snapshot(root, expected))


if __name__ == "__main__":
    unittest.main()
