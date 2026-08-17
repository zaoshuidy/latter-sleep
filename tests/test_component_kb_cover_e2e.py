from __future__ import annotations

import json
import unittest
from pathlib import Path

from ai.book_component_kb.prompts import compile_component_prompt, validate_selection
from ai.contracts import validate_data


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_ROOT = PROJECT_ROOT / "examples" / "component-kb-cover-demo"
PROJECT_PATH = EXAMPLE_ROOT / "project.json"
QUERY_PATH = EXAMPLE_ROOT / "query.json"
RETRIEVAL_PATH = EXAMPLE_ROOT / "retrieval-result.json"
SELECTION_PATHS = {
    "A": EXAMPLE_ROOT / "reference-selection-A.json",
    "B": EXAMPLE_ROOT / "reference-selection-B.json",
}
PROMPT_PATHS = {
    "A": EXAMPLE_ROOT / "prompts" / "cover-direction-A.json",
    "B": EXAMPLE_ROOT / "prompts" / "cover-direction-B.json",
}
GENOME_PATHS = {
    direction: EXAMPLE_ROOT / "compiler-inputs" / f"direction-{direction}-genome.json"
    for direction in ("A", "B")
}
OUTPUT_SPEC_PATHS = {
    direction: EXAMPLE_ROOT / "compiler-inputs" / f"direction-{direction}-output-spec.json"
    for direction in ("A", "B")
}


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


class CoverComponentExampleTests(unittest.TestCase):
    def test_real_retrieval_stage_returns_five_different_books(self) -> None:
        self.assertTrue(RETRIEVAL_PATH.is_file(), "missing real retrieval-result.json")
        self.assertTrue(PROJECT_PATH.is_file(), "missing real project.json")
        self.assertTrue(QUERY_PATH.is_file(), "missing real query.json")

        project = load_json(PROJECT_PATH)
        query = load_json(QUERY_PATH)
        retrieval = load_json(RETRIEVAL_PATH)

        self.assertEqual([], validate_data(project, "project-config"))
        self.assertEqual([], validate_data(query, "book-component-retrieval-query"))
        self.assertEqual([], validate_data(retrieval, "book-component-retrieval-result"))
        self.assertEqual("四时来信", project["title"])
        self.assertIn("第一章 春归", project["tags"])
        self.assertEqual(query["query_id"], retrieval["query_id"])
        self.assertEqual("available", retrieval["status"])
        candidates = retrieval["candidates"]
        self.assertEqual(5, len(candidates))
        self.assertEqual(5, len({item["book_case_id"] for item in candidates}))

    def test_human_approved_field_mappings_are_exact_and_retrieved(self) -> None:
        retrieval = load_json(RETRIEVAL_PATH)
        expected_mappings = {
            "A": {
                "COV-CN-0031": ["composition", "title_zone", "color"],
                "COV-CN-0036": ["visual_strategy", "composition", "title_zone"],
                "COV-CN-0047": ["composition", "title_zone", "color"],
            },
            "B": {
                "COV-CN-0004": ["composition", "color", "title_zone"],
                "COV-CN-0005": ["visual_strategy", "composition", "color"],
            },
        }

        for direction, path in SELECTION_PATHS.items():
            self.assertTrue(path.is_file(), f"missing approved direction {direction}")
            selection = load_json(path)
            self.assertIsNone(validate_selection(selection, retrieval))
            actual = {
                item["record_id"]: item["include_fields"]
                for item in selection["selected_references"]
            }
            self.assertEqual(expected_mappings[direction], actual)

    def test_approved_mappings_compile_two_text_free_cover_prompts(self) -> None:
        project = load_json(PROJECT_PATH)
        retrieval = load_json(RETRIEVAL_PATH)
        retrieved_ids = {item["record_id"] for item in retrieval["candidates"]}
        for path in (*SELECTION_PATHS.values(), *PROMPT_PATHS.values()):
            self.assertTrue(path.is_file(), f"missing approved artifact: {path.name}")
        selections = {key: load_json(path) for key, path in SELECTION_PATHS.items()}

        for selection in selections.values():
            self.assertEqual(
                [], validate_data(selection, "book-component-reference-selection")
            )
            selected = selection["selected_references"]
            self.assertIn(len(selected), (2, 3))
            self.assertTrue({item["record_id"] for item in selected} <= retrieved_ids)

        prompts = {key: load_json(path) for key, path in PROMPT_PATHS.items()}
        for direction, prompt in prompts.items():
            recompiled = compile_component_prompt(
                project,
                load_json(GENOME_PATHS[direction]),
                selections[direction],
                load_json(OUTPUT_SPEC_PATHS[direction]),
            )
            self.assertEqual(recompiled, prompt)
            self.assertEqual([], validate_data(prompt, "book-component-prompt"))
            self.assertNotIn(project["title"], prompt["background_prompt"])
            self.assertEqual("none", prompt["generation_constraints"]["readable_text"])
            self.assertEqual(
                {
                    "title": "四时来信",
                    "author": "待确认（可编辑文字层）",
                    "studio_mark": "待确认（可编辑文字层）",
                },
                prompt["editable_text_overlay"],
            )
            self.assertNotIn("待确认（可编辑文字层）", prompt["background_prompt"])

        self.assertEqual(
            prompts["A"]["compiled_blocks"]["PROJECT_TRUTH"],
            prompts["B"]["compiled_blocks"]["PROJECT_TRUTH"],
        )


if __name__ == "__main__":
    unittest.main()
