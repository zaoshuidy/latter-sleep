from __future__ import annotations

import copy
import hashlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from ai.book_component_kb.build import build_library
from ai.book_component_kb.paths import sha256_file
from ai.book_component_kb.retrieve import (
    _score_candidate as real_score_candidate,
    _select_diverse_candidates,
    retrieve,
)
from ai.book_component_kb.validate import validate_library as real_validate_library
from ai.contracts import validate_data


PROJECT_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = Path(__file__).parent / "fixtures" / "component-kb"


def load_fixture(name: str) -> dict[str, object]:
    return json.loads((FIXTURE_ROOT / name).read_text(encoding="utf-8"))


def json_bytes(data: dict[str, object]) -> bytes:
    return json.dumps(
        data,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


class ComponentKnowledgeBaseRetrievalTests(unittest.TestCase):
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
        self.registry.write_text(
            json.dumps(load_fixture("source-registry.json"), ensure_ascii=False, indent=2)
            + "\n",
            encoding="utf-8",
        )
        self.query = {
            "schema_version": "1.0",
            "query_id": "QUERY-COV-0001",
            "component_type": "cover",
            "field_targets": {
                "visual_strategy": ["ILLUSTRATION"],
                "composition": ["ｗｈｉｔｅｓｐａｃｅ"],
                "title_zone": ["TOP"],
                "color": ["墨蓝"],
                "material": ["ILLUSTRATION"],
                "mood": ["安静"],
                "cover_scope": ["front"],
                "book_category": ["memoir"],
            },
            "selection_policy": {"max_results": 5, "diversity": "strict"},
        }

    @staticmethod
    def _png_bytes(seed: str) -> bytes:
        digest = hashlib.sha256(seed.encode("utf-8")).digest()
        pixels = (digest * 21)[: 12 * 18 * 3]
        output = io.BytesIO()
        Image.frombytes("RGB", (12, 18), pixels).save(output, format="PNG")
        return output.getvalue()

    def _add_record(
        self,
        index: int,
        *,
        book_case_id: str | None = None,
        material_visibility: str | None = None,
        material_value: str = "ILLUSTRATION",
        include_category: bool = False,
        mood_tags: list[str] | None = None,
        lifecycle: str = "accumulation",
    ) -> Path:
        record_id = f"COV-CN-{index:04d}"
        asset_name = f"{record_id}.png"
        asset_bytes = self._png_bytes(record_id)
        (self.assets_root / asset_name).write_bytes(asset_bytes)
        record = copy.deepcopy(load_fixture("cover-record.json"))
        record["record_id"] = record_id
        record["identity"]["book_case_id"] = book_case_id or f"BOOK-CN-{index:04d}"
        record["asset"] = {
            "relative_path": f"cover/assets/{asset_name}",
            "sha256": hashlib.sha256(asset_bytes).hexdigest(),
            "mime_type": "image/png",
            "width": 12,
            "height": 18,
        }
        if mood_tags is not None:
            record["retrieval_features"]["mood_tags"] = mood_tags
        record["lifecycle"]["status"] = lifecycle
        observations = record["visual_decomposition"]["observations"]
        if material_visibility is not None:
            observations.append(
                {
                    "aspect": "材质",
                    "value": material_value,
                    "visibility": material_visibility,
                    "confidence": 0.95,
                    "evidence": "纸张表面清晰可见" if material_visibility != "uncertain" else "无法确认纸张",
                    "content_tags": [material_value],
                }
            )
        if include_category:
            observations.append(
                {
                    "aspect": "BOOK_CATEGORY",
                    "value": "MEMOIR",
                    "visibility": "clear",
                    "confidence": 0.9,
                    "evidence": "来源页面明确标注为 memoir",
                    "content_tags": ["memoir"],
                }
            )
        path = self.records_root / f"{record_id}.json"
        path.write_text(
            json.dumps(record, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return path

    def _build(self, count: int = 50, *, first_mood_tags: list[str] | None = None) -> None:
        for index in range(1, count + 1):
            self._add_record(
                index,
                material_visibility=("clear" if index == 1 else "uncertain" if index == 2 else None),
                include_category=index == 1,
                mood_tags=first_mood_tags if index == 1 else None,
            )
        build_library(self.cover_root, self.registry)

    @staticmethod
    def _rewrite_json_in_place(path: Path, data: dict[str, object]) -> None:
        inode = path.stat().st_ino
        with path.open("r+", encoding="utf-8") as file:
            file.seek(0)
            json.dump(data, file, ensure_ascii=False, indent=2)
            file.write("\n")
            file.truncate()
            file.flush()
            os.fsync(file.fileno())
        if path.stat().st_ino != inode:
            raise AssertionError("test mutation must preserve the inode")

    def _tree_hashes(self) -> dict[str, str]:
        return {
            path.relative_to(self.library_root).as_posix(): sha256_file(path)
            for path in sorted(self.library_root.rglob("*"))
            if path.is_file()
        }

    def test_cover_retrieval_returns_five_different_books_with_reasons(self) -> None:
        self._build()

        result = retrieve(self.cover_root, self.registry, self.query, limit=5)

        self.assertEqual("available", result["status"])
        self.assertEqual(5, len(result["candidates"]))
        self.assertEqual(5, len({item["book_case_id"] for item in result["candidates"]}))
        self.assertTrue(
            all(item["field_scores"] and item["match_explanation"] for item in result["candidates"])
        )
        self.assertEqual([], validate_data(result, "book-component-retrieval-result"))

    def test_archived_record_remains_audited_but_is_never_retrieved(self) -> None:
        self._add_record(1, lifecycle="archived")
        for index in range(2, 52):
            self._add_record(index)
        build_result = build_library(self.cover_root, self.registry)

        result = retrieve(self.cover_root, self.registry, self.query, limit=5)

        self.assertEqual("available", build_result["status"])
        self.assertEqual(50, build_result["valid_record_count"])
        self.assertNotIn("COV-CN-0001", [item["record_id"] for item in result["candidates"]])

    def test_weights_are_hand_checkable_and_nfkc_lowered(self) -> None:
        self._build()

        first = retrieve(self.cover_root, self.registry, self.query)["candidates"][0]

        self.assertEqual("COV-CN-0001", first["record_id"])
        self.assertEqual(
            {
                "visual_strategy": 0.20,
                "composition": 0.20,
                "title_zone": 0.15,
                "color": 0.15,
                "material": 0.10,
                "mood": 0.10,
                "cover_scope": 0.05,
                "book_category": 0.05,
            },
            first["field_scores"],
        )
        self.assertEqual(1.0, first["total_score"])
        self.assertIn("material=0.10/0.10 matched [illustration]", first["match_explanation"])

    def test_each_field_compares_only_its_own_target(self) -> None:
        self._build()
        query = copy.deepcopy(self.query)
        query["field_targets"] = {"visual_strategy": ["illustration"]}

        first = retrieve(self.cover_root, self.registry, query)["candidates"][0]

        self.assertEqual(0.20, first["field_scores"]["visual_strategy"])
        self.assertEqual(0.0, first["field_scores"]["material"])
        self.assertEqual(0.20, first["total_score"])

    def test_nfkc_lower_does_not_apply_casefold_sharp_s_equivalence(self) -> None:
        self._build(first_mood_tags=["ß"])
        query = copy.deepcopy(self.query)
        query["field_targets"] = {"mood": ["SS"]}

        first = retrieve(self.cover_root, self.registry, query)["candidates"][0]

        self.assertEqual(0.0, first["field_scores"]["mood"])
        self.assertEqual(0.0, first["total_score"])

    def test_uncertain_and_missing_observations_score_zero_not_negative(self) -> None:
        self._build()

        candidates = retrieve(self.cover_root, self.registry, self.query)["candidates"]
        uncertain = next(item for item in candidates if item["record_id"] == "COV-CN-0002")
        missing = next(item for item in candidates if item["record_id"] == "COV-CN-0003")

        self.assertEqual(0.0, uncertain["field_scores"]["material"])
        self.assertEqual(0.0, uncertain["field_scores"]["book_category"])
        self.assertEqual(0.0, missing["field_scores"]["material"])
        self.assertTrue(all(score >= 0 for score in missing["field_scores"].values()))
        self.assertIn("material=0.00/0.10 no certain indexed observation", uncertain["match_explanation"])

    def test_ties_sort_by_record_id_and_identical_queries_are_byte_equivalent(self) -> None:
        self._build()

        first = retrieve(self.cover_root, self.registry, copy.deepcopy(self.query))
        second = retrieve(self.cover_root, self.registry, copy.deepcopy(self.query))

        self.assertEqual(json_bytes(first), json_bytes(second))
        self.assertEqual(
            ["COV-CN-0002", "COV-CN-0003", "COV-CN-0004", "COV-CN-0005"],
            [item["record_id"] for item in first["candidates"][1:]],
        )

    def test_same_book_deduplication_keeps_only_highest_ranked_record(self) -> None:
        ranked = [
            {"record_id": "COV-CN-0002", "book_case_id": "BOOK-SHARED", "total_score": 0.8},
            {"record_id": "COV-CN-0001", "book_case_id": "BOOK-SHARED", "total_score": 0.8},
            {"record_id": "COV-CN-0003", "book_case_id": "BOOK-OTHER", "total_score": 0.7},
        ]

        selected = _select_diverse_candidates(ranked, limit=2)

        self.assertEqual(["COV-CN-0001", "COV-CN-0003"], [item["record_id"] for item in selected])

    def test_retrieval_never_repeats_to_fill_four_book_shortage(self) -> None:
        self._build(count=4)

        with self.assertRaisesRegex(ValueError, "five different books.*found 4"):
            retrieve(self.cover_root, self.registry, self.query, limit=5)

    def test_building_library_with_enough_for_limit_is_still_rejected(self) -> None:
        self._build(count=6)

        with self.assertRaisesRegex(ValueError, "must be available.*building"):
            retrieve(self.cover_root, self.registry, self.query, limit=5)

    def test_invalid_library_is_rejected_instead_of_reading_tampered_index(self) -> None:
        self._build()
        index_path = self.cover_root / "retrieval-index.json"
        index = json.loads(index_path.read_text(encoding="utf-8"))
        index["component"] = "toc"
        index_path.write_text(json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "component library is invalid"):
            retrieve(self.cover_root, self.registry, self.query)

    def test_record_changed_in_place_after_validator_is_rejected_by_manifest_hash(self) -> None:
        self._build()
        record_path = self.records_root / "COV-CN-0001.json"

        def validate_then_mutate(*args: object, **kwargs: object) -> dict[str, object]:
            report = real_validate_library(*args, **kwargs)
            record = json.loads(record_path.read_text(encoding="utf-8"))
            record["component_profile"]["cover_scope"] = "full-wrap"
            self._rewrite_json_in_place(record_path, record)
            return report

        with patch(
            "ai.book_component_kb.retrieve.validate_library",
            side_effect=validate_then_mutate,
        ):
            with self.assertRaisesRegex(ValueError, "record hash mismatch"):
                retrieve(self.cover_root, self.registry, self.query)

    def test_index_changed_in_place_after_validator_is_rejected_by_manifest_hash(self) -> None:
        self._build()
        index_path = self.cover_root / "retrieval-index.json"

        def validate_then_mutate(*args: object, **kwargs: object) -> dict[str, object]:
            report = real_validate_library(*args, **kwargs)
            index = json.loads(index_path.read_text(encoding="utf-8"))
            index["entries"][0]["color_tags"] = ["tampered"]
            self._rewrite_json_in_place(index_path, index)
            return report

        with patch(
            "ai.book_component_kb.retrieve.validate_library",
            side_effect=validate_then_mutate,
        ):
            with self.assertRaisesRegex(ValueError, "retrieval-index hash mismatch"):
                retrieve(self.cover_root, self.registry, self.query)

    def test_manifest_changed_after_validator_must_still_be_available_and_closed(self) -> None:
        self._build()
        manifest_path = self.cover_root / "manifest.json"

        def validate_then_mutate(*args: object, **kwargs: object) -> dict[str, object]:
            report = real_validate_library(*args, **kwargs)
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["status"] = "building"
            self._rewrite_json_in_place(manifest_path, manifest)
            return report

        with patch(
            "ai.book_component_kb.retrieve.validate_library",
            side_effect=validate_then_mutate,
        ):
            with self.assertRaisesRegex(ValueError, "manifest snapshot"):
                retrieve(self.cover_root, self.registry, self.query)

    def test_manifest_bytes_changed_during_scoring_are_rejected(self) -> None:
        self._build()
        manifest_path = self.cover_root / "manifest.json"
        mutated = False

        def score_then_mutate(*args: object, **kwargs: object) -> dict[str, object]:
            nonlocal mutated
            if not mutated:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                manifest["valid_record_count"] = 51
                self._rewrite_json_in_place(manifest_path, manifest)
                mutated = True
            return real_score_candidate(*args, **kwargs)

        with patch(
            "ai.book_component_kb.retrieve._score_candidate",
            side_effect=score_then_mutate,
        ):
            with self.assertRaisesRegex(ValueError, "manifest changed during retrieval"):
                retrieve(self.cover_root, self.registry, self.query)

    def test_query_schema_is_checked_before_library_paths(self) -> None:
        malformed = copy.deepcopy(self.query)
        del malformed["selection_policy"]

        with self.assertRaisesRegex(ValueError, "query schema"):
            retrieve(Path("/does/not/exist"), Path("/also/missing.json"), malformed)

    def test_cross_component_query_is_rejected(self) -> None:
        query = copy.deepcopy(self.query)
        query["component_type"] = "toc"

        with self.assertRaisesRegex(ValueError, "cover retrieval only"):
            retrieve(self.cover_root, self.registry, query)

    def test_cross_component_record_in_cover_root_is_rejected_not_filtered(self) -> None:
        self._build()
        record = copy.deepcopy(load_fixture("cover-record.json"))
        record["record_id"] = "TOC-CN-0001"
        record["component_type"] = "toc"
        record["identity"]["book_case_id"] = "BOOK-CN-0051"
        record["component_profile"] = {
            "layout_system": "two-column",
            "entry_hierarchy": "chapter and section",
            "navigation_style": "page-number led",
        }
        asset_bytes = self._png_bytes("toc")
        (self.assets_root / "TOC-CN-0001.png").write_bytes(asset_bytes)
        record["asset"] = {
            "relative_path": "cover/assets/TOC-CN-0001.png",
            "sha256": hashlib.sha256(asset_bytes).hexdigest(),
            "mime_type": "image/png",
            "width": 12,
            "height": 18,
        }
        (self.records_root / "TOC-CN-0001.json").write_text(
            json.dumps(record, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

        with self.assertRaisesRegex(ValueError, "component library is invalid"):
            retrieve(self.cover_root, self.registry, self.query)

    def test_retrieval_does_not_write_library(self) -> None:
        self._build()
        before = self._tree_hashes()

        retrieve(self.cover_root, self.registry, self.query)

        self.assertEqual(before, self._tree_hashes())

    def test_cli_requires_explicit_paths_query_and_limit_and_prints_json(self) -> None:
        self._build()
        query_path = Path(self.temp_dir.name) / "query.json"
        query_path.write_text(json.dumps(self.query, ensure_ascii=False) + "\n", encoding="utf-8")
        script = PROJECT_ROOT / "scripts" / "book_component_kb" / "retrieve_references.py"

        completed = subprocess.run(
            [
                sys.executable,
                str(script),
                "--component-root",
                str(self.cover_root),
                "--registry",
                str(self.registry),
                "--query",
                str(query_path),
                "--limit",
                "5",
            ],
            cwd=PROJECT_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(0, completed.returncode, completed.stderr)
        output = json.loads(completed.stdout)
        self.assertEqual([], validate_data(output, "book-component-retrieval-result"))
        self.assertEqual(
            retrieve(self.cover_root, self.registry, self.query),
            output,
        )


if __name__ == "__main__":
    unittest.main()
