import hashlib
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "knowledge" / "indexes" / "approved-project-case-index.json"
INBOX = ROOT / "knowledge" / "maintenance" / "inbox" / "2026-08-14.json"


class ApprovedProjectCaseTests(unittest.TestCase):
    def test_lost_human_world_toc_and_running_headers_are_hash_bound_positive_cases(self):
        self.assertTrue(INDEX.is_file(), INDEX)
        index = json.loads(INDEX.read_text(encoding="utf-8"))

        self.assertEqual("1.0", index["version"])
        self.assertEqual("positive-project-evidence", index["library_role"])
        self.assertEqual(
            {
                "APC-LOST-HUMAN-WORLD-TOC-001": "toc",
                "APC-LOST-HUMAN-WORLD-RUNNING-HEADERS-001": "running-headers",
            },
            {case["case_id"]: case["page_component"] for case in index["cases"]},
        )

        for case in index["cases"]:
            with self.subTest(case_id=case["case_id"]):
                self.assertEqual("BOOK-LOST-HUMAN-WORLD", case["project_id"])
                self.assertEqual("approved-positive", case["status"])
                self.assertEqual("user-direct", case["approval"]["source"])
                self.assertEqual("2026-08-14", case["approval"]["approved_at"])
                self.assertTrue(case["usage"]["not_a_copy_template"])
                self.assertTrue(case["reusable_principles"])
                self.assertTrue(case["non_copyable_elements"])
                self.assertEqual(
                    {"layout", "editable_html", "preview", "review"},
                    set(case["artifacts"]),
                )
                for artifact in case["artifacts"].values():
                    path = ROOT / artifact["path"]
                    self.assertTrue(path.is_file(), path)
                    self.assertEqual(
                        artifact["sha256"],
                        hashlib.sha256(path.read_bytes()).hexdigest(),
                    )

    def test_user_approved_positive_cases_are_queued_for_weekly_maintenance(self):
        self.assertTrue(INBOX.is_file(), INBOX)
        items = json.loads(INBOX.read_text(encoding="utf-8"))
        self.assertEqual(
            {
                "APC-LOST-HUMAN-WORLD-TOC-001",
                "APC-LOST-HUMAN-WORLD-RUNNING-HEADERS-001",
            },
            {item["id"] for item in items},
        )
        self.assertTrue(all(item["state"] == "accepted" for item in items))
        self.assertTrue(all(item["kind"] == "approved-project-case" for item in items))


if __name__ == "__main__":
    unittest.main()
