from copy import deepcopy
import json
from pathlib import Path
import unittest

from ai.contracts import validate_data
from ai.indesign_templates.trim import load_trim_profile


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_PROFILE_ERRORS = ["missing exact evidence-backed dimensions"]


class TrimProfileContractTests(unittest.TestCase):
    def valid_candidate_profile(self):
        return {
            "schema_version": "1.0",
            "trim_profile_id": "TRIM-32K-STANDARD",
            "display_name": "标准32开",
            "status": "candidate",
            "trim_mm": None,
            "bleed_mm": None,
            "binding": None,
            "evidence_id": None,
            "activation_errors": ["missing exact evidence-backed dimensions"],
        }

    def valid_approved_profile(self):
        return {
            "schema_version": "1.0",
            "trim_profile_id": "TRIM-32K-STANDARD",
            "display_name": "标准32开",
            "status": "approved",
            "trim_mm": [130, 184],
            "bleed_mm": 3,
            "binding": "paperback-perfect-bound",
            "evidence_id": "EVD-LULU-A5-001",
            "activation_errors": [],
        }

    def assertSchemaErrorsContain(self, payload, schema_name, *expected_fragments):
        errors = validate_data(payload, schema_name)
        self.assertTrue(errors, "expected schema errors")
        joined = "\n".join(errors)
        for fragment in expected_fragments:
            self.assertIn(fragment, joined)
        return errors

    def test_candidate_can_omit_dimensions_but_cannot_be_executable(self):
        self.assertEqual([], validate_data(self.valid_candidate_profile(), "trim-profile"))

    def test_approved_profile_requires_complete_physical_data(self):
        profile = self.valid_candidate_profile()
        profile["status"] = "approved"
        self.assertTrue(validate_data(profile, "trim-profile"))

    def test_approved_profile_is_schema_valid_once_evidence_is_complete(self):
        self.assertEqual([], validate_data(self.valid_approved_profile(), "trim-profile"))

    def test_approved_profile_rejects_each_open_gate_independently(self):
        cases = [
            (
                "trim_mm zero",
                lambda profile: profile.__setitem__("trim_mm", [0, 184]),
                ("minimum of 0",),
            ),
            (
                "trim_mm negative",
                lambda profile: profile.__setitem__("trim_mm", [-1, 184]),
                ("minimum of 0",),
            ),
            (
                "trim_mm wrong item count short",
                lambda profile: profile.__setitem__("trim_mm", [130]),
                ("too short",),
            ),
            (
                "trim_mm wrong item count long",
                lambda profile: profile.__setitem__("trim_mm", [130, 184, 210]),
                ("too long", "at most 2 items"),
            ),
            (
                "negative bleed_mm",
                lambda profile: profile.__setitem__("bleed_mm", -1),
                ("minimum of 0",),
            ),
            (
                "empty binding",
                lambda profile: profile.__setitem__("binding", ""),
                ("non-empty",),
            ),
            (
                "empty evidence_id",
                lambda profile: profile.__setitem__("evidence_id", ""),
                ("non-empty", "^EVD-[A-Z0-9-]+$"),
            ),
            (
                "nonempty activation_errors",
                lambda profile: profile.__setitem__("activation_errors", ["pending"]),
                ("expected to be empty",),
            ),
        ]

        for label, mutate, expected_fragments in cases:
            with self.subTest(label=label):
                profile = deepcopy(self.valid_approved_profile())
                mutate(profile)
                self.assertSchemaErrorsContain(profile, "trim-profile", *expected_fragments)

    def test_candidate_profile_rejects_non_null_execution_fields_independently(self):
        cases = [
            (
                "trim_mm becomes non-null",
                lambda profile: profile.__setitem__("trim_mm", [130, 184]),
                ("not of type 'null'",),
            ),
            (
                "bleed_mm becomes non-null",
                lambda profile: profile.__setitem__("bleed_mm", 3),
                ("not of type 'null'",),
            ),
            (
                "binding becomes non-null",
                lambda profile: profile.__setitem__("binding", "paperback-perfect-bound"),
                ("not of type 'null'",),
            ),
            (
                "evidence_id becomes non-null",
                lambda profile: profile.__setitem__("evidence_id", "EVD-LULU-A5-001"),
                ("not of type 'null'",),
            ),
            (
                "activation_errors becomes empty",
                lambda profile: profile.__setitem__("activation_errors", []),
                ("non-empty",),
            ),
        ]

        for label, mutate, expected_fragments in cases:
            with self.subTest(label=label):
                profile = deepcopy(self.valid_candidate_profile())
                mutate(profile)
                self.assertSchemaErrorsContain(profile, "trim-profile", *expected_fragments)

    def test_schema_is_closed_to_unexpected_properties(self):
        profile = self.valid_candidate_profile()
        profile["unexpected"] = "extra"
        self.assertSchemaErrorsContain(profile, "trim-profile", "Additional properties are not allowed")


class TrimProfileRuntimeTests(unittest.TestCase):
    def test_inventory_contains_exactly_three_expected_profiles(self):
        names = sorted(path.stem for path in (ROOT / "templates" / "trim-profiles").glob("*.json"))
        self.assertEqual(["16k-standard", "32k-large", "32k-standard"], names)

    def test_registered_profiles_are_candidate_only_and_schema_valid(self):
        expected_profiles = {
            "16k-standard": ("TRIM-16K-STANDARD", "标准16开"),
            "32k-large": ("TRIM-32K-LARGE", "大32开"),
            "32k-standard": ("TRIM-32K-STANDARD", "标准32开"),
        }

        for stem, (trim_profile_id, display_name) in expected_profiles.items():
            with self.subTest(stem=stem):
                path = ROOT / "templates" / "trim-profiles" / f"{stem}.json"
                profile = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual([], validate_data(profile, "trim-profile"))
                self.assertEqual("1.0", profile["schema_version"])
                self.assertEqual(trim_profile_id, profile["trim_profile_id"])
                self.assertEqual(display_name, profile["display_name"])
                self.assertEqual("candidate", profile["status"])
                self.assertIsNone(profile["trim_mm"])
                self.assertIsNone(profile["bleed_mm"])
                self.assertIsNone(profile["binding"])
                self.assertIsNone(profile["evidence_id"])
                self.assertEqual(EXPECTED_PROFILE_ERRORS, profile["activation_errors"])

    def test_require_approved_rejects_each_registered_candidate_profile(self):
        for stem, trim_profile_id in [
            ("16k-standard", "TRIM-16K-STANDARD"),
            ("32k-large", "TRIM-32K-LARGE"),
            ("32k-standard", "TRIM-32K-STANDARD"),
        ]:
            with self.subTest(stem=stem):
                path = ROOT / "templates" / "trim-profiles" / f"{stem}.json"
                with self.assertRaisesRegex(ValueError, f"not approved.*{trim_profile_id}"):
                    load_trim_profile(path, require_approved=True)


if __name__ == "__main__":
    unittest.main()
