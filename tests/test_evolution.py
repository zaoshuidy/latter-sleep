import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVAL_SCRIPT = ROOT / "skills" / "evolve-book-skills" / "scripts" / "evaluate_candidate.py"
WEEKLY_SCRIPT = ROOT / "skills" / "evolve-book-skills" / "scripts" / "weekly_maintenance.py"


def load_function(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, name)


def scores(count: int, baseline: float, candidate: float):
    before = [{"case_id": f"C{i:02}", "score": baseline} for i in range(count)]
    after = [{"case_id": f"C{i:02}", "score": candidate} for i in range(count)]
    return before, after


class EvolutionTests(unittest.TestCase):
    def test_fourteen_cases_are_rejected_but_fifteen_can_be_proposed(self):
        evaluate = load_function(EVAL_SCRIPT, "evaluate_candidate")
        before, after = scores(14, 0.5, 0.56)
        self.assertEqual("rejected", evaluate(before, after)["status"])
        before, after = scores(15, 0.5, 0.55)
        self.assertEqual("proposed", evaluate(before, after)["status"])

    def test_nine_percent_rejected_and_ten_percent_allowed(self):
        evaluate = load_function(EVAL_SCRIPT, "evaluate_candidate")
        before, after = scores(15, 0.5, 0.545)
        self.assertEqual("rejected", evaluate(before, after)["status"])
        before, after = scores(15, 0.5, 0.55)
        self.assertEqual("proposed", evaluate(before, after)["status"])

    def test_any_case_regression_rejects_candidate(self):
        evaluate = load_function(EVAL_SCRIPT, "evaluate_candidate")
        before, after = scores(15, 0.5, 0.7)
        after[3]["score"] = 0.49
        result = evaluate(before, after)
        self.assertEqual("rejected", result["status"])
        self.assertEqual(["C03"], result["regressions"])

    def test_human_approval_and_rollback_are_explicit(self):
        evaluate = load_function(EVAL_SCRIPT, "evaluate_candidate")
        before, after = scores(15, 0.5, 0.55)
        proposal = evaluate(before, after)
        self.assertEqual("pending", proposal["human_approval"])
        self.assertEqual("proposed", proposal["status"])
        self.assertTrue(proposal["rollback_path"])

    def test_weekly_maintenance_archives_and_never_deletes(self):
        build_plan = load_function(WEEKLY_SCRIPT, "build_maintenance_plan")
        plan = build_plan([
            {"id": "IMG-1", "kind": "image", "state": "accepted", "path": "incoming/IMG-1.png"},
            {"id": "CASE-OLD", "kind": "case", "state": "expired", "path": "cases/old.json"},
            {"id": "NEG-1", "kind": "negative-case", "state": "negative", "path": "cases/negative.json"},
        ])
        self.assertEqual(["IMG-1"], plan["added"])
        self.assertEqual({"CASE-OLD", "NEG-1"}, {item["id"] for item in plan["archive_moves"]})
        self.assertNotIn("delete", plan)


if __name__ == "__main__":
    unittest.main()
