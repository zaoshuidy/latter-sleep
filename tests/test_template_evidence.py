import unittest

from ai.contracts import validate_data


class TemplateEvidenceContractTests(unittest.TestCase):
    def valid_candidate_record(self):
        return {
            "schema_version": "1.0",
            "evidence_id": "EVD-LULU-A5-001",
            "template_id": "TPL-LULU-A5-INTERIOR",
            "status": "candidate",
            "original": {
                "provider": "Lulu",
                "source_url": "https://assets.lulu.com/media/templates/book/lulu-book-template-all-a5.zip",
                "relative_path": "research/reference-originals/lulu-book-template-all-a5.zip",
                "sha256": "B604553285B3C811350F34D499377D63E74B9ACFBBD7524FFA4D5871F304A243",
                "format": "zip-with-indd-idml",
            },
            "chinese_book_references": [],
            "adobe_sources": [],
            "print_sources": [],
            "field_mapping_path": None,
            "activation_errors": [
                "requires two Chinese published-book references",
                "requires one Adobe source",
                "requires one print or trim source",
                "requires reviewed field mapping",
            ],
        }

    def valid_approved_record(self):
        record = self.valid_candidate_record()
        record["status"] = "approved"
        record["chinese_book_references"] = [
            "ISBN 9787100000001 / 某出版社 / 2022",
            "ISBN 9787100000002 / 某出版社 / 2024",
        ]
        record["adobe_sources"] = [
            "https://helpx.adobe.com/indesign/using/templates.html",
        ]
        record["print_sources"] = [
            "https://www.example.com/print-trim-guide",
        ]
        record["field_mapping_path"] = "references/templates/lulu-a5/field-mapping-reviewed.json"
        record["activation_errors"] = []
        return record

    def test_candidate_record_is_schema_valid(self):
        self.assertEqual([], validate_data(self.valid_candidate_record(), "template-evidence"))

    def test_approved_record_requires_closed_evidence_gate(self):
        record = self.valid_candidate_record()
        record["status"] = "approved"
        self.assertTrue(validate_data(record, "template-evidence"))

    def test_approved_record_is_schema_valid_once_gate_is_complete(self):
        self.assertEqual([], validate_data(self.valid_approved_record(), "template-evidence"))

    def test_schema_is_closed_to_unexpected_properties(self):
        record = self.valid_candidate_record()
        record["unexpected"] = True
        self.assertTrue(validate_data(record, "template-evidence"))

    def test_approved_record_requires_zero_activation_errors(self):
        record = self.valid_approved_record()
        record["activation_errors"] = ["still pending"]
        self.assertTrue(validate_data(record, "template-evidence"))


if __name__ == "__main__":
    unittest.main()
