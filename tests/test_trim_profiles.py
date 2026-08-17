import unittest

from ai.contracts import validate_data


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

    def test_candidate_can_omit_dimensions_but_cannot_be_executable(self):
        self.assertEqual([], validate_data(self.valid_candidate_profile(), "trim-profile"))

    def test_approved_profile_requires_complete_physical_data(self):
        profile = self.valid_candidate_profile()
        profile["status"] = "approved"
        self.assertTrue(validate_data(profile, "trim-profile"))

    def test_approved_profile_is_schema_valid_once_evidence_is_complete(self):
        self.assertEqual([], validate_data(self.valid_approved_profile(), "trim-profile"))

    def test_candidate_profile_requires_null_physical_fields(self):
        profile = self.valid_candidate_profile()
        profile["trim_mm"] = [130, 184]
        self.assertTrue(validate_data(profile, "trim-profile"))

    def test_schema_is_closed_to_unexpected_properties(self):
        profile = self.valid_candidate_profile()
        profile["unexpected"] = "extra"
        self.assertTrue(validate_data(profile, "trim-profile"))


if __name__ == "__main__":
    unittest.main()
