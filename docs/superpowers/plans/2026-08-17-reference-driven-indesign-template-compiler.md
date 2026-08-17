# Reference-Driven InDesign Template Compiler Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a zero-token, evidence-gated pipeline that converts semantic HTML/Markdown into styled InDesign body text, applies parent-page navigation, places high-resolution special pages, and refuses unverified trim/template combinations.

**Architecture:** A Python standard-library compiler converts HTML into `BookContentIR` and deterministic RTF, then emits a build manifest consumed by three fixed JSX scripts. INDT/IDML templates and trim profiles remain inactive until their evidence records satisfy the approved `1 original + 2 Chinese books + Adobe source + print/trim source` gate. MCP/COM only orchestrates InDesign execution and reads structured results.

**Tech Stack:** Python 3.13 standard library, JSON Schema, existing `jsonschema` dependency, RTF, Adobe InDesign 2025 ExtendScript/JSX, Windows COM bridge, `unittest`, existing InDesign PDF visual-QA tooling.

---

## File Structure

### Evidence and configuration

- Create `schemas/template-evidence.schema.json`: closed evidence record contract.
- Create `schemas/trim-profile.schema.json`: candidate/approved trim profile contract.
- Create `schemas/book-content-ir.schema.json`: semantic content blocks.
- Create `schemas/special-pages.schema.json`: special-page placement manifest.
- Create `references/templates/registry.json`: all evidence-backed template sources.
- Create `references/templates/lulu-a5/evidence.json`: immutable Lulu A5 acquisition record.
- Create `templates/trim-profiles/32k-standard.json`: candidate standard-32mo profile.
- Create `templates/trim-profiles/32k-large.json`: candidate large-32mo profile.
- Create `templates/trim-profiles/16k-standard.json`: candidate standard-16mo profile.

### Compiler

- Create `ai/indesign_templates/__init__.py`: public compiler API.
- Create `ai/indesign_templates/evidence.py`: evidence and activation validation.
- Create `ai/indesign_templates/content_ir.py`: HTML/Markdown semantic parser.
- Create `ai/indesign_templates/rtf.py`: deterministic UTF-8-to-RTF writer.
- Create `ai/indesign_templates/manifest.py`: build-manifest compiler.

### InDesign execution

- Create `skills/build-indesign-book/scripts/import_body.jsx`: place RTF and map styles.
- Create `skills/build-indesign-book/scripts/apply_masters.jsx`: page roles, parents, headers, folios.
- Create `skills/build-indesign-book/scripts/place_special_pages.jsx`: full-page/background image placement.
- Create `skills/build-indesign-book/scripts/compile_book.py`: CLI and COM orchestration.

### Tests and docs

- Create `tests/test_template_evidence.py`.
- Create `tests/test_trim_profiles.py`.
- Create `tests/test_book_content_ir.py`.
- Create `tests/test_rtf_export.py`.
- Create `tests/test_indesign_manifest.py`.
- Create `tests/test_indesign_template_pipeline.py`.
- Modify `skills/build-indesign-book/SKILL.md`.
- Modify `scripts/validate_all.py`.
- Modify `docs/图书生产Skills套件使用说明.md`.

---

### Task 1: Add Closed Evidence and Trim Contracts

**Files:**
- Create: `schemas/template-evidence.schema.json`
- Create: `schemas/trim-profile.schema.json`
- Test: `tests/test_template_evidence.py`
- Test: `tests/test_trim_profiles.py`

- [ ] **Step 1: Write failing evidence-schema tests**

```python
import unittest

from ai.contracts import validate_data


class TemplateEvidenceContractTests(unittest.TestCase):
    def valid_record(self):
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
                "format": "zip-with-indd-idml"
            },
            "chinese_book_references": [],
            "adobe_sources": [],
            "print_sources": [],
            "field_mapping_path": None,
            "activation_errors": [
                "requires two Chinese published-book references",
                "requires one Adobe source",
                "requires one print or trim source",
                "requires reviewed field mapping"
            ]
        }

    def test_candidate_record_is_schema_valid(self):
        self.assertEqual([], validate_data(self.valid_record(), "template-evidence"))

    def test_approved_record_requires_closed_evidence_gate(self):
        record = self.valid_record()
        record["status"] = "approved"
        self.assertTrue(validate_data(record, "template-evidence"))
```

```python
import unittest

from ai.contracts import validate_data


class TrimProfileContractTests(unittest.TestCase):
    def test_candidate_can_omit_dimensions_but_cannot_be_executable(self):
        profile = {
            "schema_version": "1.0",
            "trim_profile_id": "TRIM-32K-STANDARD",
            "display_name": "标准32开",
            "status": "candidate",
            "trim_mm": None,
            "bleed_mm": None,
            "binding": None,
            "evidence_id": None,
            "activation_errors": ["missing exact evidence-backed dimensions"]
        }
        self.assertEqual([], validate_data(profile, "trim-profile"))
```

- [ ] **Step 2: Run tests and verify missing schemas fail**

Run:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_template_evidence tests.test_trim_profiles -v
```

Expected: `FAIL` because `template-evidence.schema.json` and `trim-profile.schema.json` do not exist.

- [ ] **Step 3: Add the exact schema rules**

`template-evidence.schema.json` must be closed with these rules:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "required": ["schema_version", "evidence_id", "template_id", "status", "original", "chinese_book_references", "adobe_sources", "print_sources", "field_mapping_path", "activation_errors"],
  "properties": {
    "schema_version": {"const": "1.0"},
    "evidence_id": {"type": "string", "pattern": "^EVD-[A-Z0-9-]+$"},
    "template_id": {"type": "string", "pattern": "^TPL-[A-Z0-9-]+$"},
    "status": {"enum": ["candidate", "approved", "rejected", "archived"]},
    "original": {
      "type": "object",
      "required": ["provider", "source_url", "relative_path", "sha256", "format"],
      "properties": {
        "provider": {"type": "string", "minLength": 1},
        "source_url": {"type": "string", "format": "uri"},
        "relative_path": {"type": "string", "minLength": 1},
        "sha256": {"type": "string", "pattern": "^[A-F0-9]{64}$"},
        "format": {"enum": ["indd", "idml", "indt", "zip-with-indd-idml"]}
      },
      "additionalProperties": false
    },
    "chinese_book_references": {"type": "array", "items": {"type": "string"}},
    "adobe_sources": {"type": "array", "items": {"type": "string", "format": "uri"}},
    "print_sources": {"type": "array", "items": {"type": "string", "format": "uri"}},
    "field_mapping_path": {"type": ["string", "null"]},
    "activation_errors": {"type": "array", "items": {"type": "string", "minLength": 1}}
  },
  "allOf": [{
    "if": {"properties": {"status": {"const": "approved"}}},
    "then": {
      "properties": {
        "chinese_book_references": {"minItems": 2},
        "adobe_sources": {"minItems": 1},
        "print_sources": {"minItems": 1},
        "field_mapping_path": {"type": "string", "minLength": 1},
        "activation_errors": {"maxItems": 0}
      }
    }
  }],
  "additionalProperties": false
}
```

`trim-profile.schema.json` must require positive dimensions only when `status` is `approved`, and require `trim_mm`, `bleed_mm`, `binding`, and `evidence_id` to remain `null` for a candidate.

- [ ] **Step 4: Run contract tests**

Run the command from Step 2. Expected: all tests `PASS`.

- [ ] **Step 5: Commit**

```text
Enforce evidence before activating book templates

Constraint: Trim aliases cannot imply millimeter dimensions.
Confidence: high
Scope-risk: narrow
Tested: template evidence and trim profile contract tests
```

---

### Task 2: Implement Evidence Validation and Register Lulu A5

**Files:**
- Create: `ai/indesign_templates/__init__.py`
- Create: `ai/indesign_templates/evidence.py`
- Create: `references/templates/registry.json`
- Create: `references/templates/lulu-a5/evidence.json`
- Test: `tests/test_template_evidence.py`

- [ ] **Step 1: Add failing hash and gate tests**

```python
from pathlib import Path
import json
import tempfile
import unittest

from ai.indesign_templates.evidence import evaluate_evidence, verify_original


class EvidenceRuntimeTests(unittest.TestCase):
    def test_original_hash_is_recomputed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            artifact = root / "original.idml"
            artifact.write_bytes(b"original")
            record = {
                "status": "candidate",
                "original": {"relative_path": "original.idml", "sha256": "0" * 64},
                "chinese_book_references": [], "adobe_sources": [],
                "print_sources": [], "field_mapping_path": None
            }
            with self.assertRaisesRegex(ValueError, "SHA-256"):
                verify_original(root, record)

    def test_gate_returns_all_missing_requirements(self):
        errors = evaluate_evidence({
            "chinese_book_references": [], "adobe_sources": [],
            "print_sources": [], "field_mapping_path": None
        })
        self.assertEqual(4, len(errors))
```

- [ ] **Step 2: Run test and verify import failure**

Run:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_template_evidence -v
```

Expected: `FAIL` because `ai.indesign_templates.evidence` does not exist.

- [ ] **Step 3: Implement deterministic validation**

```python
from __future__ import annotations

import hashlib
from pathlib import Path


def evaluate_evidence(record: dict) -> list[str]:
    errors = []
    if len(record.get("chinese_book_references", [])) < 2:
        errors.append("requires two Chinese published-book references")
    if not record.get("adobe_sources"):
        errors.append("requires one Adobe source")
    if not record.get("print_sources"):
        errors.append("requires one print or trim source")
    if not record.get("field_mapping_path"):
        errors.append("requires reviewed field mapping")
    return errors


def verify_original(root: Path, record: dict) -> Path:
    relative = Path(record["original"]["relative_path"])
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("original path must stay under the repository")
    path = root / relative
    if not path.is_file():
        raise ValueError(f"original file is missing: {relative.as_posix()}")
    digest = hashlib.sha256(path.read_bytes()).hexdigest().upper()
    if digest != record["original"]["sha256"]:
        raise ValueError("original SHA-256 mismatch")
    return path


def can_activate(root: Path, record: dict) -> bool:
    verify_original(root, record)
    return record.get("status") == "approved" and not evaluate_evidence(record)
```

- [ ] **Step 4: Register the Lulu acquisition exactly**

`references/templates/lulu-a5/evidence.json` must use the recorded URL, ZIP path, and SHA from the design specification. Keep status `candidate` and all four activation errors; do not invent Chinese references or approve A5 as Chinese 32mo.

- [ ] **Step 5: Run tests and validate the registry**

Run:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_template_evidence -v
.\.venv\Scripts\python.exe scripts\validate_json.py references\templates\registry.json
```

Expected: tests `PASS`; registry JSON valid.

- [ ] **Step 6: Commit**

```text
Bind template evidence to immutable provider artifacts

Constraint: Lulu A5 is a structural reference, not an approved Chinese trim profile.
Confidence: high
Scope-risk: narrow
Tested: evidence hash and activation-gate tests
```

---

### Task 3: Add Three Candidate Trim Families Without Guessing Dimensions

**Files:**
- Create: `templates/trim-profiles/32k-standard.json`
- Create: `templates/trim-profiles/32k-large.json`
- Create: `templates/trim-profiles/16k-standard.json`
- Create: `ai/indesign_templates/trim.py`
- Test: `tests/test_trim_profiles.py`

- [ ] **Step 1: Add failing activation tests**

```python
from pathlib import Path
import unittest

from ai.indesign_templates.trim import load_trim_profile


ROOT = Path(__file__).resolve().parents[1]


class TrimRuntimeTests(unittest.TestCase):
    def test_first_release_contains_exactly_three_families(self):
        names = sorted(path.stem for path in (ROOT / "templates/trim-profiles").glob("*.json"))
        self.assertEqual(["16k-standard", "32k-large", "32k-standard"], names)

    def test_candidate_profile_cannot_compile(self):
        with self.assertRaisesRegex(ValueError, "not approved"):
            load_trim_profile(ROOT / "templates/trim-profiles/32k-large.json", require_approved=True)
```

- [ ] **Step 2: Run test and verify failure**

Run:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_trim_profiles -v
```

Expected: `FAIL` because the files and loader do not exist.

- [ ] **Step 3: Create intentional candidate records**

Each JSON must contain the exact family ID and display name, with `status: candidate`, all physical values `null`, and `activation_errors: ["missing exact evidence-backed dimensions"]`. Do not encode 130×184, 140×203, 145×210, 148×210, 185×260, or 210×297 until the corresponding provider/standard evidence is approved.

- [ ] **Step 4: Implement the loader**

```python
from __future__ import annotations

import json
from pathlib import Path

from ai.contracts import validate_data


def load_trim_profile(path: Path, *, require_approved: bool = False) -> dict:
    profile = json.loads(path.read_text(encoding="utf-8"))
    errors = validate_data(profile, "trim-profile")
    if errors:
        raise ValueError("invalid trim profile: " + "; ".join(errors))
    if require_approved and profile["status"] != "approved":
        raise ValueError(f"trim profile is not approved: {profile['trim_profile_id']}")
    return profile
```

- [ ] **Step 5: Run tests and commit**

Expected: trim tests `PASS`.

```text
Represent the three approved scope families without guessing sizes

Constraint: Physical dimensions require evidence records.
Confidence: high
Scope-risk: narrow
Tested: trim inventory and fail-closed loading tests
```

---

### Task 4: Build Semantic HTML and Markdown Content IR

**Files:**
- Create: `schemas/book-content-ir.schema.json`
- Create: `ai/indesign_templates/content_ir.py`
- Test: `tests/test_book_content_ir.py`

- [ ] **Step 1: Write parser tests**

```python
import unittest

from ai.indesign_templates.content_ir import parse_html


class ContentIRTests(unittest.TestCase):
    def test_semantic_blocks_ignore_css_coordinates(self):
        html = '''
        <html><body>
          <h2 style="position:absolute;left:99px">第一章 春归</h2>
          <p class="body">第一段。</p>
          <blockquote>引文。</blockquote>
          <time datetime="2026-08-17">2026年8月17日</time>
        </body></html>
        '''
        result = parse_html(html)
        self.assertEqual(
            ["chapter-title", "body", "quote", "date"],
            [block["type"] for block in result["blocks"]],
        )
        self.assertNotIn("99px", str(result))

    def test_script_and_style_content_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "script"):
            parse_html("<script>alert(1)</script><p>正文</p>")
```

- [ ] **Step 2: Run and verify failure**

Run:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.test_book_content_ir -v
```

Expected: missing-module `FAIL`.

- [ ] **Step 3: Implement a standard-library HTML parser**

Use `html.parser.HTMLParser`, reject `script`, `style`, `iframe`, and unknown active content, normalize whitespace, and map only `h1`, `h2`, `h3`, `p`, `blockquote`, `aside`, `time`, `address`, `figure`, `img`, and `figcaption`. Output must validate against `book-content-ir.schema.json`; CSS and DOM coordinates must never enter the IR.

Public API names and signatures are fixed as `parse_html(source: str) -> dict`, `parse_markdown(source: str) -> dict`, and `source_digest(source: str) -> str`.

- [ ] **Step 4: Run tests and commit**

```text
Normalize book content before it reaches InDesign

Rejected: Translate browser pixel positions to InDesign coordinates | layout belongs to templates.
Confidence: high
Scope-risk: moderate
Tested: semantic HTML and active-content rejection tests
```

---

### Task 5: Export Deterministic RTF With Stable Style Names

**Files:**
- Create: `ai/indesign_templates/rtf.py`
- Test: `tests/test_rtf_export.py`

- [ ] **Step 1: Add byte-equivalence and Unicode tests**

```python
import unittest

from ai.indesign_templates.rtf import compile_rtf


class RtfExportTests(unittest.TestCase):
    def test_same_ir_is_byte_identical(self):
        ir = {"blocks": [{"type": "chapter-title", "text": "第一章 春归"}, {"type": "body", "text": "正文。"}]}
        self.assertEqual(compile_rtf(ir), compile_rtf(ir))

    def test_style_names_are_stable(self):
        output = compile_rtf({"blocks": [{"type": "body", "text": "中文正文。"}]})
        self.assertIn(b"P-BD-01", output)
        self.assertIn(b"\\u", output)
```

- [ ] **Step 2: Run and verify missing compiler failure**

- [ ] **Step 3: Implement the RTF writer without a new dependency**

The writer must emit one stylesheet with these mappings:

```python
STYLE_NAMES = {
    "book-title": "P-TITLE",
    "chapter-title": "P-CH-TTL",
    "section-title": "P-SEC-TTL",
    "body": "P-BD-01",
    "quote": "P-QUOTE",
    "note": "P-NOTE",
    "date": "P-DATE",
    "signature": "P-SIGNATURE",
    "caption": "P-CAPTION",
}
```

Escape braces and backslashes; write non-ASCII code points as signed RTF `\uN?`; end every block with `\par`. Do not encode page geometry or fonts in RTF because the InDesign template owns them.

- [ ] **Step 4: Run tests and commit**

```text
Generate stable RTF for native InDesign placement

Constraint: The converter adds no third-party dependency.
Confidence: high
Scope-risk: moderate
Tested: deterministic bytes, Unicode, and style-name tests
```

---

### Task 6: Compile a Closed Build Manifest

**Files:**
- Create: `schemas/special-pages.schema.json`
- Create: `ai/indesign_templates/manifest.py`
- Test: `tests/test_indesign_manifest.py`

- [ ] **Step 1: Add gate and path tests**

```python
import unittest

from ai.indesign_templates.manifest import compile_manifest


class BuildManifestTests(unittest.TestCase):
    def test_unapproved_trim_profile_blocks_build(self):
        with self.assertRaisesRegex(ValueError, "not approved"):
            compile_manifest(
                project_root="project",
                trim_profile={"status": "candidate", "trim_profile_id": "TRIM-32K-LARGE"},
                content_profile={"status": "approved", "content_profile_id": "BODY-LIT-01"},
                body_rtf="body.rtf",
                special_pages={"pages": []},
            )

    def test_special_page_path_traversal_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "relative"):
            compile_manifest(
                project_root="project",
                trim_profile={"status": "approved", "trim_profile_id": "TRIM-X"},
                content_profile={"status": "approved", "content_profile_id": "BODY-X"},
                body_rtf="body.rtf",
                special_pages={"pages": [{"role": "cover", "mode": "full-page-image", "path": "../escape.tif"}]},
            )
```

- [ ] **Step 2: Implement closed path and status validation**

`compile_manifest()` must emit absolute normalized runtime paths only after every input path resolves under `project_root`, both profiles are approved, evidence hashes verify, and `special-pages.json` validates.

- [ ] **Step 3: Run tests and commit**

```text
Compile only approved template combinations

Constraint: Candidate profiles and escaping paths fail closed.
Confidence: high
Scope-risk: moderate
Tested: profile status and path containment tests
```

---

### Task 7: Add the Three Fixed JSX Executors

**Files:**
- Create: `skills/build-indesign-book/scripts/import_body.jsx`
- Create: `skills/build-indesign-book/scripts/apply_masters.jsx`
- Create: `skills/build-indesign-book/scripts/place_special_pages.jsx`
- Test: `tests/test_indesign_template_pipeline.py`

- [ ] **Step 1: Write static contract tests before JSX**

```python
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "build-indesign-book" / "scripts"


class JsxContractTests(unittest.TestCase):
    def test_body_script_uses_native_place_and_smart_reflow(self):
        text = (SCRIPTS / "import_body.jsx").read_text(encoding="utf-8")
        self.assertIn("place(", text)
        self.assertIn("smartTextReflow", text)
        self.assertIn("preserveFacingPageSpreads", text)
        self.assertNotIn("1000x1448", text)

    def test_master_script_uses_parent_pages_and_auto_page_numbers(self):
        text = (SCRIPTS / "apply_masters.jsx").read_text(encoding="utf-8")
        self.assertIn("appliedMaster", text)
        self.assertIn("AUTO_PAGE_NUMBER", text)

    def test_special_page_script_supports_only_two_modes(self):
        text = (SCRIPTS / "place_special_pages.jsx").read_text(encoding="utf-8")
        self.assertIn("full-page-image", text)
        self.assertIn("background-plus-text", text)
```

- [ ] **Step 2: Run and verify three missing-file failures**

- [ ] **Step 3: Implement `import_body.jsx`**

Required behavior:

1. Parse the build manifest JSON.
2. Open the approved template file.
3. Find the parent spread and its primary text frame by labels, not page coordinates.
4. Place the RTF with import options preserving styles.
5. Resolve conflicts using InDesign style definitions.
6. Enable Smart Text Reflow, limit it to primary text frames, preserve facing-page spreads, and disable automatic empty-page deletion for the first release.
7. Return JSON with source paragraphs, placed paragraphs, pages added, story IDs, and overset count.

- [ ] **Step 4: Implement `apply_masters.jsx`**

Required page-role map:

```javascript
var ROLE_TO_PARENT = {
    "body-left": "A-Body",
    "body-right": "A-Body",
    "body-first": "F-BodyFirst",
    "chapter-opener": "E-Chapter",
    "blank": "B-Blank",
    "full-bleed-image": "B-Blank"
};
```

Use parent-page automatic folios. Replace `BOOK_TITLE` and `CHAPTER_TITLE` placeholders only through labeled parent text frames. Hide parent items on chapter-openers, blanks, and full-bleed pages.

- [ ] **Step 5: Implement `place_special_pages.jsx`**

For `full-page-image`, place one image into a labeled full-page object-style frame. For `background-plus-text`, place the image on the background layer and fill only approved labeled text frames. Reject unknown modes, missing files, RGB/CMYK policy violations, insufficient effective PPI, and images that do not cover configured bleed.

- [ ] **Step 6: Run tests and commit**

```text
Drive native InDesign features through three fixed executors

Rejected: Generate one custom JSX file per page | parent pages and style mapping already solve repetition.
Confidence: medium
Scope-risk: broad
Tested: JSX static contracts and InDesign smoke fixtures
```

---

### Task 8: Add the CLI and COM Orchestrator

**Files:**
- Create: `skills/build-indesign-book/scripts/compile_book.py`
- Modify: `skills/build-indesign-book/scripts/build_indesign_book.py`
- Test: `tests/test_indesign_template_pipeline.py`

- [ ] **Step 1: Add compile-only and execution-order tests**

```python
import unittest
from unittest import mock

from skills_build_indesign_compile_book import run_pipeline


class PipelineTests(unittest.TestCase):
    def test_compile_only_writes_manifest_without_starting_indesign(self):
        runner = mock.Mock()
        result = run_pipeline("project.json", execute=False, runner=runner)
        self.assertEqual("compiled", result["status"])
        runner.assert_not_called()

    def test_execute_runs_three_scripts_in_fixed_order(self):
        calls = []
        run_pipeline("project.json", execute=True, runner=lambda script, manifest: calls.append(script) or {"status": "ok"})
        self.assertEqual(["import_body.jsx", "apply_masters.jsx", "place_special_pages.jsx"], calls)
```

- [ ] **Step 2: Implement orchestration**

CLI:

```powershell
python skills\build-indesign-book\scripts\compile_book.py `
  --project-root projects\sample `
  --source manuscript.html `
  --trim-profile templates\trim-profiles\32k-large.json `
  --content-profile templates\content-profiles\literary-standard.json `
  --special-pages special-pages.json `
  --output-dir build\indesign `
  --execute
```

Compile stages must be `parse → RTF → manifest → import body → apply masters → place special pages → preflight → save INDD → export IDML/PDF`. Reuse the existing COM bridge; do not duplicate credential, VBS, or InDesign launch logic.

- [ ] **Step 3: Run tests and commit**

```text
Expose one deterministic InDesign compilation command

Constraint: MCP and COM execute manifests but never choose layouts.
Confidence: high
Scope-risk: moderate
Tested: compile-only and fixed execution-order tests
```

---

### Task 9: Add an Evidence-Gated Integration Fixture

**Files:**
- Create: `tests/fixtures/indesign-template-pipeline/project/`
- Create: `tests/fixtures/indesign-template-pipeline/approved-evidence/`
- Test: `tests/test_indesign_template_pipeline.py`

- [ ] **Step 1: Create a synthetic approved fixture**

Use a tiny test-only IDML/INDD fixture generated by the test setup, two test-only Chinese-reference records, one Adobe URL, one print-source URL, and a reviewed field mapping. Label every record `fixture_only: true`; never reuse real provider originals in tests.

- [ ] **Step 2: Add offline end-to-end assertions**

The test must prove:

- HTML becomes the expected IR block sequence;
- IR becomes deterministic RTF;
- the manifest includes exactly one trim profile and one content profile;
- three JSX scripts are selected in fixed order;
- changing one original byte causes evidence verification failure;
- a candidate trim profile cannot reach COM execution.

- [ ] **Step 3: Add optional real-InDesign smoke test**

Gate the smoke test behind `RUN_INDESIGN_INTEGRATION=1`. When enabled on Windows, assert the produced document has zero overset, correct millimeter dimensions, native paragraph styles, parent-page folios, and only special-page graphics links.

- [ ] **Step 4: Commit**

```text
Prove the compiler without weakening the evidence gate

Constraint: Automated tests use synthetic originals, never provider assets.
Confidence: high
Scope-risk: moderate
Tested: offline pipeline and optional real-InDesign smoke test
```

---

### Task 10: Integrate Validation, Documentation, and Release Controls

**Files:**
- Modify: `scripts/validate_all.py`
- Modify: `skills/build-indesign-book/SKILL.md`
- Modify: `docs/图书生产Skills套件使用说明.md`
- Modify: `README.md`
- Test: `tests/test_indesign_template_pipeline.py`

- [ ] **Step 1: Add release-gate tests**

Assert `validate_all.SKILLS` still contains nine skills, the template registry validates, only three trim-family files exist, and every approved template evidence record has zero activation errors.

- [ ] **Step 2: Extend `validate_all.py`**

Add read-only steps:

```python
run_step("template evidence registry", [sys.executable, "scripts/validate_template_evidence.py"])
run_step("trim profile inventory", [sys.executable, "scripts/validate_trim_profiles.py"])
run_step("InDesign compiler tests", [sys.executable, "-m", "unittest", "tests.test_indesign_template_pipeline", "-v"])
```

Validation must pass when all three trim profiles remain candidates, but release output must state that zero production trim profiles are active. It must fail if any candidate is silently marked approved without complete evidence.

- [ ] **Step 3: Document the zero-token path and activation process**

Documentation must include the exact CLI, the two special-page modes, the three supported trim families, the evidence directory format, and a warning that a family alias never determines millimeter dimensions.

- [ ] **Step 4: Run focused validation**

```powershell
.\.venv\Scripts\python.exe -m unittest `
  tests.test_template_evidence `
  tests.test_trim_profiles `
  tests.test_book_content_ir `
  tests.test_rtf_export `
  tests.test_indesign_manifest `
  tests.test_indesign_template_pipeline -v
```

Expected: all focused tests `PASS`.

- [ ] **Step 5: Run existing unaffected workflow tests**

```powershell
.\.venv\Scripts\python.exe -m unittest `
  tests.test_personal_install `
  tests.test_router `
  tests.test_review `
  tests.test_book_flipbook `
  tests.test_indesign_build `
  tests.test_editable_indesign_build -v
```

Expected: all selected tests `PASS`.

- [ ] **Step 6: Run Skill validation**

```powershell
.\.venv\Scripts\python.exe `
  D:\migrate\.codex\skills\.system\skill-creator\scripts\quick_validate.py `
  skills\build-indesign-book
```

Expected: `Skill is valid!`

- [ ] **Step 7: Commit**

```text
Make reference-backed template compilation a release gate

Constraint: The first release may ship with candidate trim families but no falsely approved production templates.
Confidence: high
Scope-risk: moderate
Tested: compiler, workflow regression, and Skill validation suites
Not-tested: Provider-specific press output until an approved printer profile is supplied.
```

---

## Plan Self-Review

- Spec coverage: evidence gate, three trim families, 7×3 composition model, HTML semantic IR, Word/RTF mapping, Tagged Text-ready boundaries, INDT/IDML skeletons, three JSX scripts, COM execution, special-page modes, Token boundary, preflight, and fail-closed behavior are each assigned to a task.
- Scope control: first implementation may produce zero approved production templates; it must not invent physical dimensions to make a demo pass.
- Type consistency: `template-evidence`, `trim-profile`, `book-content-ir`, and `special-pages` schema names match the proposed loader and validation calls.
- Dependency control: RTF generation uses the Python standard library; no new package is introduced.
- Historical Windows limitation: the existing POSIX `O_NOFOLLOW` subsystem is not expanded by this plan and remains a separately documented platform issue.
