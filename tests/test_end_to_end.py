import hashlib
import json
import unittest
from pathlib import Path

from ai.contracts import validate_data


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "four-seasons-letters"


class EndToEndTests(unittest.TestCase):
    def test_example_runs_from_intake_to_two_approved_gates(self):
        project = json.loads((EXAMPLE / "project-config.json").read_text(encoding="utf-8"))
        assets = json.loads((EXAMPLE / "assets" / "asset-manifest.json").read_text(encoding="utf-8"))
        content_map = json.loads((EXAMPLE / "output" / "content-map.json").read_text(encoding="utf-8"))
        self.assertEqual([], validate_data(project, "project-config"))
        self.assertEqual([], validate_data(assets, "asset-manifest"))
        source = EXAMPLE / "content" / "source.txt"
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        self.assertEqual(digest, content_map["source_text_hashes"]["TXT-001"])

        for direction in ["direction-a", "direction-b"]:
            genome = json.loads((EXAMPLE / "output" / direction / "design-genome.json").read_text(encoding="utf-8"))
            cover = json.loads((EXAMPLE / "output" / direction / "cover-prompt.json").read_text(encoding="utf-8"))
            html = (EXAMPLE / "output" / direction / "visual-proposal.html").read_text(encoding="utf-8")
            self.assertEqual([], validate_data(genome, "design-genome"))
            self.assertEqual([], validate_data(cover, "cover-prompt"))
            self.assertIn("四时来信", html)
            self.assertIn("春归", html)
            self.assertNotIn("<canvas", html.lower())

        image_manifest = json.loads((EXAMPLE / "output" / "image-manifest.json").read_text(encoding="utf-8"))
        self.assertEqual([], validate_data(image_manifest, "image-manifest"))
        for item in image_manifest["images"]:
            self.assertTrue((EXAMPLE / "output" / item["prompt_file"]).is_file())

        gates = json.loads((EXAMPLE / "output" / "gate-status.json").read_text(encoding="utf-8"))
        review = json.loads((EXAMPLE / "output" / "review-report.json").read_text(encoding="utf-8"))
        self.assertEqual({"sample_review": "approved", "final_review": "approved"}, gates)
        self.assertEqual("approved", review["status"])

    def test_example_output_excludes_deferred_scopes(self):
        forbidden = ["copyright", "indesign", "proofread", "版权页", "校对"]
        for path in (EXAMPLE / "output").rglob("*"):
            if not path.is_file():
                continue
            text = path.read_text(encoding="utf-8", errors="ignore").lower()
            for term in forbidden:
                self.assertNotIn(term, text, f"{term} in {path}")

    def test_human_docs_and_release_manifest_exist(self):
        for name in ["图书生产Skills套件使用说明.md", "旧Skill迁移与保留说明.md", "知识库每周维护说明.md"]:
            self.assertTrue((ROOT / "docs" / name).is_file(), name)
        self.assertTrue((ROOT / "RELEASE-MANIFEST.json").is_file())


if __name__ == "__main__":
    unittest.main()
