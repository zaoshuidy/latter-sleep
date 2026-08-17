from __future__ import annotations

import copy
import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ai.book_component_kb.paths import read_image_metadata, sha256_file
import ai.book_component_kb.review as review_module
from ai.contracts import validate_data


ROOT = Path(__file__).resolve().parents[1]
EXAMPLE = ROOT / "examples" / "component-kb-cover-demo"
SOURCE_IMAGE = (
    ROOT
    / "knowledge"
    / "book-component-libraries"
    / "cover"
    / "assets"
    / "COV-CN-0004.jpg"
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


def json_bytes(value: dict) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


class ProjectEvidenceSchemaTests(unittest.TestCase):
    def test_selection_and_generation_approval_artifacts_are_closed_and_dated(self) -> None:
        selection_approval = {
            "schema_version": "1.0",
            "approval_id": "SELECT-COVER-T17-0001",
            "approved_by": "项目维护人",
            "decision": "selected",
            "selection_id": "SEL-COV-FOUR-SEASONS-A-0001",
            "prompt_id": "PROMPT-COV-FOUR-SEASONS-A-0001",
            "component_type": "cover",
            "image_id": "COVER-TASK17",
            "selected_version": "V001",
            "selected_image_sha256": "1" * 64,
            "approved_at": "2026-08-12",
        }
        generation_authorization = {
            "schema_version": "1.0",
            "approval_id": "GENERATE-COVER-T17-0001",
            "approved_by": "项目维护人",
            "decision": "approved",
            "selection_id": "SEL-COV-FOUR-SEASONS-A-0001",
            "prompt_id": "PROMPT-COV-FOUR-SEASONS-A-0001",
            "component_type": "cover",
            "selection_sha256": "2" * 64,
            "prompt_sha256": "3" * 64,
            "generation_payload_sha256": "4" * 64,
            "retrieval_result_sha256": "6" * 64,
            "fee_action": "已明确批准本次生成费用动作",
            "output_path": "generated/COVER-TASK17-V001.jpg",
            "referenced_images": [],
            "approved_at": "2026-08-12",
        }
        payload = {"background_prompt": "background only", "referenced_image_paths": []}

        self.assertEqual(
            [],
            validate_data(
                selection_approval, "book-project-image-selection-approval"
            ),
        )
        self.assertEqual(
            [],
            validate_data(
                generation_authorization,
                "book-project-image-generation-authorization",
            ),
        )
        self.assertEqual(
            [], validate_data(payload, "book-project-image-generation-payload")
        )

        invalid_date = {**selection_approval, "approved_at": "2026-13-40"}
        unknown = {**selection_approval, "machine_approved": True}
        self.assertNotEqual(
            [], validate_data(invalid_date, "book-project-image-selection-approval")
        )
        self.assertNotEqual(
            [], validate_data(unknown, "book-project-image-selection-approval")
        )

    def test_version_requires_hashes_for_every_generation_fact_artifact(self) -> None:
        version = {
            "schema_version": "1.0",
            "image_id": "COVER-TASK17",
            "prompt_id": "PROMPT-COV-FOUR-SEASONS-A-0001",
            "selection_id": "SEL-COV-FOUR-SEASONS-A-0001",
            "component_type": "cover",
            "record_ids": ["COV-CN-0031", "COV-CN-0036", "COV-CN-0047"],
            "output_path": "generated/COVER-TASK17-V001.jpg",
            "sha256": "1" * 64,
            "mime_type": "image/jpeg",
            "dimensions": {"width": 10, "height": 20},
            "version": "V001",
            "status": "draft",
            "selection_sha256": "2" * 64,
            "prompt_sha256": "3" * 64,
            "generation_payload_sha256": "4" * 64,
            "generation_authorization_sha256": "5" * 64,
            "retrieval_result_sha256": "6" * 64,
        }
        self.assertEqual([], validate_data(version, "book-project-image-version"))
        for field in (
            "selection_sha256",
            "prompt_sha256",
            "generation_payload_sha256",
            "generation_authorization_sha256",
            "retrieval_result_sha256",
        ):
            with self.subTest(field=field):
                missing = copy.deepcopy(version)
                del missing[field]
                self.assertNotEqual(
                    [], validate_data(missing, "book-project-image-version")
                )


class ProjectBundleFixture:
    def __init__(self, temporary_root: Path) -> None:
        self.root = temporary_root / "book-project"
        for directory in (
            "approvals",
            "generated",
            "inputs",
            "manifests",
            "overlays",
            "payloads",
            "promotions",
            "references",
            "reviews",
            "versions",
        ):
            (self.root / directory).mkdir(parents=True, exist_ok=True)
        source_paths = {
            "project_config": EXAMPLE / "project.json",
            "genome": EXAMPLE / "compiler-inputs" / "direction-A-genome.json",
            "selection": EXAMPLE / "reference-selection-A.json",
            "output_spec": EXAMPLE / "compiler-inputs" / "direction-A-output-spec.json",
            "prompt": EXAMPLE / "prompts" / "cover-direction-A.json",
            "retrieval_result": EXAMPLE / "retrieval-result.json",
        }
        self.paths: dict[str, Path] = {}
        for name, source in source_paths.items():
            target = self.root / "inputs" / f"{name}.json"
            shutil.copyfile(source, target)
            self.paths[name] = target

        self.image = self.root / "generated" / "COVER-TASK17-V001.jpg"
        shutil.copyfile(SOURCE_IMAGE, self.image)
        self.paths["source_image"] = self.image
        prompt = self.read("prompt")
        selection = self.read("selection")

        payload = {
            "background_prompt": prompt["background_prompt"],
            "referenced_image_paths": [],
        }
        self.write("generation_payload", "payloads/generation.json", payload)
        authorization = {
            "schema_version": "1.0",
            "approval_id": "GENERATE-COVER-T17-0001",
            "approved_by": "项目维护人",
            "decision": "approved",
            "selection_id": selection["selection_id"],
            "prompt_id": prompt["prompt_id"],
            "component_type": "cover",
            "selection_sha256": sha256_file(self.paths["selection"]),
            "prompt_sha256": sha256_file(self.paths["prompt"]),
            "generation_payload_sha256": sha256_file(
                self.paths["generation_payload"]
            ),
            "retrieval_result_sha256": sha256_file(
                self.paths["retrieval_result"]
            ),
            "fee_action": "已明确批准本次生成费用动作",
            "output_path": "generated/COVER-TASK17-V001.jpg",
            "referenced_images": [],
            "approved_at": "2026-08-12",
        }
        self.write(
            "generation_authorization",
            "approvals/generation-authorization.json",
            authorization,
        )

        metadata = read_image_metadata(self.image)
        version = {
            "schema_version": "1.0",
            "image_id": "COVER-TASK17",
            "prompt_id": prompt["prompt_id"],
            "selection_id": selection["selection_id"],
            "component_type": "cover",
            "record_ids": [
                reference["record_id"]
                for reference in selection["selected_references"]
            ],
            "output_path": "generated/COVER-TASK17-V001.jpg",
            "sha256": sha256_file(self.image),
            "mime_type": metadata["mime_type"],
            "dimensions": {
                "width": metadata["width"],
                "height": metadata["height"],
            },
            "version": "V001",
            "status": "draft",
            "selection_sha256": sha256_file(self.paths["selection"]),
            "prompt_sha256": sha256_file(self.paths["prompt"]),
            "generation_payload_sha256": sha256_file(
                self.paths["generation_payload"]
            ),
            "generation_authorization_sha256": sha256_file(
                self.paths["generation_authorization"]
            ),
            "retrieval_result_sha256": sha256_file(
                self.paths["retrieval_result"]
            ),
        }
        self.write("version", "versions/COVER-TASK17-V001.json", version)
        selection_approval = {
            "schema_version": "1.0",
            "approval_id": "SELECT-COVER-T17-0001",
            "approved_by": "项目维护人",
            "decision": "selected",
            "selection_id": selection["selection_id"],
            "prompt_id": prompt["prompt_id"],
            "component_type": "cover",
            "image_id": "COVER-TASK17",
            "selected_version": "V001",
            "selected_image_sha256": sha256_file(self.image),
            "approved_at": "2026-08-12",
        }
        self.write(
            "selection_approval",
            "approvals/image-selection-approval.json",
            selection_approval,
        )
        self.overlay = self.root / "overlays" / "component-overlay.json"
        self.overlay.write_bytes(json_bytes(prompt["editable_text_overlay"]))
        self.manifest = self.root / "manifests" / "image-manifest.json"
        self.manifest.write_bytes(
            json_bytes(
                {
                    "version": "1.0",
                    "project_id": "T17-PROJECT",
                    "images": [
                        {
                            "image_id": "COVER-TASK17",
                            "image_role": "design",
                            "use": "cover background",
                            "skill": "create-book-images",
                            "prompt_file": "inputs/prompt.json",
                            "reference_files": version["record_ids"],
                            "output_file": "generated/COVER-TASK17-V001.jpg",
                            "status": "draft",
                        }
                    ],
                }
            )
        )

    def write(self, name: str, relative: str, value: dict) -> None:
        path = self.root / relative
        path.write_bytes(json_bytes(value))
        self.paths[name] = path

    def read(self, name: str) -> dict:
        return json.loads(self.paths[name].read_text(encoding="utf-8"))

    def evidence_paths(self):
        paths_class = getattr(review_module, "ProjectImageEvidencePaths", None)
        if paths_class is None:
            raise AssertionError("missing ProjectImageEvidencePaths")
        return paths_class(
            project_config=self.paths["project_config"],
            genome=self.paths["genome"],
            selection=self.paths["selection"],
            output_spec=self.paths["output_spec"],
            prompt=self.paths["prompt"],
            generation_payload=self.paths["generation_payload"],
            generation_authorization=self.paths["generation_authorization"],
            retrieval_result=self.paths["retrieval_result"],
            version=self.paths["version"],
            selection_approval=self.paths["selection_approval"],
            source_image=self.image,
        )

    def generation_evidence_paths(self):
        return review_module.ProjectGenerationEvidencePaths(
            project_config=self.paths["project_config"],
            genome=self.paths["genome"],
            selection=self.paths["selection"],
            retrieval_result=self.paths["retrieval_result"],
            output_spec=self.paths["output_spec"],
            prompt=self.paths["prompt"],
            generation_payload=self.paths["generation_payload"],
            generation_authorization=self.paths["generation_authorization"],
        )

    def selected_review(self) -> dict:
        prompt = self.read("prompt")
        return {
            "schema_version": "1.0",
            "review_id": "REVIEW-COVER-T17-0001",
            "prompt_id": prompt["prompt_id"],
            "component_type": "cover",
            "image": {
                "relative_path": "generated/COVER-TASK17-V001.jpg",
                "sha256": sha256_file(self.image),
                "mime_type": "image/jpeg",
            },
            "observations": [
                {
                    "aspect": "证据链",
                    "value": "项目内真实文件用于受控链路验收",
                    "visibility": "clear",
                    "confidence": 1.0,
                    "evidence": "真实路径、哈希、MIME、尺寸与批准 artifact",
                    "content_tags": ["测试资产", "审计证据"],
                }
            ],
            "checks": {name: True for name in CHECK_NAMES},
            "status": "selected",
            "human_selection": {
                "decision": "selected",
                "approval_id": "SELECT-COVER-T17-0001",
                "approved_by": "项目维护人",
                "selected_version": "V001",
                "selected_image_sha256": sha256_file(self.image),
                "approval_artifact_sha256": sha256_file(
                    self.paths["selection_approval"]
                ),
            },
        }


class ProjectEvidenceChainTests(unittest.TestCase):
    def test_generation_execution_bundle_holds_authorized_bytes_and_detects_path_change(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = ProjectBundleFixture(Path(directory))
            reference = fixture.root / "references" / "authorized.jpg"
            shutil.copyfile(SOURCE_IMAGE, reference)
            authorized_bytes = reference.read_bytes()
            payload = fixture.read("generation_payload")
            payload["referenced_image_paths"] = ["references/authorized.jpg"]
            fixture.paths["generation_payload"].write_bytes(json_bytes(payload))
            authorization = fixture.read("generation_authorization")
            authorization["output_path"] = "generated/FUTURE-COVER-V001.jpg"
            authorization["generation_payload_sha256"] = sha256_file(
                fixture.paths["generation_payload"]
            )
            authorization["referenced_images"] = [
                {
                    "relative_path": "references/authorized.jpg",
                    "sha256": sha_bytes(authorized_bytes),
                    "mime_type": "image/jpeg",
                }
            ]
            fixture.paths["generation_authorization"].write_bytes(
                json_bytes(authorization)
            )

            with review_module.validate_generation_bundle(
                fixture.root, fixture.generation_evidence_paths()
            ) as execution:
                self.assertEqual(payload["background_prompt"], execution.background_prompt)
                self.assertEqual(1, len(execution.reference_materials))
                material = execution.reference_materials[0]
                self.assertEqual("references/authorized.jpg", material.relative_path)
                self.assertEqual(authorized_bytes, material.content)
                reference.write_bytes(b"changed after authorized preflight")
                self.assertEqual(authorized_bytes, material.content)
                with self.assertRaises(ValueError):
                    execution.verify()

    def test_generation_execution_bundle_accepts_empty_references_and_closes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = ProjectBundleFixture(Path(directory))
            authorization = fixture.read("generation_authorization")
            authorization["output_path"] = "generated/FUTURE-COVER-V001.jpg"
            fixture.paths["generation_authorization"].write_bytes(
                json_bytes(authorization)
            )
            execution = review_module.validate_generation_bundle(
                fixture.root, fixture.generation_evidence_paths()
            )
            with execution as active:
                self.assertEqual((), active.reference_materials)
                active.verify()
            self.assertTrue(execution.closed)

    def test_review_publish_revalidates_evidence_in_atomic_commit_window(self) -> None:
        cases = [
            ("before_link", name)
            for name in (
                "project_config",
                "genome",
                "selection",
                "retrieval_result",
                "output_spec",
                "prompt",
                "generation_payload",
                "generation_authorization",
                "version",
                "selection_approval",
                "source_image",
            )
        ] + [("during_link", "selection")]
        for race_point, artifact_name in cases:
            with self.subTest(
                race_point=race_point, artifact=artifact_name
            ), tempfile.TemporaryDirectory() as directory:
                fixture = ProjectBundleFixture(Path(directory))
                output = (
                    fixture.root
                    / "reviews"
                    / f"{race_point}-{artifact_name}.json"
                )
                artifact_path = fixture.paths[artifact_name]
                changed = artifact_path.read_bytes() + b"\n"
                mutated = False

                if race_point == "before_link":
                    original = review_module._create_temporary_sidecar

                    def race(*args, **kwargs):
                        nonlocal mutated
                        result = original(*args, **kwargs)
                        if not mutated:
                            mutated = True
                            artifact_path.write_bytes(changed)
                        return result

                    target = "_create_temporary_sidecar"
                else:
                    original = review_module.os.link

                    def race(*args, **kwargs):
                        nonlocal mutated
                        result = original(*args, **kwargs)
                        if not mutated:
                            mutated = True
                            artifact_path.write_bytes(changed)
                        return result

                    target = "os.link"

                patch_target = (
                    patch.object(review_module, target, side_effect=race)
                    if race_point == "before_link"
                    else patch.object(review_module.os, "link", side_effect=race)
                )
                with patch_target:
                    with self.assertRaises(ValueError):
                        review_module.review_project_image(
                            fixture.root,
                            fixture.evidence_paths(),
                            fixture.selected_review(),
                            output_sidecar=output,
                        )
                self.assertFalse(output.exists())

    def test_promotion_review_rejects_external_hardlink(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = ProjectBundleFixture(Path(directory))
            review_path = fixture.root / "reviews" / "selected.json"
            review_module.review_project_image(
                fixture.root,
                fixture.evidence_paths(),
                fixture.selected_review(),
                output_sidecar=review_path,
            )
            outside = Path(directory) / "outside-selected.json"
            outside.write_bytes(review_path.read_bytes())
            review_path.unlink()
            review_path.hardlink_to(outside)
            output = fixture.root / "promotions" / "hardlink-review.json"
            with self.assertRaises(ValueError):
                review_module.prepare_project_promotion(
                    fixture.root,
                    fixture.evidence_paths(),
                    review_path,
                    "cover",
                    output_sidecar=output,
                )
            self.assertFalse(output.exists())

    def test_promotion_review_change_during_publish_rolls_back_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = ProjectBundleFixture(Path(directory))
            review_path = fixture.root / "reviews" / "selected.json"
            review_module.review_project_image(
                fixture.root,
                fixture.evidence_paths(),
                fixture.selected_review(),
                output_sidecar=review_path,
            )
            rejected = json.loads(review_path.read_text(encoding="utf-8"))
            rejected["status"] = "rejected"
            output = fixture.root / "promotions" / "mutated-review.json"
            original_link = review_module.os.link
            mutated = False

            def racing_link(*args, **kwargs):
                nonlocal mutated
                result = original_link(*args, **kwargs)
                if not mutated:
                    mutated = True
                    review_path.write_bytes(json_bytes(rejected))
                return result

            with patch.object(review_module.os, "link", side_effect=racing_link):
                with self.assertRaises(ValueError):
                    review_module.prepare_project_promotion(
                        fixture.root,
                        fixture.evidence_paths(),
                        review_path,
                        "cover",
                        output_sidecar=output,
                    )
            self.assertFalse(output.exists())

    def test_pre_generation_entry_reads_real_artifacts_and_rejects_forged_hashes_or_output_links(self) -> None:
        preflight = getattr(review_module, "validate_project_generation_bundle", None)
        self.assertTrue(callable(preflight), "missing path-based generation preflight")
        with tempfile.TemporaryDirectory() as directory:
            fixture = ProjectBundleFixture(Path(directory))
            generation_paths_class = getattr(
                review_module, "ProjectGenerationEvidencePaths", None
            )
            self.assertIsNotNone(generation_paths_class)
            paths = generation_paths_class(
                project_config=fixture.paths["project_config"],
                genome=fixture.paths["genome"],
                selection=fixture.paths["selection"],
                retrieval_result=fixture.paths["retrieval_result"],
                output_spec=fixture.paths["output_spec"],
                prompt=fixture.paths["prompt"],
                generation_payload=fixture.paths["generation_payload"],
                generation_authorization=fixture.paths["generation_authorization"],
            )
            authorization = fixture.read("generation_authorization")
            authorization["output_path"] = "generated/FUTURE-COVER-V001.jpg"
            fixture.paths["generation_authorization"].write_bytes(
                json_bytes(authorization)
            )
            with preflight(fixture.root, paths) as execution:
                self.assertEqual(
                    fixture.read("generation_payload")["background_prompt"],
                    execution.background_prompt,
                )
                self.assertEqual((), execution.reference_materials)

            authorization = fixture.read("generation_authorization")
            authorization["selection_sha256"] = "0" * 64
            fixture.paths["generation_authorization"].write_bytes(json_bytes(authorization))
            with self.assertRaises(ValueError):
                preflight(fixture.root, paths)

        with tempfile.TemporaryDirectory() as directory:
            fixture = ProjectBundleFixture(Path(directory))
            authorization = fixture.read("generation_authorization")
            authorization["output_path"] = "generated/FUTURE-COVER-V001.jpg"
            fixture.paths["generation_authorization"].write_bytes(
                json_bytes(authorization)
            )
            paths = generation_paths_class(
                project_config=fixture.paths["project_config"],
                genome=fixture.paths["genome"],
                selection=fixture.paths["selection"],
                retrieval_result=fixture.paths["retrieval_result"],
                output_spec=fixture.paths["output_spec"],
                prompt=fixture.paths["prompt"],
                generation_payload=fixture.paths["generation_payload"],
                generation_authorization=fixture.paths["generation_authorization"],
            )
            original_stat = review_module.os.stat
            moved = False

            def racing_stat(path, *args, **kwargs):
                nonlocal moved
                if path == "FUTURE-COVER-V001.jpg" and not moved:
                    moved = True
                    (fixture.root / "generated").rename(
                        Path(directory) / "escaped-generated-race"
                    )
                    (fixture.root / "generated").mkdir()
                return original_stat(path, *args, **kwargs)

            with patch.object(review_module.os, "stat", side_effect=racing_stat):
                with self.assertRaises(ValueError):
                    preflight(fixture.root, paths)

        with tempfile.TemporaryDirectory() as directory:
            fixture = ProjectBundleFixture(Path(directory))
            generated = fixture.root / "generated"
            escaped = Path(directory) / "escaped-generated"
            generated.rename(escaped)
            generated.symlink_to(escaped, target_is_directory=True)
            paths = generation_paths_class(
                project_config=fixture.paths["project_config"],
                genome=fixture.paths["genome"],
                selection=fixture.paths["selection"],
                retrieval_result=fixture.paths["retrieval_result"],
                output_spec=fixture.paths["output_spec"],
                prompt=fixture.paths["prompt"],
                generation_payload=fixture.paths["generation_payload"],
                generation_authorization=fixture.paths["generation_authorization"],
            )
            with self.assertRaises(ValueError):
                preflight(fixture.root, paths)

    def test_all_project_inputs_references_and_source_reject_hardlinks(self) -> None:
        artifact_names = (
            "project_config",
            "genome",
            "selection",
            "retrieval_result",
            "output_spec",
            "prompt",
            "generation_payload",
            "generation_authorization",
            "version",
            "selection_approval",
        )
        for name in artifact_names:
            with self.subTest(artifact=name), tempfile.TemporaryDirectory() as directory:
                fixture = ProjectBundleFixture(Path(directory))
                target = fixture.paths[name]
                outside = Path(directory) / f"outside-{name}.json"
                outside.write_bytes(target.read_bytes())
                target.unlink()
                target.hardlink_to(outside)
                self.assertTrue(target.samefile(outside))
                with self.assertRaises(ValueError):
                    review_module.review_project_image(
                        fixture.root,
                        fixture.evidence_paths(),
                        fixture.selected_review(),
                    )

        with tempfile.TemporaryDirectory() as directory:
            fixture = ProjectBundleFixture(Path(directory))
            fixture.image.unlink()
            fixture.image.hardlink_to(SOURCE_IMAGE)
            with self.assertRaises(ValueError):
                review_module.review_project_image(
                    fixture.root, fixture.evidence_paths(), fixture.selected_review()
                )

        with tempfile.TemporaryDirectory() as directory:
            fixture = ProjectBundleFixture(Path(directory))
            reference = fixture.root / "references" / "hardlinked.jpg"
            reference.hardlink_to(SOURCE_IMAGE)
            payload = fixture.read("generation_payload")
            payload["referenced_image_paths"] = ["references/hardlinked.jpg"]
            fixture.paths["generation_payload"].write_bytes(json_bytes(payload))
            authorization = fixture.read("generation_authorization")
            authorization["generation_payload_sha256"] = sha256_file(
                fixture.paths["generation_payload"]
            )
            authorization["referenced_images"] = [
                {
                    "relative_path": "references/hardlinked.jpg",
                    "sha256": sha256_file(reference),
                    "mime_type": "image/jpeg",
                }
            ]
            fixture.paths["generation_authorization"].write_bytes(
                json_bytes(authorization)
            )
            version = fixture.read("version")
            version["generation_payload_sha256"] = sha256_file(
                fixture.paths["generation_payload"]
            )
            version["generation_authorization_sha256"] = sha256_file(
                fixture.paths["generation_authorization"]
            )
            fixture.paths["version"].write_bytes(json_bytes(version))
            with self.assertRaises(ValueError):
                review_module.review_project_image(
                    fixture.root, fixture.evidence_paths(), fixture.selected_review()
                )

    def test_sidecar_publish_rejects_role_directory_reparent_race_without_residue(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = ProjectBundleFixture(Path(directory))
            escaped = Path(directory) / "escaped-reviews"
            original_link = review_module.os.link
            moved = False

            def racing_link(*args, **kwargs):
                nonlocal moved
                if not moved:
                    moved = True
                    (fixture.root / "reviews").rename(escaped)
                    (fixture.root / "reviews").mkdir()
                return original_link(*args, **kwargs)

            output = fixture.root / "reviews" / "race.json"
            with patch.object(review_module.os, "link", side_effect=racing_link):
                with self.assertRaises(ValueError):
                    review_module.review_project_image(
                        fixture.root,
                        fixture.evidence_paths(),
                        fixture.selected_review(),
                        output_sidecar=output,
                    )
            self.assertFalse(output.exists())
            self.assertFalse((escaped / "race.json").exists())

    def test_artifact_mutation_after_snapshot_is_rejected_for_review_and_promotion(self) -> None:
        for operation in ("review", "promotion"):
            with self.subTest(operation=operation), tempfile.TemporaryDirectory() as directory:
                fixture = ProjectBundleFixture(Path(directory))
                selection_path = fixture.paths["selection"]
                original = selection_path.read_bytes()
                changed_selection = fixture.read("selection")
                changed_selection["selected_references"][0]["record_id"] = "COV-CN-FORGED-RACE"
                changed = json_bytes(changed_selection)
                original_compile = review_module.compile_component_prompt
                mutated = False

                def racing_compile(*args, **kwargs):
                    nonlocal mutated
                    result = original_compile(*args, **kwargs)
                    if not mutated:
                        mutated = True
                        selection_path.write_bytes(changed)
                    return result

                if operation == "promotion":
                    review_path = fixture.root / "reviews" / "selected.json"
                    review_module.review_project_image(
                        fixture.root,
                        fixture.evidence_paths(),
                        fixture.selected_review(),
                        output_sidecar=review_path,
                    )
                    selection_path.write_bytes(original)
                with patch.object(
                    review_module,
                    "compile_component_prompt",
                    side_effect=racing_compile,
                ):
                    with self.assertRaises(ValueError):
                        if operation == "review":
                            review_module.review_project_image(
                                fixture.root,
                                fixture.evidence_paths(),
                                fixture.selected_review(),
                            )
                        else:
                            review_module.prepare_project_promotion(
                                fixture.root,
                                fixture.evidence_paths(),
                                review_path,
                                "cover",
                            )

    def test_coherent_cross_component_relabel_with_cover_records_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = ProjectBundleFixture(Path(directory))
            selection = fixture.read("selection")
            selection["component_type"] = "toc"
            fixture.paths["selection"].write_bytes(json_bytes(selection))
            retrieval = fixture.read("retrieval_result")
            retrieval["component_type"] = "toc"
            fixture.paths["retrieval_result"].write_bytes(json_bytes(retrieval))
            with self.assertRaises(ValueError):
                review_module.validate_project_generation_bundle(
                    fixture.root,
                    review_module.ProjectGenerationEvidencePaths(
                        project_config=fixture.paths["project_config"],
                        genome=fixture.paths["genome"],
                        selection=fixture.paths["selection"],
                        retrieval_result=fixture.paths["retrieval_result"],
                        output_spec=fixture.paths["output_spec"],
                        prompt=fixture.paths["prompt"],
                        generation_payload=fixture.paths["generation_payload"],
                        generation_authorization=fixture.paths["generation_authorization"],
                    ),
                )

    def test_project_review_and_promotion_revalidate_the_complete_disk_chain(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = ProjectBundleFixture(Path(directory))
            evidence = fixture.evidence_paths()
            review_output = fixture.root / "reviews" / "REVIEW-COVER-T17-0001.json"
            reviewed = review_module.review_project_image(
                fixture.root,
                evidence,
                fixture.selected_review(),
                output_sidecar=review_output,
            )
            proposal_output = (
                fixture.root / "promotions" / "PROMOTE-COVER-T17-0001.json"
            )
            proposal = review_module.prepare_project_promotion(
                fixture.root,
                evidence,
                review_output,
                "cover",
                output_sidecar=proposal_output,
            )
            self.assertEqual(reviewed, json.loads(review_output.read_text()))
            self.assertEqual(proposal, json.loads(proposal_output.read_text()))
            self.assertEqual("proposed", proposal["status"])
            self.assertEqual("pending", proposal["human_approval"])
            self.assertEqual(
                fixture.read("prompt")["editable_text_overlay"],
                json.loads(fixture.overlay.read_text(encoding="utf-8")),
            )
            self.assertEqual(
                [],
                validate_data(
                    json.loads(fixture.manifest.read_text(encoding="utf-8")),
                    "image-manifest",
                ),
            )
            for name, schema in (
                ("generation_payload", "book-project-image-generation-payload"),
                (
                    "generation_authorization",
                    "book-project-image-generation-authorization",
                ),
                ("version", "book-project-image-version"),
                (
                    "selection_approval",
                    "book-project-image-selection-approval",
                ),
            ):
                with self.subTest(artifact=name):
                    self.assertEqual([], validate_data(fixture.read(name), schema))
                    self.assertTrue(
                        fixture.paths[name].resolve().is_relative_to(
                            fixture.root.resolve()
                        )
                    )

    def test_project_chain_rejects_forged_binding_fields_and_approval_artifacts(self) -> None:
        mutations = {
            "selection_id": ("version", "selection_id", "SEL-FORGED"),
            "prompt_id": ("version", "prompt_id", "PROMPT-FORGED"),
            "component": ("version", "component_type", "toc"),
            "record_ids": ("version", "record_ids", ["FAKE-1", "FAKE-2"]),
            "selection_hash": ("version", "selection_sha256", "0" * 64),
            "prompt_hash": ("version", "prompt_sha256", "0" * 64),
            "payload_hash": (
                "version",
                "generation_payload_sha256",
                "0" * 64,
            ),
        }
        for label, (artifact, field, value) in mutations.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as directory:
                fixture = ProjectBundleFixture(Path(directory))
                changed = fixture.read(artifact)
                changed[field] = value
                fixture.paths[artifact].write_bytes(json_bytes(changed))
                with self.assertRaises(ValueError):
                    review_module.review_project_image(
                        fixture.root,
                        fixture.evidence_paths(),
                        fixture.selected_review(),
                    )

        for label in ("missing", "outside", "symlink", "content"):
            with self.subTest(label=label), tempfile.TemporaryDirectory() as directory:
                fixture = ProjectBundleFixture(Path(directory))
                paths = fixture.evidence_paths()
                review = fixture.selected_review()
                if label == "missing":
                    fixture.paths["selection_approval"].unlink()
                elif label == "outside":
                    outside = Path(directory) / "outside-approval.json"
                    shutil.copyfile(fixture.paths["selection_approval"], outside)
                    paths = copy.copy(paths)
                    object.__setattr__(paths, "selection_approval", outside)
                elif label == "symlink":
                    real = fixture.paths["selection_approval"]
                    linked = fixture.root / "approvals" / "linked.json"
                    linked.symlink_to(real)
                    paths = copy.copy(paths)
                    object.__setattr__(paths, "selection_approval", linked)
                else:
                    approval = fixture.read("selection_approval")
                    approval["prompt_id"] = "PROMPT-FORGED"
                    fixture.paths["selection_approval"].write_bytes(json_bytes(approval))
                with self.assertRaises(ValueError):
                    review_module.review_project_image(fixture.root, paths, review)

        for label in ("missing", "outside", "symlink", "content"):
            with self.subTest(generation_authorization=label), tempfile.TemporaryDirectory() as directory:
                fixture = ProjectBundleFixture(Path(directory))
                paths = fixture.evidence_paths()
                review = fixture.selected_review()
                if label == "missing":
                    fixture.paths["generation_authorization"].unlink()
                elif label == "outside":
                    outside = Path(directory) / "outside-generation-approval.json"
                    shutil.copyfile(fixture.paths["generation_authorization"], outside)
                    paths = copy.copy(paths)
                    object.__setattr__(paths, "generation_authorization", outside)
                elif label == "symlink":
                    real = fixture.paths["generation_authorization"]
                    linked = fixture.root / "approvals" / "linked-generation.json"
                    linked.symlink_to(real)
                    paths = copy.copy(paths)
                    object.__setattr__(paths, "generation_authorization", linked)
                else:
                    authorization = fixture.read("generation_authorization")
                    authorization["selection_id"] = "SEL-FORGED"
                    fixture.paths["generation_authorization"].write_bytes(
                        json_bytes(authorization)
                    )
                with self.assertRaises(ValueError):
                    review_module.review_project_image(fixture.root, paths, review)

        with tempfile.TemporaryDirectory() as directory:
            fixture = ProjectBundleFixture(Path(directory))
            review = fixture.selected_review()
            review["human_selection"]["approval_artifact_sha256"] = "0" * 64
            with self.assertRaises(ValueError):
                review_module.review_project_image(
                    fixture.root, fixture.evidence_paths(), review
                )

    def test_project_outputs_are_new_role_scoped_files_and_never_clobber_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            fixture = ProjectBundleFixture(Path(directory))
            evidence = fixture.evidence_paths()
            review = fixture.selected_review()
            protected = (
                fixture.paths["project_config"],
                fixture.paths["selection"],
                fixture.paths["prompt"],
                fixture.overlay,
                fixture.paths["version"],
                fixture.manifest,
                fixture.paths["selection_approval"],
                fixture.paths["generation_authorization"],
            )
            for target in protected:
                before = target.read_bytes()
                with self.subTest(target=target), self.assertRaises(ValueError):
                    review_module.review_project_image(
                        fixture.root, evidence, review, output_sidecar=target
                    )
                self.assertEqual(before, target.read_bytes())

            review_output = fixture.root / "reviews" / "selected.json"
            review_module.review_project_image(
                fixture.root, evidence, review, output_sidecar=review_output
            )
            review_before = review_output.read_bytes()
            with self.assertRaises(ValueError):
                review_module.review_project_image(
                    fixture.root, evidence, review, output_sidecar=review_output
                )
            self.assertEqual(review_before, review_output.read_bytes())
            with self.assertRaises(ValueError):
                review_module.prepare_project_promotion(
                    fixture.root,
                    evidence,
                    review_output,
                    "cover",
                    output_sidecar=review_output,
                )
            self.assertEqual(review_before, review_output.read_bytes())

            proposal_output = fixture.root / "promotions" / "proposal.json"
            proposal = review_module.prepare_project_promotion(
                fixture.root,
                evidence,
                review_output,
                "cover",
                output_sidecar=proposal_output,
            )
            proposal_before = proposal_output.read_bytes()
            self.assertEqual("proposed", proposal["status"])
            with self.assertRaises(ValueError):
                review_module.prepare_project_promotion(
                    fixture.root,
                    evidence,
                    review_output,
                    "cover",
                    output_sidecar=proposal_output,
                )
            self.assertEqual(proposal_before, proposal_output.read_bytes())

            hardlink = fixture.root / "reviews" / "hardlink.json"
            hardlink.hardlink_to(fixture.paths["prompt"])
            prompt_before = fixture.paths["prompt"].read_bytes()
            with self.assertRaises(ValueError):
                review_module.review_project_image(
                    fixture.root, evidence, review, output_sidecar=hardlink
                )
            self.assertEqual(prompt_before, fixture.paths["prompt"].read_bytes())

    def test_generation_references_must_be_exact_authorized_project_images(self) -> None:
        cases = ("overlay", "outside", "traversal", "symlink", "unauthorized")
        for label in cases:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as directory:
                fixture = ProjectBundleFixture(Path(directory))
                if label == "overlay":
                    reference = fixture.root / "overlays" / "title.png"
                    shutil.copyfile(SOURCE_IMAGE, reference)
                    payload_path = "overlays/title.png"
                elif label == "outside":
                    reference = Path(directory) / "outside.jpg"
                    shutil.copyfile(SOURCE_IMAGE, reference)
                    payload_path = str(reference)
                elif label == "traversal":
                    reference = Path(directory) / "outside.jpg"
                    shutil.copyfile(SOURCE_IMAGE, reference)
                    payload_path = "references/../../outside.jpg"
                elif label == "symlink":
                    reference = fixture.root / "references" / "linked.jpg"
                    reference.symlink_to(SOURCE_IMAGE)
                    payload_path = "references/linked.jpg"
                else:
                    reference = fixture.root / "references" / "unapproved.jpg"
                    shutil.copyfile(SOURCE_IMAGE, reference)
                    payload_path = "references/unapproved.jpg"
                payload = fixture.read("generation_payload")
                payload["referenced_image_paths"] = [payload_path]
                fixture.paths["generation_payload"].write_bytes(json_bytes(payload))
                authorization = fixture.read("generation_authorization")
                authorization["generation_payload_sha256"] = sha256_file(
                    fixture.paths["generation_payload"]
                )
                # Deliberately leave the exact authorized image list empty.
                fixture.paths["generation_authorization"].write_bytes(
                    json_bytes(authorization)
                )
                version = fixture.read("version")
                version["generation_payload_sha256"] = sha256_file(
                    fixture.paths["generation_payload"]
                )
                version["generation_authorization_sha256"] = sha256_file(
                    fixture.paths["generation_authorization"]
                )
                fixture.paths["version"].write_bytes(json_bytes(version))
                with self.assertRaises(ValueError):
                    review_module.review_project_image(
                        fixture.root,
                        fixture.evidence_paths(),
                        fixture.selected_review(),
                    )


if __name__ == "__main__":
    unittest.main()
