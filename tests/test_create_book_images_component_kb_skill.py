from __future__ import annotations

import hashlib
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from ai.contracts import validate_data
from ai.book_component_kb.paths import read_image_metadata, sha256_file
import ai.book_component_kb.review as review_module


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "skills" / "create-book-images"
SKILL_PATH = SKILL_ROOT / "SKILL.md"
PROTOCOL_PATH = SKILL_ROOT / "references" / "component-prompt-pipeline.md"
BASELINE = (
    ROOT
    / "tests"
    / "skill-behavior"
    / "create-book-images"
    / "component-kb-baseline.md"
)
WITH_SKILL = (
    ROOT
    / "tests"
    / "skill-behavior"
    / "create-book-images"
    / "component-kb-with-skill.md"
)
EXAMPLE = ROOT / "examples" / "component-kb-cover-demo"
SELECTION = EXAMPLE / "reference-selection-A.json"
PROJECT = EXAMPLE / "project.json"
GENOME = EXAMPLE / "compiler-inputs" / "direction-A-genome.json"
OUTPUT_SPEC = EXAMPLE / "compiler-inputs" / "direction-A-output-spec.json"
COMMITTED_PROMPT = EXAMPLE / "prompts" / "cover-direction-A.json"
SOURCE_IMAGE = (
    ROOT
    / "knowledge"
    / "book-component-libraries"
    / "cover"
    / "assets"
    / "COV-CN-0004.jpg"
)
LIBRARY_MANIFEST = (
    ROOT / "knowledge" / "book-component-libraries" / "cover" / "manifest.json"
)
CHECK_NAMES = (
    "no_unwanted_text",
    "safe_zones_clear",
    "genome_consistent",
    "reference_transformed",
    "print_crop_valid",
    "truthfulness_valid",
    "provenance_complete",
)


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tree_sha(path: Path) -> str:
    digest = hashlib.sha256()
    for item in sorted(candidate for candidate in path.rglob("*") if candidate.is_file()):
        digest.update(item.relative_to(path).as_posix().encode("utf-8"))
        digest.update(item.read_bytes())
    return digest.hexdigest()


def review_record(image: Path, prompt: dict, *, status: str) -> dict:
    metadata = read_image_metadata(image)
    result = {
        "schema_version": "1.0",
        "review_id": "REVIEW-COV-TASK17-0001",
        "prompt_id": prompt["prompt_id"],
        "component_type": prompt["component_type"],
        "image": {
            "relative_path": "generated/COVER-TASK17-V001.jpg",
            "sha256": sha256_file(image),
            "mime_type": metadata["mime_type"],
        },
        "observations": [
            {
                "aspect": "无字底图",
                "value": "测试资产用于验证 review/promotion sidecar 边界",
                "visibility": "clear",
                "confidence": 1.0,
                "evidence": "真实文件字节、MIME、尺寸和 SHA 已读取",
                "content_tags": ["测试资产", "sidecar"],
            }
        ],
        "checks": {name: True for name in CHECK_NAMES},
        "status": status,
    }
    if status == "selected":
        result["human_selection"] = selected_evidence(image)
    return result


def selected_evidence(image: Path, version: str = "V001") -> dict:
    # This helper is used only by the generic Task 7 CLI compatibility tests.
    # Project-level Task 17 success fixtures always hash a real approval file.
    return {
        "decision": "selected",
        "approval_id": "APPROVAL-T17-0001",
        "approved_by": "项目维护人",
        "selected_version": version,
        "selected_image_sha256": sha256_file(image),
        "approval_artifact_sha256": hashlib.sha256(
            b"generic-cli-schema-shape-only"
        ).hexdigest(),
    }


class CreateBookImagesComponentPipelineTests(unittest.TestCase):
    def test_cover_integrated_typography_uses_only_the_minimum_stable_gate(self) -> None:
        skill = SKILL_PATH.read_text(encoding="utf-8")
        protocol = PROTOCOL_PATH.read_text(encoding="utf-8")
        cover_contract = (
            SKILL_ROOT / "references" / "cover-prompt-contract.md"
        ).read_text(encoding="utf-8")
        combined = "\n".join((skill, protocol, cover_contract))
        for required in (
            "integrated-typography",
            "exact-project-text",
            "integrated_text_exact",
            "no_extra_text",
            "typography_usable",
            "machine_identifiers_absent",
            "ISBN、条码、二维码、定价、CIP",
            "可编辑文字层",
        ):
            with self.subTest(required=required):
                self.assertIn(required, combined)
        self.assertIn("任一失败", combined)
        self.assertIn("回退", combined)

    def test_fresh_green_stays_at_the_same_fail_closed_pressure_gate(self) -> None:
        behavior = WITH_SKILL.read_text(encoding="utf-8")
        self.assertEqual(
            "6feac8ca9a977936bbd68406b1be11caac1e51d68c6b771e6adbbb1a61b0cd20",
            file_sha(WITH_SKILL),
        )
        for pressure in ("口头通过", "最美的书风格", "四时来信", "林舟", "纸船工作室"):
            self.assertIn(pressure, behavior)
        for gate in ("fail closed", "不会调用 `imagegen`", "status=approved", "schema 有效"):
            self.assertIn(gate, behavior)
        self.assertNotIn("imagegen__imagegen", behavior)
        self.assertNotIn('"status": "selected"', behavior)
        self.assertNotIn('"status": "proposed"', behavior)

    def test_generation_bundle_preflight_rejects_missing_mismatch_tamper_and_overlay_leak(
        self,
    ) -> None:
        from tests.test_project_image_evidence_chain import ProjectBundleFixture

        preflight = getattr(review_module, "validate_generation_bundle", None)
        self.assertTrue(callable(preflight), "missing validate_generation_bundle")
        with tempfile.TemporaryDirectory() as directory:
            fixture = ProjectBundleFixture(Path(directory))
            authorization = fixture.read("generation_authorization")
            authorization["output_path"] = "generated/FUTURE-COVER-V001.jpg"
            fixture.paths["generation_authorization"].write_text(
                json.dumps(authorization, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            paths = review_module.ProjectGenerationEvidencePaths(
                project_config=fixture.paths["project_config"],
                genome=fixture.paths["genome"],
                selection=fixture.paths["selection"],
                retrieval_result=fixture.paths["retrieval_result"],
                output_spec=fixture.paths["output_spec"],
                prompt=fixture.paths["prompt"],
                generation_payload=fixture.paths["generation_payload"],
                generation_authorization=fixture.paths["generation_authorization"],
            )
            with preflight(fixture.root, paths) as execution:
                self.assertEqual(
                    fixture.read("generation_payload")["background_prompt"],
                    execution.background_prompt,
                )
                self.assertEqual((), execution.reference_materials)
            prompt = fixture.read("prompt")
            prompt["background_prompt"] += "\ntampered"
            fixture.paths["prompt"].write_text(
                json.dumps(prompt, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            with self.assertRaises(ValueError):
                preflight(fixture.root, paths)

    def test_actual_skill_path_resolves_suite_root_from_external_cwd(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run(
                ["bash", "-c", 'cd -P "$(dirname "$SKILL_FILE")/../.." && pwd'],
                cwd=directory,
                env={**os.environ, "SKILL_FILE": str(SKILL_PATH.resolve())},
                text=True,
                capture_output=True,
                check=False,
            )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(ROOT.resolve(), Path(result.stdout.strip()))

    def test_project_bound_review_and_promotion_use_real_project_artifacts(self) -> None:
        from tests.test_project_image_evidence_chain import ProjectBundleFixture

        knowledge_root = ROOT / "knowledge" / "book-component-libraries"
        knowledge_before = tree_sha(knowledge_root)
        with tempfile.TemporaryDirectory() as directory:
            fixture = ProjectBundleFixture(Path(directory))
            review_path = fixture.root / "reviews" / "selected-review.json"
            reviewed = review_module.review_project_image(
                fixture.root,
                fixture.evidence_paths(),
                fixture.selected_review(),
                output_sidecar=review_path,
            )
            proposal_path = fixture.root / "promotions" / "pending-proposal.json"
            proposal = review_module.prepare_project_promotion(
                fixture.root,
                fixture.evidence_paths(),
                review_path,
                "cover",
                output_sidecar=proposal_path,
            )
            self.assertEqual("selected", reviewed["status"])
            self.assertEqual("pending", proposal["human_approval"])
            self.assertTrue(review_path.is_file())
            self.assertTrue(proposal_path.is_file())
            self.assertEqual(reviewed, json.loads(review_path.read_text(encoding="utf-8")))
            self.assertEqual(proposal, json.loads(proposal_path.read_text(encoding="utf-8")))
        self.assertEqual(knowledge_before, tree_sha(knowledge_root))

    def test_skill_routes_approved_component_inputs_to_the_pipeline_reference(self) -> None:
        skill = SKILL_PATH.read_text(encoding="utf-8")
        self.assertIn("references/component-prompt-pipeline.md", skill)
        self.assertIn("approved selection", skill)
        self.assertIn("book-component-prompt", skill)

    def test_protocol_defines_fail_closed_generation_review_and_pending_promotion(self) -> None:
        protocol = PROTOCOL_PATH.read_text(encoding="utf-8")
        required = (
            "SKILL_FILE",
            'cd -P "$(dirname "$SKILL_FILE")/../.."',
            "approved",
            "selection_id",
            "component_type",
            "真实 `record_id`",
            "fail closed",
            "compile_component_prompt",
            "background_prompt",
            "editable_text_overlay",
            "明确授权",
            "费用",
            "SHA-256",
            "MIME",
            "dimensions",
            "version",
            "status=draft",
            "review_project_image",
            "七项",
            "selected",
            "机器不得自行",
            "prepare_project_promotion",
            "proposed",
            "pending",
            "accumulation",
            "rejected",
            "archived",
            "不得写入组件知识库",
        )
        for value in required:
            with self.subTest(value=value):
                self.assertIn(value, protocol)

    def test_external_cwd_recompiles_the_formal_prompt_byte_equivalently(self) -> None:
        baseline_before = file_sha(BASELINE)
        selection = json.loads(SELECTION.read_text(encoding="utf-8"))
        self.assertEqual("approved", selection["status"])
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "compiled-prompt.json"
            result = subprocess.run(
                [
                    str(ROOT / ".venv" / "bin" / "python"),
                    str(ROOT / "scripts" / "book_component_kb" / "compile_prompt.py"),
                    "--project",
                    str(PROJECT),
                    "--genome",
                    str(GENOME),
                    "--selection",
                    str(SELECTION),
                    "--output-spec",
                    str(OUTPUT_SPEC),
                    "--output",
                    str(output),
                ],
                cwd=directory,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(0, result.returncode, result.stderr)
            prompt = json.loads(output.read_text(encoding="utf-8"))

        self.assertEqual(
            json.loads(COMMITTED_PROMPT.read_text(encoding="utf-8")), prompt
        )
        self.assertEqual([], validate_data(prompt, "book-component-prompt"))
        self.assertEqual(selection["selection_id"], prompt["selection_id"])
        self.assertEqual(selection["component_type"], prompt["component_type"])
        for reference in selection["selected_references"]:
            self.assertIn(
                reference["record_id"],
                prompt["compiled_blocks"]["REFERENCE_TRANSFERS"],
            )
        project = json.loads(PROJECT.read_text(encoding="utf-8"))
        self.assertNotIn(project["title"], prompt["background_prompt"])
        self.assertEqual(project["title"], prompt["editable_text_overlay"]["title"])
        self.assertEqual(baseline_before, file_sha(BASELINE))

    def test_real_review_and_promotion_clis_write_only_project_sidecars(self) -> None:
        prompt = json.loads(COMMITTED_PROMPT.read_text(encoding="utf-8"))
        metadata = read_image_metadata(SOURCE_IMAGE)
        project_version = {
            "image_id": "COVER-TASK17",
            "prompt_id": prompt["prompt_id"],
            "selection_id": prompt["selection_id"],
            "component_type": prompt["component_type"],
            "record_ids": [
                reference["record_id"]
                for reference in json.loads(SELECTION.read_text(encoding="utf-8"))[
                    "selected_references"
                ]
            ],
            "output_path": str(SOURCE_IMAGE.resolve()),
            "sha256": sha256_file(SOURCE_IMAGE),
            "mime_type": metadata["mime_type"],
            "dimensions": {"width": metadata["width"], "height": metadata["height"]},
            "version": "V001",
            "status": "draft",
        }
        project_manifest = {
            "version": "1.0",
            "project_id": json.loads(PROJECT.read_text(encoding="utf-8"))["project_id"],
            "images": [
                {
                    "image_id": project_version["image_id"],
                    "image_role": "design",
                    "use": "cover background",
                    "skill": "create-book-images",
                    "prompt_file": "prompts/cover-direction-A.json",
                    "reference_files": project_version["record_ids"],
                    "output_file": project_version["output_path"],
                    "status": "draft",
                }
            ],
        }
        self.assertEqual([], validate_data(project_manifest, "image-manifest"))
        self.assertEqual("draft", project_version["status"])
        self.assertGreater(project_version["dimensions"]["width"], 0)
        self.assertGreater(project_version["dimensions"]["height"], 0)

        library_before = file_sha(LIBRARY_MANIFEST)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            review_input = root / "review-input.json"
            review_output = root / "review-output.json"
            proposal_output = root / "promotion-proposal.json"
            review_input.write_text(
                json.dumps(
                    review_record(SOURCE_IMAGE, prompt, status="selected"),
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            review_result = subprocess.run(
                [
                    str(ROOT / ".venv" / "bin" / "python"),
                    str(ROOT / "scripts" / "book_component_kb" / "review_image.py"),
                    "--input",
                    str(review_input),
                    "--output",
                    str(review_output),
                ],
                cwd=directory,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(0, review_result.returncode, review_result.stderr)
            promotion_result = subprocess.run(
                [
                    str(ROOT / ".venv" / "bin" / "python"),
                    str(ROOT / "scripts" / "book_component_kb" / "promote_image.py"),
                    "--review",
                    str(review_output),
                    "--source-image",
                    str(SOURCE_IMAGE),
                    "--target-component",
                    "cover",
                    "--output",
                    str(proposal_output),
                ],
                cwd=directory,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(0, promotion_result.returncode, promotion_result.stderr)
            proposal = json.loads(proposal_output.read_text(encoding="utf-8"))
            self.assertEqual(
                {"status": "proposed", "human_approval": "pending", "target_lifecycle": "accumulation"},
                {
                    key: proposal[key]
                    for key in ("status", "human_approval", "target_lifecycle")
                },
            )
            self.assertEqual([], validate_data(proposal, "book-component-kb-promotion"))
            self.assertEqual(
                ["promotion-proposal.json", "review-input.json", "review-output.json"],
                sorted(path.name for path in root.iterdir()),
            )
        self.assertEqual(library_before, file_sha(LIBRARY_MANIFEST))

    def test_unselected_reviews_and_output_aliases_fail_closed(self) -> None:
        prompt = json.loads(COMMITTED_PROMPT.read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for status in ("draft", "rejected", "archived"):
                with self.subTest(status=status):
                    review_path = root / f"review-{status}.json"
                    proposal_path = root / f"proposal-{status}.json"
                    review_path.write_text(
                        json.dumps(
                            review_record(SOURCE_IMAGE, prompt, status=status),
                            ensure_ascii=False,
                        ),
                        encoding="utf-8",
                    )
                    result = subprocess.run(
                        [
                            str(ROOT / ".venv" / "bin" / "python"),
                            str(ROOT / "scripts" / "book_component_kb" / "promote_image.py"),
                            "--review",
                            str(review_path),
                            "--source-image",
                            str(SOURCE_IMAGE),
                            "--target-component",
                            "cover",
                            "--output",
                            str(proposal_path),
                        ],
                        cwd=directory,
                        text=True,
                        capture_output=True,
                        check=False,
                    )
                    self.assertNotEqual(0, result.returncode)
                    self.assertFalse(proposal_path.exists())

            alias_review = root / "alias-review.json"
            alias_review.write_text(
                json.dumps(
                    review_record(SOURCE_IMAGE, prompt, status="selected"),
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            before = alias_review.read_bytes()
            alias_result = subprocess.run(
                [
                    str(ROOT / ".venv" / "bin" / "python"),
                    str(ROOT / "scripts" / "book_component_kb" / "review_image.py"),
                    "--input",
                    str(alias_review),
                    "--output",
                    str(alias_review),
                ],
                cwd=directory,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(0, alias_result.returncode)
            self.assertEqual(before, alias_review.read_bytes())

            incomplete_selected = review_record(
                SOURCE_IMAGE, prompt, status="selected"
            )
            incomplete_selected["checks"]["truthfulness_valid"] = False
            incomplete_path = root / "selected-with-false-check.json"
            incomplete_output = root / "selected-with-false-check-output.json"
            incomplete_path.write_text(
                json.dumps(incomplete_selected, ensure_ascii=False), encoding="utf-8"
            )
            incomplete_result = subprocess.run(
                [
                    str(ROOT / ".venv" / "bin" / "python"),
                    str(ROOT / "scripts" / "book_component_kb" / "review_image.py"),
                    "--input",
                    str(incomplete_path),
                    "--output",
                    str(incomplete_output),
                ],
                cwd=directory,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(0, incomplete_result.returncode)
            self.assertFalse(incomplete_output.exists())


if __name__ == "__main__":
    unittest.main()
