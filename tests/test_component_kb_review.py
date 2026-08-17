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
from contextlib import redirect_stderr
from pathlib import Path
from unittest.mock import patch

from PIL import Image

import ai.book_component_kb.review as review_module
import scripts.book_component_kb.promote_image as promotion_cli
import scripts.book_component_kb.review_image as review_cli
from ai.contracts import validate_data
from ai.book_component_kb.review import prepare_promotion, review_image


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CHECK_NAMES = (
    "no_unwanted_text",
    "safe_zones_clear",
    "genome_consistent",
    "reference_transformed",
    "print_crop_valid",
    "truthfulness_valid",
    "provenance_complete",
)
INTEGRATED_CHECK_NAMES = (
    "integrated_text_exact",
    "no_extra_text",
    "typography_usable",
    "machine_identifiers_absent",
)


def png_bytes() -> bytes:
    output = io.BytesIO()
    Image.new("RGB", (12, 18), (233, 228, 214)).save(output, format="PNG")
    return output.getvalue()


def valid_review(image_bytes: bytes, *, status: str = "selected") -> dict:
    result = {
        "schema_version": "1.0",
        "review_id": "REVIEW-COV-0001",
        "prompt_id": "PROMPT-COV-0001",
        "component_type": "cover",
        "image": {
            "relative_path": "generated/cover-0001.png",
            "sha256": hashlib.sha256(image_bytes).hexdigest(),
            "mime_type": "image/png",
        },
        "observations": [
            {
                "aspect": "标题安全区",
                "value": "上方留白完整且没有生成文字",
                "visibility": "clear",
                "confidence": 0.95,
                "evidence": "上方约三分之一为连续浅色背景",
                "content_tags": ["留白", "无字底图"],
            }
        ],
        "checks": {name: True for name in CHECK_NAMES},
        "status": status,
    }
    if status == "selected":
        result["human_selection"] = {
            "decision": "selected",
            "approval_id": "APPROVAL-COV-0001",
            "approved_by": "项目维护人",
            "selected_version": "V001",
            "selected_image_sha256": hashlib.sha256(image_bytes).hexdigest(),
            "approval_artifact_sha256": "a" * 64,
        }
    return result


def valid_integrated_review(image_bytes: bytes, *, status: str = "selected") -> dict:
    result = valid_review(image_bytes, status=status)
    result["text_rendering_mode"] = "integrated-typography"
    result["integrated_text"] = [
        {
            "text_id": "TITLE-001",
            "surface": "front",
            "role": "title",
            "value": "失落人间",
            "language": "zh-CN",
        }
    ]
    result["checks"].update({name: True for name in INTEGRATED_CHECK_NAMES})
    return result


class HumanSelectionEvidenceTests(unittest.TestCase):
    def test_selected_review_without_human_selection_evidence_is_rejected(self) -> None:
        review = valid_review(png_bytes(), status="selected")
        del review["human_selection"]
        with self.assertRaisesRegex(ValueError, "human_selection|schema"):
            review_image(review)

    def test_selected_review_rejects_wrong_hash_version_and_artifact_shape(self) -> None:
        image_bytes = png_bytes()
        cases = (
            ("image hash", {"selected_image_sha256": "0" * 64}),
            ("version", {"selected_version": "latest"}),
            ("artifact", {"approval_artifact_sha256": "not-a-sha"}),
        )
        for label, mutation in cases:
            with self.subTest(label=label):
                review = valid_review(image_bytes, status="selected")
                review["human_selection"] = {
                    "decision": "selected",
                    "approval_id": "APPROVAL-T17-0001",
                    "approved_by": "项目维护人",
                    "selected_version": "V001",
                    "selected_image_sha256": hashlib.sha256(image_bytes).hexdigest(),
                    "approval_artifact_sha256": "a" * 64,
                    **mutation,
                }
                with self.assertRaises(ValueError):
                    review_image(review)

    def test_nonselected_review_cannot_carry_selected_human_evidence(self) -> None:
        review = valid_review(png_bytes(), status="draft")
        review["human_selection"] = {
            "decision": "selected",
            "approval_id": "APPROVAL-T17-0001",
            "approved_by": "项目维护人",
            "selected_version": "V001",
            "selected_image_sha256": review["image"]["sha256"],
            "approval_artifact_sha256": "a" * 64,
        }
        with self.assertRaisesRegex(ValueError, "schema"):
            review_image(review)


class ComponentImageReviewTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = Path(self.temp_dir.name)
        self.image_bytes = png_bytes()
        self.image = self.root / "generated-cover.jpg"
        self.image.write_bytes(self.image_bytes)

    def test_review_image_accepts_a_schema_valid_record_without_mutating_input(self) -> None:
        source = valid_review(self.image_bytes)
        before = copy.deepcopy(source)

        reviewed = review_image(source)

        self.assertEqual(before, source)
        self.assertEqual(before, reviewed)
        self.assertIsNot(source, reviewed)
        self.assertEqual([], validate_data(reviewed, "book-component-image-review"))

    def test_selected_review_rejects_each_individual_false_check(self) -> None:
        for check_name in CHECK_NAMES:
            with self.subTest(check_name=check_name):
                review = valid_review(self.image_bytes)
                review["checks"][check_name] = False
                with self.assertRaisesRegex(ValueError, "selected.*seven checks"):
                    review_image(review)

    def test_integrated_review_requires_each_of_four_stable_effect_checks(self) -> None:
        accepted = valid_integrated_review(self.image_bytes)
        self.assertEqual(accepted, review_image(accepted))
        for check_name in INTEGRATED_CHECK_NAMES:
            with self.subTest(check_name=check_name):
                review = valid_integrated_review(self.image_bytes)
                review["checks"][check_name] = False
                with self.assertRaisesRegex(
                    ValueError, "integrated typography checks"
                ):
                    review_image(review)

    def test_review_text_mode_and_exact_entries_must_match_compiled_prompt(self) -> None:
        from tests.test_cover_integrated_typography_contracts import integrated_prompt

        validator = getattr(review_module, "validate_review_text_contract", None)
        self.assertTrue(callable(validator), "missing review text contract validator")
        prompt = integrated_prompt()
        review = valid_integrated_review(self.image_bytes)
        review["integrated_text"] = copy.deepcopy(prompt["integrated_text"])
        self.assertIsNone(validator(prompt, review))

        legacy_claim = valid_review(self.image_bytes)
        with self.assertRaisesRegex(ValueError, "text rendering mode"):
            validator(prompt, legacy_claim)

        changed = valid_integrated_review(self.image_bytes)
        changed["integrated_text"] = copy.deepcopy(prompt["integrated_text"])
        changed["integrated_text"][0]["value"] = "失落人问"
        with self.assertRaisesRegex(ValueError, "integrated text"):
            validator(prompt, changed)

    def test_review_image_rejects_malformed_schema(self) -> None:
        review = valid_review(self.image_bytes)
        del review["checks"]["provenance_complete"]
        with self.assertRaisesRegex(ValueError, "review schema validation failed"):
            review_image(review)

    def test_python_apis_reject_nonfinite_observation_confidence(self) -> None:
        for confidence in (float("nan"), float("inf"), float("-inf")):
            with self.subTest(confidence=confidence):
                review = valid_review(self.image_bytes)
                review["observations"][0]["confidence"] = confidence
                with self.assertRaisesRegex(ValueError, "finite"):
                    review_image(review)
                with self.assertRaisesRegex(ValueError, "finite"):
                    prepare_promotion(review, self.image, "cover")

    def test_unselected_reviews_cannot_be_promoted(self) -> None:
        for status in ("draft", "archived", "rejected"):
            with self.subTest(status=status):
                with self.assertRaisesRegex(ValueError, "selected"):
                    prepare_promotion(
                        valid_review(self.image_bytes, status=status),
                        self.image,
                        "cover",
                    )

    def test_prepare_promotion_rechecks_selected_review_and_component(self) -> None:
        review = valid_review(self.image_bytes)
        review["checks"]["truthfulness_valid"] = False
        with self.assertRaisesRegex(ValueError, "selected.*seven checks"):
            prepare_promotion(review, self.image, "cover")

        with self.assertRaisesRegex(ValueError, "component"):
            prepare_promotion(valid_review(self.image_bytes), self.image, "toc")

    def test_selected_image_remains_a_pending_accumulation_proposal(self) -> None:
        proposal = prepare_promotion(
            valid_review(self.image_bytes), self.image, "cover"
        )

        self.assertEqual("proposed", proposal["status"])
        self.assertEqual("pending", proposal["human_approval"])
        self.assertEqual("accumulation", proposal["target_lifecycle"])
        self.assertEqual("cover", proposal["component_type"])
        self.assertEqual([], validate_data(proposal, "book-component-kb-promotion"))

    def test_promotion_ids_and_json_are_deterministic(self) -> None:
        review = valid_review(self.image_bytes)
        first = prepare_promotion(review, self.image, "cover")
        second = prepare_promotion(copy.deepcopy(review), self.image, "cover")

        self.assertEqual(first, second)
        self.assertEqual(
            json.dumps(first, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
            json.dumps(second, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
        )
        self.assertTrue(first["record_id"].startswith("ACC-COV-"))
        self.assertTrue(first["promotion_id"].startswith("PROMOTE-COV-"))

    def test_image_mime_and_sha_are_derived_from_bytes_not_extension_or_review_claims(self) -> None:
        proposal = prepare_promotion(
            valid_review(self.image_bytes), self.image, "cover"
        )
        self.assertEqual("proposed", proposal["status"])

        bad_mime = valid_review(self.image_bytes)
        bad_mime["image"]["mime_type"] = "image/jpeg"
        with self.assertRaisesRegex(ValueError, "MIME"):
            prepare_promotion(bad_mime, self.image, "cover")

        bad_sha = valid_review(self.image_bytes)
        bad_sha["image"]["sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            prepare_promotion(bad_sha, self.image, "cover")

    def test_missing_symlink_special_and_undecodable_images_are_rejected(self) -> None:
        review = valid_review(self.image_bytes)
        with self.assertRaises(ValueError):
            prepare_promotion(review, self.root / "missing.png", "cover")

        symlink = self.root / "linked.png"
        symlink.symlink_to(self.image)
        with self.assertRaises(ValueError):
            prepare_promotion(review, symlink, "cover")

        directory = self.root / "directory.png"
        directory.mkdir()
        with self.assertRaises(ValueError):
            prepare_promotion(review, directory, "cover")

        undecodable = self.root / "not-an-image.png"
        undecodable.write_bytes(b"not an image")
        undecodable_review = valid_review(b"not an image")
        with self.assertRaisesRegex(ValueError, "decodable image"):
            prepare_promotion(undecodable_review, undecodable, "cover")

    @unittest.skipUnless(hasattr(os, "mkfifo"), "POSIX FIFO support is unavailable")
    def test_fifo_is_rejected_without_blocking(self) -> None:
        fifo = self.root / "stream.png"
        os.mkfifo(fifo)
        with self.assertRaises(ValueError):
            prepare_promotion(valid_review(self.image_bytes), fifo, "cover")

    def test_review_cli_uses_strict_json_and_writes_only_one_sidecar(self) -> None:
        review_path = self.root / "review-input.json"
        output_path = self.root / "review-output.json"
        review_path.write_text(
            json.dumps(valid_review(self.image_bytes), ensure_ascii=False),
            encoding="utf-8",
        )
        result = subprocess.run(
            [
                sys.executable,
                str(PROJECT_ROOT / "scripts/book_component_kb/review_image.py"),
                "--input",
                str(review_path),
                "--output",
                str(output_path),
            ],
            cwd=PROJECT_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("", result.stdout)
        self.assertEqual(
            ["generated-cover.jpg", "review-input.json", "review-output.json"],
            sorted(path.name for path in self.root.iterdir() if path.is_file()),
        )
        self.assertEqual(valid_review(self.image_bytes), json.loads(output_path.read_text(encoding="utf-8")))

        output_path.unlink()
        review_path.write_text('{"confidence": NaN}', encoding="utf-8")
        failure = subprocess.run(
            [
                sys.executable,
                str(PROJECT_ROOT / "scripts/book_component_kb/review_image.py"),
                "--input",
                str(review_path),
                "--output",
                str(output_path),
            ],
            cwd=PROJECT_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertNotEqual(0, failure.returncode)
        self.assertFalse(output_path.exists())

    def test_promotion_cli_writes_sidecar_only_and_never_changes_the_image(self) -> None:
        review_path = self.root / "review.json"
        output_path = self.root / "promotion.json"
        review_path.write_text(
            json.dumps(valid_review(self.image_bytes), ensure_ascii=False),
            encoding="utf-8",
        )
        before = self.image.read_bytes()
        result = subprocess.run(
            [
                sys.executable,
                str(PROJECT_ROOT / "scripts/book_component_kb/promote_image.py"),
                "--review",
                str(review_path),
                "--source-image",
                str(self.image),
                "--target-component",
                "cover",
                "--output",
                str(output_path),
            ],
            cwd=PROJECT_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("", result.stdout)
        self.assertEqual(before, self.image.read_bytes())
        self.assertEqual(
            ["generated-cover.jpg", "promotion.json", "review.json"],
            sorted(path.name for path in self.root.iterdir() if path.is_file()),
        )
        proposal = json.loads(output_path.read_text(encoding="utf-8"))
        self.assertEqual("pending", proposal["human_approval"])

    def test_clis_reject_output_aliases_of_json_inputs_and_source_image(self) -> None:
        review_path = self.root / "review.json"
        review_path.write_text(
            json.dumps(valid_review(self.image_bytes), ensure_ascii=False),
            encoding="utf-8",
        )
        commands = (
            [
                sys.executable,
                str(PROJECT_ROOT / "scripts/book_component_kb/review_image.py"),
                "--input",
                str(review_path),
                "--output",
                str(review_path),
            ],
            [
                sys.executable,
                str(PROJECT_ROOT / "scripts/book_component_kb/promote_image.py"),
                "--review",
                str(review_path),
                "--source-image",
                str(self.image),
                "--target-component",
                "cover",
                "--output",
                str(self.image),
            ],
        )
        before_review = review_path.read_bytes()
        before_image = self.image.read_bytes()
        for command in commands:
            result = subprocess.run(
                command,
                cwd=PROJECT_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertNotEqual(0, result.returncode)
        self.assertEqual(before_review, review_path.read_bytes())
        self.assertEqual(before_image, self.image.read_bytes())

    def test_clis_reject_non_json_output_paths(self) -> None:
        review_path = self.root / "review.json"
        review_path.write_text(
            json.dumps(valid_review(self.image_bytes), ensure_ascii=False),
            encoding="utf-8",
        )
        outputs = (self.root / "review.md", self.root / "promotion.txt")
        commands = (
            [
                sys.executable,
                str(PROJECT_ROOT / "scripts/book_component_kb/review_image.py"),
                "--input",
                str(review_path),
                "--output",
                str(outputs[0]),
            ],
            [
                sys.executable,
                str(PROJECT_ROOT / "scripts/book_component_kb/promote_image.py"),
                "--review",
                str(review_path),
                "--source-image",
                str(self.image),
                "--target-component",
                "cover",
                "--output",
                str(outputs[1]),
            ],
        )

        for command, output in zip(commands, outputs, strict=True):
            result = subprocess.run(
                command,
                cwd=PROJECT_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(1, result.returncode)
            self.assertFalse(output.exists())

    def test_clis_cannot_write_isolated_component_library_files(self) -> None:
        review_path = self.root / "review.json"
        review_path.write_text(
            json.dumps(valid_review(self.image_bytes), ensure_ascii=False),
            encoding="utf-8",
        )
        library = self.root / "knowledge" / "book-component-libraries"
        records = library / "cover" / "records"
        assets = library / "cover" / "assets"
        records.mkdir(parents=True)
        assets.mkdir()
        protected_paths = (
            library / "cover" / "manifest.json",
            records / "COV-CN-0001.json",
            library / "source-registry.json",
            assets / "COV-CN-0001.png",
        )
        for path in protected_paths:
            path.write_bytes(f"SENTINEL:{path.name}".encode("utf-8"))
        before = {path: path.read_bytes() for path in protected_paths}

        commands = (
            [
                sys.executable,
                str(PROJECT_ROOT / "scripts/book_component_kb/review_image.py"),
                "--input",
                str(review_path),
                "--output",
                str(protected_paths[0]),
            ],
            [
                sys.executable,
                str(PROJECT_ROOT / "scripts/book_component_kb/review_image.py"),
                "--input",
                str(review_path),
                "--output",
                str(protected_paths[1]),
            ],
            [
                sys.executable,
                str(PROJECT_ROOT / "scripts/book_component_kb/promote_image.py"),
                "--review",
                str(review_path),
                "--source-image",
                str(self.image),
                "--target-component",
                "cover",
                "--output",
                str(protected_paths[2]),
            ],
            [
                sys.executable,
                str(PROJECT_ROOT / "scripts/book_component_kb/promote_image.py"),
                "--review",
                str(review_path),
                "--source-image",
                str(self.image),
                "--target-component",
                "cover",
                "--output",
                str(protected_paths[3]),
            ],
        )
        for command in commands:
            result = subprocess.run(
                command,
                cwd=PROJECT_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(1, result.returncode)
        self.assertEqual(before, {path: path.read_bytes() for path in protected_paths})

    def test_review_cli_rejects_symlink_dotdot_and_hardlink_routes_to_protected_files(self) -> None:
        review_path = self.root / "review.json"
        review_path.write_text(
            json.dumps(valid_review(self.image_bytes), ensure_ascii=False),
            encoding="utf-8",
        )
        library = self.root / "knowledge" / "book-component-libraries"
        cover = library / "cover"
        cover.mkdir(parents=True)
        (cover / "records").mkdir()
        manifest = cover / "manifest.json"
        manifest.write_bytes(b"SENTINEL:manifest")
        alias = self.root / "library-alias"
        alias.symlink_to(library, target_is_directory=True)
        hardlink = self.root / "hardlinked-manifest.json"
        os.link(manifest, hardlink)
        outputs = (
            alias / "cover" / "manifest.json",
            cover / "records" / ".." / "manifest.json",
            hardlink,
        )
        before = manifest.read_bytes()

        for output in outputs:
            result = subprocess.run(
                [
                    sys.executable,
                    str(PROJECT_ROOT / "scripts/book_component_kb/review_image.py"),
                    "--input",
                    str(review_path),
                    "--output",
                    str(output),
                ],
                cwd=PROJECT_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(1, result.returncode)
        self.assertEqual(before, manifest.read_bytes())
        self.assertEqual(before, hardlink.read_bytes())

    def test_clis_reject_case_variants_of_component_library_paths_on_macos_volume(self) -> None:
        review_path = self.root / "review.json"
        review_path.write_text(
            json.dumps(valid_review(self.image_bytes), ensure_ascii=False),
            encoding="utf-8",
        )
        library = self.root / "knowledge" / "book-component-libraries"
        cover = library / "cover"
        cover.mkdir(parents=True)
        manifest = cover / "manifest.json"
        registry = library / "source-registry.json"
        manifest.write_bytes(b"SENTINEL:manifest-case")
        registry.write_bytes(b"SENTINEL:registry-case")
        case_variant_manifest = (
            self.root
            / "KNOWLEDGE"
            / "book-component-libraries"
            / "cover"
            / "manifest.json"
        )
        case_variant_registry = (
            self.root
            / "knowledge"
            / "BOOK-COMPONENT-LIBRARIES"
            / "source-registry.json"
        )
        if not (
            case_variant_manifest.exists()
            and case_variant_registry.exists()
            and os.path.samefile(case_variant_manifest, manifest)
            and os.path.samefile(case_variant_registry, registry)
        ):
            self.skipTest("test requires the current case-insensitive macOS volume")
        before_manifest = manifest.read_bytes()
        before_registry = registry.read_bytes()

        commands = (
            [
                sys.executable,
                str(PROJECT_ROOT / "scripts/book_component_kb/review_image.py"),
                "--input",
                str(review_path),
                "--output",
                str(case_variant_manifest),
            ],
            [
                sys.executable,
                str(PROJECT_ROOT / "scripts/book_component_kb/promote_image.py"),
                "--review",
                str(review_path),
                "--source-image",
                str(self.image),
                "--target-component",
                "cover",
                "--output",
                str(case_variant_registry),
            ],
        )
        for command in commands:
            result = subprocess.run(
                command,
                cwd=PROJECT_ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(1, result.returncode)
        self.assertEqual(before_manifest, manifest.read_bytes())
        self.assertEqual(before_registry, registry.read_bytes())

    def test_review_cli_parent_swap_cannot_redirect_output_into_protected_library(self) -> None:
        review_path = self.root / "review.json"
        review_path.write_text(
            json.dumps(valid_review(self.image_bytes), ensure_ascii=False),
            encoding="utf-8",
        )
        safe_parent = self.root / "safe-review-output"
        safe_parent.mkdir()
        protected = self.root / "knowledge" / "book-component-libraries"
        protected.mkdir(parents=True)
        output = safe_parent / "review-sidecar.json"
        original_parent = self.root / "safe-review-output-original"
        real_writer = review_cli._write_json_atomic

        def swap_then_write(path, value, *args):
            safe_parent.rename(original_parent)
            safe_parent.symlink_to(protected, target_is_directory=True)
            return real_writer(path, value, *args)

        before_input = review_path.read_bytes()
        with (
            patch.object(
                sys,
                "argv",
                [
                    "review_image.py",
                    "--input",
                    str(review_path),
                    "--output",
                    str(output),
                ],
            ),
            patch.object(review_cli, "_write_json_atomic", side_effect=swap_then_write),
            redirect_stderr(io.StringIO()),
        ):
            result = review_cli.main()

        self.assertEqual(1, result)
        self.assertEqual(before_input, review_path.read_bytes())
        self.assertFalse((protected / output.name).exists())
        self.assertFalse((original_parent / output.name).exists())

    def test_promotion_cli_parent_swap_cannot_redirect_output_onto_input_alias(self) -> None:
        alias_target = self.root / "input-alias-target"
        alias_target.mkdir()
        review_path = alias_target / "promotion-sidecar.json"
        review_path.write_text(
            json.dumps(valid_review(self.image_bytes), ensure_ascii=False),
            encoding="utf-8",
        )
        safe_parent = self.root / "safe-promotion-output"
        safe_parent.mkdir()
        output = safe_parent / review_path.name
        original_parent = self.root / "safe-promotion-output-original"
        real_writer = promotion_cli._write_json_atomic

        def swap_then_write(path, value, *args):
            safe_parent.rename(original_parent)
            safe_parent.symlink_to(alias_target, target_is_directory=True)
            return real_writer(path, value, *args)

        before_input = review_path.read_bytes()
        with (
            patch.object(
                sys,
                "argv",
                [
                    "promote_image.py",
                    "--review",
                    str(review_path),
                    "--source-image",
                    str(self.image),
                    "--target-component",
                    "cover",
                    "--output",
                    str(output),
                ],
            ),
            patch.object(
                promotion_cli, "_write_json_atomic", side_effect=swap_then_write
            ),
            redirect_stderr(io.StringIO()),
        ):
            result = promotion_cli.main()

        self.assertEqual(1, result)
        self.assertEqual(before_input, review_path.read_bytes())
        self.assertFalse((original_parent / output.name).exists())

    def test_shared_writer_rejects_parent_identity_swap_after_open(self) -> None:
        writer = getattr(review_module, "write_json_sidecar_atomic")
        safe_parent = self.root / "safe-writer-output"
        safe_parent.mkdir()
        replacement = self.root / "replacement-output"
        replacement.mkdir()
        original_parent = self.root / "safe-writer-output-original"
        output = safe_parent / "sidecar.json"
        real_open_parent = review_module._open_output_parent

        def open_then_swap(parent):
            opened = real_open_parent(parent)
            safe_parent.rename(original_parent)
            replacement.rename(safe_parent)
            return opened

        with patch.object(
            review_module, "_open_output_parent", side_effect=open_then_swap
        ):
            with self.assertRaisesRegex(ValueError, "identity"):
                writer(output, {"status": "pending"}, ())

        self.assertFalse((safe_parent / output.name).exists())
        self.assertFalse((original_parent / output.name).exists())

    def test_shared_writer_rejects_nonfinite_json_without_leaving_temp_files(self) -> None:
        writer = getattr(review_module, "write_json_sidecar_atomic")
        output = self.root / "nonfinite.json"
        with self.assertRaises(ValueError):
            writer(output, {"confidence": float("nan")}, ())
        self.assertFalse(output.exists())
        self.assertEqual([], list(self.root.glob(".nonfinite.json.*.tmp")))


if __name__ == "__main__":
    unittest.main()
