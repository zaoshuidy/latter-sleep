# Book Component Knowledge-Base Foundation and Cover Library Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the reusable four-component knowledge-base engine and deliver the first available Chinese cover-design library with 50 validated 2017—2026 cases, explainable five-book retrieval, reference mapping, text-free cover Prompt compilation, review, and knowledge promotion.

**Architecture:** Store one shared source registry and four physically isolated component libraries under `knowledge/book-component-libraries/`. Human-maintained source records and image assets are the source of truth; catalogues, categories, retrieval indexes, and manifests are deterministic derivatives. Implement the reusable engine first, validate it with fixtures, then collect the cover library in five reviewable batches of ten before integrating it into `design-book-editorial` and `create-book-images`.

**Tech Stack:** Python 3.14, JSON Schema Draft 2020-12, `jsonschema`, Pillow, standard-library `hashlib/json/pathlib`, `unittest`, Codex `imagegen`, existing Skill validators and release scripts.

## Global Constraints

- The approved design is `docs/superpowers/specs/2026-08-10-book-component-image-knowledge-bases-design.md`.
- V1 component libraries are exactly `cover`, `toc`, `chapter-opener`, and `illustration-decoration`.
- This plan implements shared infrastructure plus `cover`; it must not collect the other three libraries yet.
- The cover library requires exactly 50 valid Chinese book cases published from 2017 through 2026 inclusive.
- Every cover record uses a unique local image and a unique `book_case_id` within the cover library.
- Source mode is `accumulation`; authorization does not block V1 retrieval, but source URL, platform, collection date, and file SHA-256 are mandatory.
- Book title, author, publisher mark, spine text, and any other final readable text remain editable overlays and must not be generated into the cover background.
- The source manuscript and existing book-production records remain immutable.
- The supplied commercial archive is read-only and remains unchanged at SHA-256 `3941d5376afb0896c0689e725ba5f1a3b55ef63faae2feecf688d08632dad4ba`.
- No proofreading, copyright-page work, InDesign execution, PDF production, web frontend, or scheduled automation.
- Original and rejected assets are archived, never automatically deleted.
- The workspace is not a usable Git repository. Do not initialize Git. Use fresh tests and task checkpoint manifests instead of commits.

## Roadmap Boundary

This plan finishes the cover vertical slice. After its human acceptance, create three follow-up plans in order:

1. `toc` library, 50 cases.
2. `chapter-opener` library, 50 cases.
3. `illustration-decoration` library, 50 cases.

Each follow-up reuses the interfaces defined below and adds only its component profile, weights, 50 records, component Prompt tests, and Skill behavior evidence.

## File Map

### Shared engine

- Create `ai/book_component_kb/__init__.py`: public exports.
- Create `ai/book_component_kb/paths.py`: safe path resolution, hashes, and image metadata.
- Create `ai/book_component_kb/build.py`: deterministic derived-index and manifest builder.
- Create `ai/book_component_kb/validate.py`: full-chain integrity validator.
- Create `ai/book_component_kb/retrieve.py`: component scoring, diversity, and stable retrieval.
- Create `ai/book_component_kb/prompts.py`: approved-selection to component Prompt compiler.
- Create `ai/book_component_kb/review.py`: image review and promotion records.

### CLI entry points

- Create `scripts/book_component_kb/build_library.py`.
- Create `scripts/book_component_kb/validate_library.py`.
- Create `scripts/book_component_kb/retrieve_references.py`.
- Create `scripts/book_component_kb/compile_prompt.py`.
- Create `scripts/book_component_kb/review_image.py`.
- Create `scripts/book_component_kb/promote_image.py`.

### Contracts

- Create eight schemas under `schemas/`:
  - `book-component-reference-record.schema.json`
  - `book-component-source-registry.schema.json`
  - `book-component-retrieval-query.schema.json`
  - `book-component-retrieval-result.schema.json`
  - `book-component-reference-selection.schema.json`
  - `book-component-prompt.schema.json`
  - `book-component-image-review.schema.json`
  - `book-component-kb-promotion.schema.json`

### Knowledge base

- Create `knowledge/book-component-libraries/source-registry.json`.
- Create `knowledge/book-component-libraries/cover/records/` with `COV-CN-0001.json` through `COV-CN-0050.json`.
- Create `knowledge/book-component-libraries/cover/assets/` with one immutable source image per record.
- Generate `catalog.json`, `retrieval-index.json`, `manifest.json`, and `categories/*.json`.

### Tests and documentation

- Create `tests/fixtures/component-kb/` fixtures.
- Create six new test modules described task-by-task below.
- Modify `scripts/validate_all.py`.
- Modify `scripts/install_personal.py`.
- Modify `docs/Skill与知识库位置索引.md`.
- Create `docs/封面知识库采集与使用说明.md`.
- Update and behavior-test `design-book-editorial`, then deploy it before updating `create-book-images`.

---

### Task 1: Add the eight JSON contracts and fixtures

**Files:**
- Create: `schemas/book-component-reference-record.schema.json`
- Create: `schemas/book-component-source-registry.schema.json`
- Create: `schemas/book-component-retrieval-query.schema.json`
- Create: `schemas/book-component-retrieval-result.schema.json`
- Create: `schemas/book-component-reference-selection.schema.json`
- Create: `schemas/book-component-prompt.schema.json`
- Create: `schemas/book-component-image-review.schema.json`
- Create: `schemas/book-component-kb-promotion.schema.json`
- Create: `tests/fixtures/component-kb/source-registry.json`
- Create: `tests/fixtures/component-kb/cover-record.json`
- Create: `tests/test_component_kb_contracts.py`

**Interfaces:**
- Consumes: `ai.contracts.validate_data(data: dict, schema_name: str) -> list[str]`.
- Produces: eight schema names accepted by `validate_data`; canonical fixture IDs `BOOK-CN-0001`, `SER-CN-0001`, `COV-CN-0001`.

- [ ] **Step 1: Write failing schema tests**

```python
class ComponentKnowledgeContractsTests(unittest.TestCase):
    def test_cover_record_requires_real_source_asset_and_cover_profile(self):
        record = fixture("cover-record.json")
        self.assertEqual([], validate_data(record, "book-component-reference-record"))
        for field in ["identity", "source", "asset", "component_profile", "visual_decomposition", "reference_transfer", "retrieval_features", "lifecycle"]:
            broken = copy.deepcopy(record)
            del broken[field]
            self.assertTrue(validate_data(broken, "book-component-reference-record"), field)

    def test_final_text_is_an_editable_overlay(self):
        prompt = valid_component_prompt()
        self.assertEqual([], validate_data(prompt, "book-component-prompt"))
        prompt["generation_constraints"]["readable_text"] = "四时来信"
        self.assertTrue(validate_data(prompt, "book-component-prompt"))
```

- [ ] **Step 2: Run the tests and observe RED**

Run: `.venv/bin/python -m unittest tests.test_component_kb_contracts -v`  
Expected: FAIL because the eight schema files do not exist.

- [ ] **Step 3: Implement the schemas with closed fields**

The record schema must use `additionalProperties: false`, `component_type` enum `cover/toc/chapter-opener/illustration-decoration`, publication year integer `2017..2026`, and lifecycle status enum `accumulation/confirmed/archived`.

The cover profile must require:

```json
{
  "cover_scope": "front|full-wrap|dust-jacket|casebound|with-flaps",
  "visual_strategy": "image|typography|abstract|photography|illustration|mixed",
  "composition": "centered|asymmetric|full-bleed|whitespace|bordered|grid",
  "title_zone": "top|center|bottom|vertical|distributed",
  "spine_relationship": "independent|continuous|not-visible",
  "thumbnail_recognition": "strong|medium|weak"
}
```

Every observation must require `value`, `visibility`, `confidence`, `evidence`, and non-empty `content_tags`. A Prompt must require `generation_constraints.readable_text` to equal `none` and a non-empty `editable_text_overlay` object.

- [ ] **Step 4: Run GREEN and full contract regression**

Run: `.venv/bin/python -m unittest tests.test_component_kb_contracts tests.test_contracts -v`  
Expected: PASS.

- [ ] **Step 5: Create checkpoint**

Run: `.venv/bin/python scripts/hash_tree.py schemas --exclude __pycache__`  
Expected: JSON output containing all eight new schema hashes. Save the reviewed output as `tests/checkpoint-component-kb-task-01.sha256.json` using `apply_patch`.

### Task 2: Implement asset safety and record loading

**Files:**
- Create: `ai/book_component_kb/__init__.py`
- Create: `ai/book_component_kb/paths.py`
- Create: `tests/test_component_kb_paths.py`
- Modify: `requirements-dev.txt`

**Interfaces:**
- Produces: `sha256_file(path: Path) -> str`, `safe_relative_file(root: Path, relative: str) -> Path`, `read_image_metadata(path: Path) -> dict[str, int | str]`, `load_json(path: Path) -> dict`.

- [ ] **Step 1: Write failing path and image tests**

```python
def test_safe_relative_file_rejects_escape_and_symlink(self):
    with self.assertRaises(ValueError):
        safe_relative_file(self.root, "../outside.jpg")
    link = self.root / "linked.jpg"
    link.symlink_to(self.outside)
    with self.assertRaises(ValueError):
        safe_relative_file(self.root, "linked.jpg")

def test_image_metadata_reads_actual_bytes(self):
    meta = read_image_metadata(self.fixture_jpeg)
    self.assertEqual({"width": 8, "height": 12, "mime_type": "image/jpeg"}, meta)
```

- [ ] **Step 2: Run RED**

Run: `.venv/bin/python -m unittest tests.test_component_kb_paths -v`  
Expected: FAIL because `ai.book_component_kb.paths` does not exist.

- [ ] **Step 3: Add Pillow and minimal safe-path implementation**

Add `Pillow>=11,<13` to `requirements-dev.txt`. `safe_relative_file` must resolve under the supplied root, reject absolute paths, `..`, symlinks, directories, and missing files. `read_image_metadata` must use Pillow to verify decoded bytes and return actual dimensions/MIME.

- [ ] **Step 4: Install dependency and run GREEN**

Run: `.venv/bin/python -m pip install -r requirements-dev.txt`  
Run: `.venv/bin/python -m unittest tests.test_component_kb_paths -v`  
Expected: PASS.

- [ ] **Step 5: Run legacy safety tests**

Run: `.venv/bin/python -m unittest tests.test_legacy_migration tests.test_upstream_snapshot -v`  
Expected: PASS; no existing source-preservation behavior changes.

### Task 3: Build deterministic catalogues, categories, indexes, and manifests

**Files:**
- Create: `ai/book_component_kb/build.py`
- Create: `scripts/book_component_kb/build_library.py`
- Create: `tests/test_component_kb_build.py`

**Interfaces:**
- Consumes: a component root containing `records/`, `assets/`, plus the shared registry.
- Produces: `build_library(component_root: Path, registry_path: Path) -> dict[str, object]` and four derived JSON files.

- [ ] **Step 1: Write failing deterministic-build tests**

```python
def test_builder_derives_files_without_editing_records(self):
    before = sha256_file(self.record)
    result = build_library(self.cover_root, self.registry)
    self.assertEqual(before, sha256_file(self.record))
    self.assertEqual("building", result["status"])
    for name in ["catalog.json", "retrieval-index.json", "manifest.json"]:
        self.assertTrue((self.cover_root / name).is_file())

def test_second_build_is_byte_identical(self):
    build_library(self.cover_root, self.registry)
    first = hashes(self.cover_root)
    build_library(self.cover_root, self.registry)
    self.assertEqual(first, hashes(self.cover_root))
```

- [ ] **Step 2: Run RED**

Run: `.venv/bin/python -m unittest tests.test_component_kb_build -v`  
Expected: FAIL because `build_library` is missing.

- [ ] **Step 3: Implement the builder**

Rules:

- Sort records by `record_id`.
- Build cover categories `by-visual-strategy`, `by-composition`, `by-title-zone`, and `by-publication-year`.
- Catalogue entries contain only IDs, source registry ID, asset path/hash, component, year, lifecycle, and record hash.
- Retrieval index contains normalized closed fields, never free-form report text as evidence.
- Manifest binds the registry, every record, every asset, categories, catalogue, and retrieval index.
- Status is `building` for fewer than 50 valid records and `available` only at exactly 50 or more valid records.
- Write via sibling temporary files and `Path.replace`; never mutate records or assets.

- [ ] **Step 4: Run GREEN**

Run: `.venv/bin/python -m unittest tests.test_component_kb_build -v`  
Expected: PASS and identical hashes across two builds.

- [ ] **Step 5: Validate CLI behavior**

Run: `.venv/bin/python scripts/book_component_kb/build_library.py --help`  
Expected: documents required `--component-root` and `--registry` arguments; no implicit desktop paths.

### Task 4: Implement full-chain validation

**Files:**
- Create: `ai/book_component_kb/validate.py`
- Create: `scripts/book_component_kb/validate_library.py`
- Create: `tests/test_component_kb_validate.py`

**Interfaces:**
- Produces: `validate_library(component_root: Path, registry_path: Path, required_count: int = 50) -> dict` with `valid`, `status`, `record_count`, `errors`, `warnings`, and `counts`.

- [ ] **Step 1: Write corruption and diversity tests**

```python
def test_modified_asset_breaks_hash_chain(self):
    build_library(self.cover_root, self.registry)
    self.asset.write_bytes(b"changed")
    report = validate_library(self.cover_root, self.registry, required_count=1)
    self.assertFalse(report["valid"])
    self.assertIn("asset hash mismatch", " ".join(report["errors"]))

def test_duplicate_book_or_asset_is_rejected(self):
    report = validate_library(self.duplicate_root, self.registry, required_count=2)
    self.assertFalse(report["valid"])
    self.assertTrue(any("duplicate" in error for error in report["errors"]))
```

- [ ] **Step 2: Run RED**

Run: `.venv/bin/python -m unittest tests.test_component_kb_validate -v`  
Expected: FAIL because validator is missing.

- [ ] **Step 3: Implement validation phases**

Execute in this order: schema checks, safe paths, decoded image facts, source registry binding, record/asset uniqueness, year range, component match, derived index agreement, manifest hashes, count/status agreement. Do not rebuild automatically inside validation.

- [ ] **Step 4: Run GREEN**

Run: `.venv/bin/python -m unittest tests.test_component_kb_validate -v`  
Expected: PASS.

- [ ] **Step 5: Confirm controlled building status**

Run validator against the single-record fixture with `--required-count 50`.  
Expected: exit code 2, JSON `valid=true`, `status=building`, `record_count=1`; integrity is valid but availability is not claimed.

### Task 5: Implement explainable cover retrieval

**Files:**
- Create: `ai/book_component_kb/retrieve.py`
- Create: `scripts/book_component_kb/retrieve_references.py`
- Create: `tests/test_component_kb_retrieve.py`

**Interfaces:**
- Consumes: validated `book-component-retrieval-query` and available component library.
- Produces: `retrieve(component_root: Path, registry_path: Path, query: dict, limit: int = 5) -> dict` conforming to `book-component-retrieval-result`.

- [ ] **Step 1: Write failing retrieval tests**

```python
def test_cover_retrieval_returns_five_different_books_with_reasons(self):
    result = retrieve(self.cover_root, self.registry, self.query, limit=5)
    self.assertEqual("available", result["status"])
    self.assertEqual(5, len(result["candidates"]))
    self.assertEqual(5, len({item["book_case_id"] for item in result["candidates"]}))
    self.assertTrue(all(item["field_scores"] and item["match_explanation"] for item in result["candidates"]))

def test_retrieval_never_repeats_to_fill_shortage(self):
    with self.assertRaisesRegex(ValueError, "five different books"):
        retrieve(self.four_book_root, self.registry, self.query, limit=5)
```

- [ ] **Step 2: Run RED**

Run: `.venv/bin/python -m unittest tests.test_component_kb_retrieve -v`  
Expected: FAIL because retriever is missing.

- [ ] **Step 3: Implement normalized weighted scoring**

Cover weights:

```python
COVER_WEIGHTS = {
    "visual_strategy": 0.20,
    "composition": 0.20,
    "title_zone": 0.15,
    "color": 0.15,
    "material": 0.10,
    "mood": 0.10,
    "cover_scope": 0.05,
    "book_category": 0.05,
}
```

Normalize Unicode with NFKC and lowercase. Missing or uncertain observations receive zero, never negative. Sort by descending total score then `record_id`. Filter to one candidate per `book_case_id`, then take exactly five.

- [ ] **Step 4: Run GREEN and determinism tests**

Run: `.venv/bin/python -m unittest tests.test_component_kb_retrieve -v`  
Expected: PASS; two identical queries return byte-equivalent JSON.

- [ ] **Step 5: Verify no cross-component retrieval**

Add a `toc` fixture to the cover root and assert the validator/retriever rejects it rather than silently filtering a malformed library.

### Task 6: Implement reference selection and text-free Prompt compilation

**Files:**
- Create: `ai/book_component_kb/prompts.py`
- Create: `scripts/book_component_kb/compile_prompt.py`
- Create: `tests/test_component_kb_prompts.py`

**Interfaces:**
- Produces: `validate_selection(selection: dict, retrieval_result: dict) -> None` and `compile_component_prompt(project: dict, genome: dict, selection: dict, output_spec: dict) -> dict`.

- [ ] **Step 1: Write failing mapping and text-boundary tests**

```python
def test_selection_requires_two_or_three_retrieved_records_with_distinct_roles(self):
    with self.assertRaisesRegex(ValueError, "2 or 3"):
        validate_selection(one_reference_selection(), self.retrieval)

def test_cover_prompt_has_fixed_blocks_and_no_final_text(self):
    prompt = compile_component_prompt(self.project, self.genome, self.selection, self.output_spec)
    self.assertEqual(EXPECTED_BLOCK_ORDER, list(prompt["compiled_blocks"]))
    self.assertEqual("none", prompt["generation_constraints"]["readable_text"])
    self.assertEqual("editable-text-layer", prompt["editable_text_overlay"]["title"])
```

- [ ] **Step 2: Run RED**

Run: `.venv/bin/python -m unittest tests.test_component_kb_prompts -v`  
Expected: FAIL because compiler is missing.

- [ ] **Step 3: Implement the compiler**

Fixed block order:

```python
EXPECTED_BLOCK_ORDER = (
    "PROJECT_TRUTH", "COMPONENT_ROLE", "DESIGN_GENOME",
    "REFERENCE_TRANSFERS", "COMPOSITION", "IMAGE_CONTENT",
    "COLOR_LIGHT_MATERIAL", "EDITABLE_TEXT_SAFE_ZONES",
    "PRINT_AND_CROP", "NEGATIVE", "OUTPUT_SPEC",
)
```

Require every reference line to include record ID, allowed fields, existing baseline, adjustment, preserved elements, required changes, and excluded fields. Reject a requested final title, author, publisher, spine text, page number, or other readable text in generated pixels.

- [ ] **Step 4: Run GREEN**

Run: `.venv/bin/python -m unittest tests.test_component_kb_prompts tests.test_image_records -v`  
Expected: PASS; the existing cover Prompt contract remains valid.

- [ ] **Step 5: Verify CLI emits sidecar JSON only**

Run compiler against fixtures and verify it writes `cover-prompt.json` without invoking `imagegen` or creating an image.

### Task 7: Implement review and knowledge promotion records

**Files:**
- Create: `ai/book_component_kb/review.py`
- Create: `scripts/book_component_kb/review_image.py`
- Create: `scripts/book_component_kb/promote_image.py`
- Create: `tests/test_component_kb_review.py`

**Interfaces:**
- Produces: `review_image(input_record: dict) -> dict` and `prepare_promotion(review: dict, source_image: Path, target_component: str) -> dict`.

- [ ] **Step 1: Write failing gate tests**

```python
def test_rejected_or_unselected_image_cannot_be_promoted(self):
    for status in ["draft", "archived", "rejected"]:
        with self.assertRaisesRegex(ValueError, "selected"):
            prepare_promotion(review(status=status), self.image, "cover")

def test_selected_image_still_requires_human_kb_approval(self):
    candidate = prepare_promotion(review(status="selected"), self.image, "cover")
    self.assertEqual("pending", candidate["human_approval"])
    self.assertEqual("accumulation", candidate["target_lifecycle"])
```

- [ ] **Step 2: Run RED**

Run: `.venv/bin/python -m unittest tests.test_component_kb_review -v`  
Expected: FAIL because review module is missing.

- [ ] **Step 3: Implement review checks**

Require explicit booleans for `no_unwanted_text`, `safe_zones_clear`, `genome_consistent`, `reference_transformed`, `print_crop_valid`, `truthfulness_valid`, and `provenance_complete`. Any false check prevents `selected`. Promotion is always a proposal with human approval `pending`; the script never writes into the library directly.

- [ ] **Step 4: Run GREEN**

Run: `.venv/bin/python -m unittest tests.test_component_kb_review -v`  
Expected: PASS.

### Task 8: Integrate engine checks into the release validator

**Files:**
- Modify: `scripts/validate_all.py`
- Create: `tests/test_validate_all_component_kb.py`

**Interfaces:**
- Consumes: component library validator CLI.
- Produces: release validation that reports each component as `missing`, `building`, or `available`; only cover must be `available` at this plan's final checkpoint.

- [ ] **Step 1: Write failing integration test**

Assert the validator command list includes `validate_library.py` for `cover` with `--required-count 50`, and that final validation fails if the cover library is `building`.

- [ ] **Step 2: Run RED**

Run: `.venv/bin/python -m unittest tests.test_validate_all_component_kb -v`  
Expected: FAIL because `validate_all.py` does not know component libraries.

- [ ] **Step 3: Add explicit cover validation**

Do not require the other three libraries yet. Print them as `planned` based on the roadmap, not `available`.

- [ ] **Step 4: Run GREEN against fixtures**

Use dependency injection or a temporary fixture path in the unit test; do not weaken the production path `knowledge/book-component-libraries/cover`.

### Task 9: Create the source registry, cover skeleton, and collection protocol

**Files:**
- Create: `knowledge/book-component-libraries/source-registry.json`
- Create directory: `knowledge/book-component-libraries/cover/records/`
- Create directory: `knowledge/book-component-libraries/cover/assets/`
- Create directory: `knowledge/book-component-libraries/cover/categories/`
- Create: `docs/封面知识库采集与使用说明.md`

**Interfaces:**
- Produces: canonical source IDs `SRC-CN-0001..0050` and record IDs `COV-CN-0001..0050` as entries are accepted.

- [ ] **Step 1: Write collection acceptance checks in documentation**

Each collected item must satisfy: Chinese book design, publication year 2017—2026, visible cover, source URL, platform, collected date, book title, designer when stated, publisher when stated, readable local image, unique image SHA, and unique `book_case_id` for the cover library. Unknown designer/publisher values are `null`, never invented.

- [ ] **Step 2: Create the empty registry and library directories**

Set registry version `1.0`, source mode `accumulation`, and empty `sources`. Build and validation must return valid `building`, count 0.

- [ ] **Step 3: Document acquisition priority**

Use official Chinese book-design awards and institutions first, publishers/design studios second, professional media/exhibitions third, and social discovery only for remaining diversity gaps. Preserve direct page URL and original downloaded bytes.

- [ ] **Step 4: Run skeleton validation**

Expected: `valid=true`, `status=building`, `record_count=0`, availability exit code 2.

### Task 10: Collect and validate cover cases 001—010 from official sources

**Files:**
- Create: `knowledge/book-component-libraries/cover/records/COV-CN-0001.json` through `COV-CN-0010.json`
- Create: ten matching files under `knowledge/book-component-libraries/cover/assets/`
- Modify: `knowledge/book-component-libraries/source-registry.json`

- [ ] **Step 1: Search official 2017—2026 Chinese publication/design award sources**

Use web research and preserve the direct case URL for every book. Do not use a search-results URL as provenance.

- [ ] **Step 2: Save original image bytes and compute facts**

Do not re-encode. Record actual MIME, width, height, aspect ratio, and SHA-256 from the saved file.

- [ ] **Step 3: Create ten records from visible evidence only**

Every observation needs evidence from the current cover image. Do not infer print finishes that are not visibly documented.

- [ ] **Step 4: Build and validate**

Expected: valid `building`, 10 records, 10 unique assets, 10 unique books, zero errors.

- [ ] **Step 5: Human batch review**

Show a compact contact sheet or index with book title, year, source, visual strategy, and asset. Do not continue to Task 11 until the batch is accepted.

### Task 11: Collect and validate cover cases 011—020 from publishers

**Files:**
- Create: records `COV-CN-0011..0020` and ten assets.
- Modify: source registry and derived files.

- [ ] Search Chinese publisher project/catalogue pages dated 2017—2026.
- [ ] Reject duplicate book IDs and asset hashes against cases 001—010.
- [ ] Record only stated designer/publisher facts; use `null` for unstated designer.
- [ ] Build and validate: expected 20 unique books, status `building`, zero errors.
- [ ] Present batch for human acceptance before Task 12.

### Task 12: Collect and validate cover cases 021—030 from Chinese design studios and designers

**Files:**
- Create: records `COV-CN-0021..0030` and ten assets.
- Modify: source registry and derived files.

- [ ] Search designers' or studios' own project pages for Chinese books dated 2017—2026.
- [ ] Prefer cases adding underrepresented visual strategies, years, and cover scopes.
- [ ] Record visible cover evidence separately from surrounding project-description claims.
- [ ] Build and validate: expected 30 unique books, status `building`, zero errors.
- [ ] Present batch for human acceptance before Task 13.

### Task 13: Collect and validate cover cases 031—040 from professional media and exhibitions

**Files:**
- Create: records `COV-CN-0031..0040` and ten assets.
- Modify: source registry and derived files.

- [ ] Search Chinese professional publishing/design media, exhibitions, and institutional showcases.
- [ ] Preserve original URLs and distinguish publication year from article/display year.
- [ ] Add cases only when book publication year is within 2017—2026.
- [ ] Build and validate: expected 40 unique books, status `building`, zero errors.
- [ ] Present batch for human acceptance before Task 14.

### Task 14: Collect and validate cover cases 041—050 as diversity gap fill

**Files:**
- Create: records `COV-CN-0041..0050` and ten assets.
- Modify: source registry and derived files.

- [ ] Generate a coverage report by year, visual strategy, composition, title zone, publisher, and designer.
- [ ] Fill gaps from primary sources; if social discovery is necessary, use the existing `scrape` or `xhs-benchmark` Skill and preserve the discovered direct post URL.
- [ ] Reject cases that merely duplicate an already dominant visual pattern.
- [ ] Build and validate: expected `available`, 50 records/assets/books, zero errors.
- [ ] Present the complete 50-cover index for human acceptance.

### Task 15: Run the cover retrieval and Prompt end-to-end sample

**Files:**
- Create: `examples/component-kb-cover-demo/project.json`
- Create: `examples/component-kb-cover-demo/query.json`
- Generate: `examples/component-kb-cover-demo/retrieval-result.json`
- Create after human selection: `examples/component-kb-cover-demo/reference-selection-A.json`
- Create after human selection: `examples/component-kb-cover-demo/reference-selection-B.json`
- Generate: two direction Prompt JSON files under `examples/component-kb-cover-demo/prompts/`
- Create: `tests/test_component_kb_cover_e2e.py`

- [ ] **Step 1: Write failing end-to-end test**

Assert: five candidates from different books, selection contains 2—3 retrieved records, two directions share the same project truth, compiled cover backgrounds contain no readable text, and editable overlays contain title/author/studio mark.

- [ ] **Step 2: Run RED before creating example outputs**

Expected: missing retrieval and Prompt artifacts.

- [ ] **Step 3: Retrieve against a real project brief**

Use the existing `four-seasons-letters` real title/chapter facts only; do not invent body copy. The query may request a restrained documentary direction and a warm memory direction.

- [ ] **Step 4: Human reference-mapping gate**

Show five real candidates and ask the user to select 2—3 per direction with explicit field roles. Do not compile Prompts before approval.

- [ ] **Step 5: Compile two text-free cover Prompts and run GREEN**

Do not invoke `imagegen` during automated tests. A real image generation demonstration is a separate human-authorized action after Prompt approval.

### Task 16: Update and behavior-test `design-book-editorial`

**Files:**
- Modify: `skills/design-book-editorial/SKILL.md`
- Create: `skills/design-book-editorial/references/component-knowledge-retrieval.md`
- Create: `tests/skill-behavior/design-book-editorial/component-kb-baseline.md`
- Create: `tests/skill-behavior/design-book-editorial/component-kb-with-skill.md`

**Interfaces:**
- Consumes: `book-component-retrieval-query/result/selection`.
- Produces: two design directions whose cover reference recipes point to real record IDs.

- [ ] Run a fresh baseline agent without the updated Skill using a pressure case that tempts it to use generic web inspiration or mix cover/TOC records.
- [ ] Record the baseline answer verbatim.
- [ ] Add the minimum Skill guidance: validate the component library, retrieve exactly five, show real images, require 2—3 mapped selections, and bind selected records into each direction.
- [ ] Run the same scenario with the updated Skill and record compliance.
- [ ] Run `quick_validate.py` and the complete test suite.
- [ ] Package and deploy this Skill update before touching `create-book-images`, as required by `writing-skills`.

### Task 17: Update and behavior-test `create-book-images`

**Files:**
- Modify: `skills/create-book-images/SKILL.md`
- Create: `skills/create-book-images/references/component-prompt-pipeline.md`
- Create: `tests/skill-behavior/create-book-images/component-kb-baseline.md`
- Create: `tests/skill-behavior/create-book-images/component-kb-with-skill.md`

**Interfaces:**
- Consumes: approved component selection and `book-component-prompt`.
- Produces: image manifest entry, sidecar Prompt, output version, review, and optional promotion proposal.

- [ ] Run a baseline pressure scenario that tempts the agent to generate cover text into pixels, omit record IDs, and auto-promote its own output.
- [ ] Record the baseline verbatim.
- [ ] Add minimal guidance linking the compiler, `imagegen`, review checklist, and human promotion gate.
- [ ] Re-run with the updated Skill and verify it keeps final text editable and promotion pending.
- [ ] Run `quick_validate.py`, all tests, package, and deploy.

### Task 18: Update indexes, documentation, release, and installed runtime

**Files:**
- Modify: `scripts/install_personal.py`
- Modify: `docs/Skill与知识库位置索引.md`
- Modify: `docs/图书生产Skills套件使用说明.md`
- Modify: `RELEASE-MANIFEST.json` via package script.
- Update: `/Users/edy/.codex/book-production-skills-v1/LOCATION-INDEX.json` via installer.

- [ ] Add location-index entries for source registry, cover library root, cover manifest, cover records, and cover assets.
- [ ] Add a test that every indexed knowledge path exists after personal installation.
- [ ] Run `.venv/bin/python scripts/validate_all.py`; expected all tests, seven Skill validators, cover availability, case coverage, and upstream integrity pass.
- [ ] Run `.venv/bin/python scripts/package_release.py --replace`.
- [ ] Run `python3 scripts/install_personal.py --replace`.
- [ ] Run the installed runtime's `scripts/validate_all.py` from `/Users/edy/Desktop/book`.
- [ ] Verify the release ZIP with `unzip -t`, compare its SHA-256 with the checksum file, and recheck both supplied source ZIP hashes.
- [ ] Deliver the 50-cover index, validation report, sample retrieval/Prompt artifacts, updated Skill paths, release ZIP, and known boundaries.

## Final Acceptance Checklist

- [ ] The shared engine has RED/GREEN evidence for schemas, paths, build, validation, retrieval, Prompt, review, and promotion.
- [ ] Cover library contains exactly 50 unique local images, records, and `book_case_id` values.
- [ ] All cover cases are Chinese book designs published 2017—2026.
- [ ] Cover manifest and all derived indexes match source records and assets.
- [ ] Retrieval returns exactly five different books in stable order with explanations.
- [ ] Two sample directions bind explicit reference roles and generate no final readable text.
- [ ] Both modified Skills have baseline and with-Skill behavior evidence and pass validation.
- [ ] Personal runtime location index resolves the new knowledge paths.
- [ ] Release package integrity and SHA-256 pass.
- [ ] The other three libraries remain planned, not falsely marked available.
