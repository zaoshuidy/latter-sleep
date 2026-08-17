import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills" / "review-book-production" / "scripts" / "review_project.py"
REQUIRED_CHECKS = {
    "toc_complete": True,
    "running_headers_consistent": True,
    "fonts_available": True,
    "no_overflow": True,
    "images_resolution_ok": True,
    "page_numbers_continuous": True,
    "prompts_complete": True,
}


def load_review_project():
    spec = importlib.util.spec_from_file_location("book_review_project", SCRIPT)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load review_project.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.review_project


def make_project(root: Path, sample: str = "approved", final: str = "approved") -> None:
    source = root / "source.txt"
    source.write_text("定稿正文", encoding="utf-8")
    expected = hashlib.sha256(source.read_bytes()).hexdigest()
    data = {
        "version": "1.0",
        "project_id": "P-500",
        "source_texts": [{"source_id": "TXT-001", "path": "source.txt", "expected_sha256": expected}],
        "production_checks": dict(REQUIRED_CHECKS),
        "gates": {"sample_review": sample, "final_review": final},
    }
    (root / "review-input.json").write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")


class ReviewTests(unittest.TestCase):
    def test_approved_project_requires_all_checks_and_two_approved_gates(self):
        review_project = load_review_project()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_project(root)
            report = review_project(root)
            self.assertEqual("approved", report["status"])
            self.assertEqual("complete", report["next_action"])

    def test_source_hash_difference_is_hard_block(self):
        review_project = load_review_project()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_project(root)
            (root / "source.txt").write_text("正文被改", encoding="utf-8")
            report = review_project(root)
            self.assertEqual("blocked", report["status"])
            self.assertIn("source_integrity", [item["check_id"] for item in report["checks"] if item["status"] == "failed"])

    def test_each_production_failure_blocks_final_approval(self):
        review_project = load_review_project()
        for check_id in REQUIRED_CHECKS:
            with self.subTest(check_id=check_id), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                make_project(root)
                data = json.loads((root / "review-input.json").read_text(encoding="utf-8"))
                data["production_checks"][check_id] = False
                (root / "review-input.json").write_text(json.dumps(data), encoding="utf-8")
                self.assertEqual("blocked", review_project(root)["status"])

    def test_pending_sample_gate_blocks_full_book_even_with_oral_approval(self):
        review_project = load_review_project()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_project(root, sample="pending", final="pending")
            report = review_project(root)
            self.assertEqual("blocked", report["status"])
            self.assertEqual("await_sample_review", report["next_action"])

    def test_final_review_must_be_approved_and_report_has_no_proofreading(self):
        review_project = load_review_project()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_project(root, sample="approved", final="pending")
            report = review_project(root)
            self.assertEqual("ready", report["status"])
            self.assertEqual("await_final_review", report["next_action"])
            self.assertNotIn("proofread", json.dumps(report).lower())
            self.assertNotIn("校对", json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    unittest.main()
