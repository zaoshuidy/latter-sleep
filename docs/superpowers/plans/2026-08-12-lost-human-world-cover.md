# 《失落人间》封面测试 Implementation Plan

> 2026-08-12 更新：Task 1—3 的分类、检索、案例与字体证据继续有效；Task 4 以后原“无字背景＋SVG 叠字”执行细节被精简方案替代。先按 `2026-08-12-cover-integrated-typography-minimal.md` 完成封面一体化文字能力，再回到案例字段和字体选择。

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 使用现有封面知识库和受控生图链，为文学小说《失落人间》完成两个克制的正封候选、案例与字体依据、可编辑文字层和可审计生成记录。

**Architecture:** 项目文件独立保存在 `projects/lost-human-world-cover/`，维护源知识库只读。已完成 50 条封面库验证与 5 本不同图书检索；用户完成案例字段和字体选择后，系统创建 selection、Prompt、生成授权和图像版本。正封使用 `integrated-typography` 生成已登记的书名／副标题／作者，并保留等值可编辑备份；文字不稳定时回退到无字底图。不执行 InDesign。

**Tech Stack:** Python 3.14、JSON Schema、现有 `ai.book_component_kb` production API、Pillow、Codex `imagegen`、HTML/SVG 可编辑文字层。

## Global Constraints

- 设计事实以 `docs/superpowers/specs/2026-08-12-lost-human-world-cover-design.md` 为唯一规格来源。
- 正封尺寸为 32 开 `145 × 210 mm`；当前不制作封底、书脊或勒口。
- 书名为《失落人间》，副标题为“在所有归途之外”，作者为“早睡的猫”，无出版社或品牌标志。
- 方向 A 为“不能合拢的边界”，方向 B 为“不属于任何一页”；两方向不得被解释成城市、乡村、道路或写实人物。
- 色彩限定为纸白、黑色结构与一点暗红；避免企业标志感和情节插图感。
- 封面知识库必须 `valid=true`、`status=available`、`record_count>=50`、`errors=[]`；检索结果必须恰好 5 本不同图书。
- 用户只可选择候选中 `field_scores > 0` 的字段；每方向选择 2—3 个不同 record。
- 字体身份、气质、字重、字距和题名结构必须在案例展示后由用户批准；字体限免费合法字体或用户方正会员可用字体。
- Prompt 只允许独立 `INTEGRATED_TEXT` 块中的书名、副标题和作者；禁止额外文字与机器信息，并保留三项可编辑备份。
- 未获得 selection ID + SHA 批准和独立、明确的实际生图授权前，不调用 `imagegen`。
- 案例仅作内部研究和字段借鉴，不复制具体图形、照片、原书文字、色值组合或完整封面。
- 工作区当前不是 Git 仓库；不得伪造 commit。每个任务以测试结果和 `shasum -a 256` 读回记录代替提交证据。

---

## File Map

### Core contract change

- Modify: `schemas/project-config.schema.json` — 增加真实的 `literary-fiction` 项目类别。
- Modify: `tests/test_contracts.py` — 锁定文学小说分类可验证，未知分类仍拒绝。

### Project-owned artifacts

- Create: `projects/lost-human-world-cover/README.md` — 人用项目索引、状态和审批门说明。
- Create: `projects/lost-human-world-cover/inputs/project.json` — 事实配置。
- Create: `projects/lost-human-world-cover/inputs/query.json` — 封面检索 query。
- Create: `projects/lost-human-world-cover/retrieval/retrieval-result.json` — 唯一一次正式检索结果。
- Create: `projects/lost-human-world-cover/retrieval/case-comparison.md` — 5 案例的字段证据、字体结构观察与版权边界。
- Create: `projects/lost-human-world-cover/retrieval/case-board.html` — 5 张真实本地资产的视觉选择板。
- Create: `projects/lost-human-world-cover/retrieval/typography-evidence.md` — 免费／方正候选字体的官方来源和使用边界。
- Create after user mapping: `projects/lost-human-world-cover/inputs/reference-selection-A.json`
- Create after user mapping: `projects/lost-human-world-cover/inputs/reference-selection-B.json`
- Create after user typography choice: `projects/lost-human-world-cover/inputs/typography-choice.json`
- Create after approval: `projects/lost-human-world-cover/inputs/design-genome-A.json`
- Create after approval: `projects/lost-human-world-cover/inputs/design-genome-B.json`
- Create after approval: `projects/lost-human-world-cover/inputs/output-spec-A.json`
- Create after approval: `projects/lost-human-world-cover/inputs/output-spec-B.json`
- Create after approval: `projects/lost-human-world-cover/prompts/cover-direction-A.json`
- Create after approval: `projects/lost-human-world-cover/prompts/cover-direction-B.json`
- Create after generation approval: `projects/lost-human-world-cover/payloads/generation-A.json`
- Create after generation approval: `projects/lost-human-world-cover/payloads/generation-B.json`
- Create after generation approval: `projects/lost-human-world-cover/approvals/generation-A.json`
- Create after generation approval: `projects/lost-human-world-cover/approvals/generation-B.json`
- Create after generation: `projects/lost-human-world-cover/generated/COVER-A-V001.png`
- Create after generation: `projects/lost-human-world-cover/generated/COVER-B-V001.png`
- Create after generation: `projects/lost-human-world-cover/versions/COVER-A-V001.json`
- Create after generation: `projects/lost-human-world-cover/versions/COVER-B-V001.json`
- Create after typography composition: `projects/lost-human-world-cover/overlays/COVER-A-V001.svg`
- Create after typography composition: `projects/lost-human-world-cover/overlays/COVER-B-V001.svg`
- Create after typography composition: `projects/lost-human-world-cover/previews/cover-comparison.html`
- Create after human selection: `projects/lost-human-world-cover/reviews/REVIEW-COVER-SELECTED.json`
- Create after human selection: `projects/lost-human-world-cover/promotions/PROMOTE-COVER-SELECTED.json`

### Project acceptance test

- Create: `tests/test_lost_human_world_cover_project.py` — 验证项目事实、检索闭合、无字 Prompt、overlay 值、文件哈希与最终版本。

---

### Task 1: Add truthful literary-fiction classification

**Files:**
- Modify: `schemas/project-config.schema.json`
- Modify: `tests/test_contracts.py`

**Interfaces:**
- Consumes: `ai.contracts.validate_data(data, "project-config") -> list[str]`
- Produces: `primary_category="literary-fiction"` 作为受控合法值；其他未知类别仍被拒绝。

- [ ] **Step 1: Write the failing contract test**

```python
def test_literary_fiction_category_is_supported(self):
    data = {
        "version": "1.0",
        "project_id": "BOOK-LOST-HUMAN-WORLD",
        "title": "失落人间",
        "mode": "template",
        "primary_category": "literary-fiction",
        "tags": ["double-displacement"],
        "confirmer": "用户",
        "page_size": "145mm × 210mm",
        "page_plan": {"fixed_pages": 1},
    }
    self.assertEqual([], validate_data(data, "project-config"))

def test_unknown_editorial_category_is_rejected(self):
    data = {
        "version": "1.0",
        "project_id": "BOOK-LOST-HUMAN-WORLD",
        "title": "失落人间",
        "mode": "template",
        "primary_category": "novel-anything",
        "tags": [],
        "confirmer": "用户",
        "page_plan": {"fixed_pages": 1},
    }
    self.assertTrue(validate_data(data, "project-config"))
```

- [ ] **Step 2: Run the focused test and confirm RED**

Run:

```bash
PYTHONPATH=. .venv/bin/python -m unittest \
  tests.test_contracts.ContractValidationTests.test_literary_fiction_category_is_supported \
  tests.test_contracts.ContractValidationTests.test_unknown_editorial_category_is_rejected -v
```

Expected: `literary-fiction` test fails because the enum does not contain it; unknown value test passes.

- [ ] **Step 3: Add the minimal schema enum value**

Add exactly one value under `primary_category.enum`:

```json
"literary-fiction"
```

Do not add a third production mode; this cover-only fixed artifact uses the existing `template` process mode and `fixed_pages=1`.

- [ ] **Step 4: Run focused and contract suites**

```bash
PYTHONPATH=. .venv/bin/python -m unittest tests.test_contracts -v
PYTHONPATH=. .venv/bin/python -m unittest tests.test_component_kb_contracts -v
```

Expected: all pass.

- [ ] **Step 5: Record task checkpoint**

```bash
shasum -a 256 schemas/project-config.schema.json tests/test_contracts.py
```

Expected: two hashes copied into the Task 1 entry of `projects/lost-human-world-cover/README.md` after that file is created in Task 2.

---

### Task 2: Create project truth, query, and the single formal retrieval result

**Files:**
- Create: `projects/lost-human-world-cover/README.md`
- Create: `projects/lost-human-world-cover/inputs/project.json`
- Create: `projects/lost-human-world-cover/inputs/query.json`
- Create: `projects/lost-human-world-cover/retrieval/retrieval-result.json`
- Create: `tests/test_lost_human_world_cover_project.py`

**Interfaces:**
- Consumes: `retrieve(component_root: Path, registry: Path, query: dict, limit: int) -> dict`
- Produces: project ID `BOOK-LOST-HUMAN-WORLD`; query ID `QUERY-COV-LOST-HUMAN-WORLD-0001`; one `status=available` retrieval containing exactly 5 distinct `book_case_id` values.

- [ ] **Step 1: Write project and query fixtures with apply_patch**

`inputs/project.json`:

```json
{
  "version": "1.0",
  "project_id": "BOOK-LOST-HUMAN-WORLD",
  "title": "失落人间",
  "mode": "template",
  "primary_category": "literary-fiction",
  "tags": [
    "double-displacement",
    "urban-alienation",
    "failed-homecoming",
    "symbolic-cover",
    "subtitle:在所有归途之外",
    "author:早睡的猫"
  ],
  "confirmer": "用户",
  "purpose": "为文学小说建立克制、开放、具有隐喻和象征意义的正封概念稿",
  "primary_readers": "当代中文文学读者",
  "page_size": "145mm × 210mm",
  "brand_profile": "lost-human-world",
  "page_plan": {"fixed_pages": 1}
}
```

`inputs/query.json`:

```json
{
  "schema_version": "1.0",
  "query_id": "QUERY-COV-LOST-HUMAN-WORLD-0001",
  "component_type": "cover",
  "field_targets": {
    "visual_strategy": ["abstract", "typography", "mixed"],
    "composition": ["whitespace", "asymmetric", "centered"],
    "title_zone": ["top", "center", "vertical", "distributed"],
    "color": ["米白", "白色", "浅灰米色", "低对比灰", "黑色", "红色"],
    "mood": ["克制", "疏离", "冷峻", "内省", "寂静", "哲思", "张力"],
    "cover_scope": ["front"],
    "book_category": ["literary-fiction"]
  },
  "selection_policy": {"max_results": 5, "diversity": "strict"}
}
```

- [ ] **Step 2: Write the fixture validation test**

```python
import json
import unittest
from pathlib import Path

from ai.contracts import validate_data

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "projects" / "lost-human-world-cover"


class LostHumanWorldCoverProjectTests(unittest.TestCase):
    def load(self, relative: str) -> dict:
        return json.loads((PROJECT / relative).read_text(encoding="utf-8"))

    def test_project_and_query_are_schema_valid_and_truthful(self):
        project = self.load("inputs/project.json")
        query = self.load("inputs/query.json")
        self.assertEqual([], validate_data(project, "project-config"))
        self.assertEqual([], validate_data(query, "book-component-retrieval-query"))
        self.assertEqual("literary-fiction", project["primary_category"])
        self.assertEqual("cover", query["component_type"])
        self.assertEqual(5, query["selection_policy"]["max_results"])
```

- [ ] **Step 3: Validate the production cover library**

```bash
.venv/bin/python scripts/book_component_kb/validate_library.py \
  --component-root knowledge/book-component-libraries/cover \
  --registry knowledge/book-component-libraries/source-registry.json \
  --required-count 50
```

Expected: exit 0 with `valid=true`, `status=available`, `record_count=50`, `errors=[]`.

- [ ] **Step 4: Execute formal retrieval exactly once**

```bash
.venv/bin/python scripts/book_component_kb/retrieve_references.py \
  --component-root knowledge/book-component-libraries/cover \
  --registry knowledge/book-component-libraries/source-registry.json \
  --query projects/lost-human-world-cover/inputs/query.json \
  --limit 5
```

Expected: exit 0 and one JSON object on stdout. Save that exact stdout through `apply_patch` to `retrieval/retrieval-result.json`; do not rerun with changed targets to curate preferred books.

- [ ] **Step 5: Extend the acceptance test with retrieval invariants**

```python
def test_retrieval_is_available_exactly_five_and_book_distinct(self):
    result = self.load("retrieval/retrieval-result.json")
    self.assertEqual([], validate_data(result, "book-component-retrieval-result"))
    self.assertEqual("available", result["status"])
    self.assertEqual("cover", result["component_type"])
    self.assertEqual("QUERY-COV-LOST-HUMAN-WORLD-0001", result["query_id"])
    self.assertEqual(5, len(result["candidates"]))
    self.assertEqual(5, len({row["book_case_id"] for row in result["candidates"]}))
```

- [ ] **Step 6: Run tests and record hashes**

```bash
PYTHONPATH=. .venv/bin/python -m unittest tests.test_lost_human_world_cover_project -v
shasum -a 256 \
  projects/lost-human-world-cover/inputs/project.json \
  projects/lost-human-world-cover/inputs/query.json \
  projects/lost-human-world-cover/retrieval/retrieval-result.json
```

Expected: tests pass; README records the command result and three hashes.

---

### Task 3: Present five real cases and obtain visual/typography mappings

**Files:**
- Create: `projects/lost-human-world-cover/retrieval/case-comparison.md`
- Create: `projects/lost-human-world-cover/retrieval/case-board.html`
- Create: `projects/lost-human-world-cover/retrieval/typography-evidence.md`
- Create after user decision: `projects/lost-human-world-cover/inputs/typography-choice.json`
- Modify: `tests/test_lost_human_world_cover_project.py`

**Interfaces:**
- Consumes: the five candidate rows and their production `records/*.json`.
- Produces: user mapping of 2—3 candidate record IDs per direction plus one `typography-choice.json` containing `font_family`, `source_type`, `source_url`, `title_structure`, `weight`, `tracking`, `subtitle_relation`, and `author_relation` for A and B.

- [ ] **Step 1: Resolve and verify every real local asset**

For each candidate, load its record from `knowledge/book-component-libraries/cover/records/`, resolve `asset.relative_path`, then verify with Pillow:

```python
from PIL import Image
with Image.open(asset_path) as image:
    image.verify()
```

Also recompute SHA-256 and require it to equal the record. Stop if any asset is missing, undecodable, or mismatched.

- [ ] **Step 2: Write the five-case evidence comparison**

For each case, record:

```text
record_id / book_case_id / 书名 / source_url / local asset
完整 component_profile
8 个字段各自的 indexed value / field_score / 可选或不可选
题名的可见结构观察（不猜字体身份）
只可借鉴项 / 必须排除项
internal-reference-only 权利说明
```

`field_scores == 0` 必须明确写“不可选”；材料或工艺只能使用 record 的确定证据。

- [ ] **Step 3: Verify current font availability from official sources**

只查字体官方站点或方正字库官方页面，在 `typography-evidence.md` 记录：字体名、官方 URL、免费或方正会员类别、可用范围、不确定项。不得因封面图片外观猜出原案例字体名。

- [ ] **Step 4: Build and visually inspect the case board**

`case-board.html` 同屏显示五张真实资产，逐张列出 ID、书名、可借字段、不可借字段；另为方向 A/B 展示题名结构建议，但不把案例原题名或原图形复制到项目封面。用本地浏览器查看一次，确认图片、中文和长字段没有溢出。

- [ ] **Step 5: Ask one consolidated non-visual question after the visual review**

一次收集：

1. 方向 A 选择的 2—3 个 record 及各自字段。
2. 方向 B 选择的 2—3 个 record 及各自字段。
3. A/B 各自的字体气质、题名结构、字重、字距与副标题/作者关系。

用户不需要填写 schema 状态或哈希。

- [ ] **Step 6: Persist the typography decision and test it**

`typography-choice.json` 必须为：

```json
{
  "project_id": "BOOK-LOST-HUMAN-WORLD",
  "directions": {
    "A": {
      "font_family": "用户批准的字体全名",
      "source_type": "free-official 或 fangzheng-membership",
      "source_url": "对应官方直达页",
      "title_structure": "用户批准的题名结构",
      "weight": "用户批准的字重",
      "tracking": "用户批准的字距",
      "subtitle_relation": "用户批准的副标题关系",
      "author_relation": "用户批准的作者关系"
    },
    "B": {
      "font_family": "用户批准的字体全名",
      "source_type": "free-official 或 fangzheng-membership",
      "source_url": "对应官方直达页",
      "title_structure": "用户批准的题名结构",
      "weight": "用户批准的字重",
      "tracking": "用户批准的字距",
      "subtitle_relation": "用户批准的副标题关系",
      "author_relation": "用户批准的作者关系"
    }
  }
}
```

The acceptance test asserts exact project ID, directions `A/B`, non-empty fields, official URLs, and allowed `source_type` values.

---

### Task 4: Convert user mappings into two draft selections and obtain ID + SHA approval

**Files:**
- Create: `projects/lost-human-world-cover/inputs/reference-selection-A.json`
- Create: `projects/lost-human-world-cover/inputs/reference-selection-B.json`
- Modify: `tests/test_lost_human_world_cover_project.py`

**Interfaces:**
- Consumes: Task 2 retrieval result and Task 3 user mapping.
- Produces: two schema-valid, Prompt-safe `status=draft` selections, each with 2—3 distinct records from the same retrieval.

- [ ] **Step 1: Write both draft selections using the user’s exact mapping**

Use IDs:

```text
SEL-COV-LOST-HUMAN-WORLD-A-0001
SEL-COV-LOST-HUMAN-WORLD-B-0001
```

For each selected record include all seven transfer fields. Positive text uses only “本项目”“项目题名长度”“本项目生命痕迹”等 Prompt-safe phrases. `exclude_fields` explicitly removes original book text, original concrete image, original geometry, original exact colors and unique combinations.

- [ ] **Step 2: Validate schemas and Prompt safety**

```bash
PYTHONPATH=. .venv/bin/python scripts/validate_json.py \
  book-component-reference-selection projects/lost-human-world-cover/inputs/reference-selection-A.json
PYTHONPATH=. .venv/bin/python scripts/validate_json.py \
  book-component-reference-selection projects/lost-human-world-cover/inputs/reference-selection-B.json
```

Then run:

```python
from ai.book_component_kb.prompts import validate_selection_prompt_safety
validate_selection_prompt_safety(project, selection_a)
validate_selection_prompt_safety(project, selection_b)
```

Expected: no exception; neither selection contains `失落人间`、`在所有归途之外` or `早睡的猫`.

- [ ] **Step 3: Add selection invariants to the acceptance test**

Assert each selection is draft, has 2—3 unique record IDs, uses only candidates from the retrieval, and every included field has score greater than zero for that record.

- [ ] **Step 4: Report full files and hashes, then stop**

```bash
shasum -a 256 \
  projects/lost-human-world-cover/inputs/reference-selection-A.json \
  projects/lost-human-world-cover/inputs/reference-selection-B.json
```

Show the user both complete JSON files, exact selection IDs, absolute paths and hashes. Do not approve them, build directions or compile Prompt until the user explicitly approves both ID + SHA pairs.

- [ ] **Step 5: Apply approval and revalidate**

After exact approval, change only `status` from `draft` to `approved`, rerun schema validation, recompute hashes and call:

```python
from ai.book_component_kb.prompts import validate_selection
validate_selection(selection_a, retrieval)
validate_selection(selection_b, retrieval)
```

Expected: both pass against the same retrieval result.

---

### Task 5: Compile two text-free production Prompts and request generation authorization

**Files:**
- Create: `projects/lost-human-world-cover/inputs/design-genome-A.json`
- Create: `projects/lost-human-world-cover/inputs/design-genome-B.json`
- Create: `projects/lost-human-world-cover/inputs/output-spec-A.json`
- Create: `projects/lost-human-world-cover/inputs/output-spec-B.json`
- Create: `projects/lost-human-world-cover/prompts/cover-direction-A.json`
- Create: `projects/lost-human-world-cover/prompts/cover-direction-B.json`
- Create: `projects/lost-human-world-cover/payloads/generation-A.json`
- Create: `projects/lost-human-world-cover/payloads/generation-B.json`
- Modify: `tests/test_lost_human_world_cover_project.py`

**Interfaces:**
- Consumes: approved selections and `typography-choice.json`.
- Produces: two reproducible `book-component-prompt` files and two generation payloads whose `referenced_image_paths` are empty unless the user separately supplies project-owned authorized references.

- [ ] **Step 1: Build direction genomes**

Both genomes use the approved record IDs only. Direction A’s grid character is `two non-closing structures with restrained asymmetric tension`; direction B’s is `misregistered boundaries with an unclaimed outer trace`. Color is:

```json
{"paper": "warm paper white", "ink": "near black", "accent": "single muted dark red trace"}
```

`fonts` is copied from the corresponding A/B entry of `typography-choice.json`; it is metadata for editable layout only.

- [ ] **Step 2: Build exact output specifications**

Direction A image content: two abstract near-black structural masses approach without closing; one tiny dark-red non-figurative trace remains in the unclaimed interval; no scene or recognizable object.

Direction B image content: two abstract misregistered black boundary systems create an ambiguous third absence; one tiny dark-red non-figurative trace remains outside all valid boundaries; no page, window, map or grid depiction.

Both output specs use:

```json
{
  "aspect_ratio": "145:210",
  "editable_text_overlay": ["title", "other_text", "author"],
  "editable_text_values": {
    "title": "失落人间",
    "other_text": "在所有归途之外",
    "author": "早睡的猫"
  }
}
```

Negative constraints include no readable text, no title/author/subtitle glyphs, no city, village, road, person, illness, death, grave, logo, watermark, copied case geometry or original case content.

- [ ] **Step 3: Compile through the production CLI**

```bash
.venv/bin/python scripts/book_component_kb/compile_prompt.py \
  --project projects/lost-human-world-cover/inputs/project.json \
  --genome projects/lost-human-world-cover/inputs/design-genome-A.json \
  --selection projects/lost-human-world-cover/inputs/reference-selection-A.json \
  --output-spec projects/lost-human-world-cover/inputs/output-spec-A.json \
  --output projects/lost-human-world-cover/prompts/cover-direction-A.json

.venv/bin/python scripts/book_component_kb/compile_prompt.py \
  --project projects/lost-human-world-cover/inputs/project.json \
  --genome projects/lost-human-world-cover/inputs/design-genome-B.json \
  --selection projects/lost-human-world-cover/inputs/reference-selection-B.json \
  --output-spec projects/lost-human-world-cover/inputs/output-spec-B.json \
  --output projects/lost-human-world-cover/prompts/cover-direction-B.json
```

- [ ] **Step 4: Test production recompilation and text separation**

The acceptance test calls `compile_component_prompt` again and deep-compares both committed dicts. It asserts the three real strings appear only in `editable_text_overlay`, never in `background_prompt`, `compiled_blocks`, or `negative_constraints`.

- [ ] **Step 5: Create payloads and request explicit authorization**

Each payload contains the exact compiled `background_prompt` and:

```json
"referenced_image_paths": []
```

Show the user both backgrounds, chosen case IDs, empty reference list, expected outputs `generated/COVER-A-V001.png` and `generated/COVER-B-V001.png`, and the fact that this action calls `imagegen`. Stop until the user explicitly authorizes A, B, or both.

---

### Task 6: Generate authorized backgrounds and create editable cover previews

**Files:**
- Create only for authorized directions: `approvals/generation-<DIRECTION>.json`
- Create only for authorized directions: `generated/COVER-<DIRECTION>-V001.png`
- Create only for authorized directions: `versions/COVER-<DIRECTION>-V001.json`
- Create only for authorized directions: `overlays/COVER-<DIRECTION>-V001.svg`
- Create: `previews/cover-comparison.html`
- Modify: `tests/test_lost_human_world_cover_project.py`

**Interfaces:**
- Consumes: compiled Prompt, approved selection, retrieval result, payload and explicit user generation approval through `validate_generation_bundle(...) -> GenerationExecutionBundle`.
- Produces: real raster background, draft version evidence, editable SVG typography overlay and browser comparison.

- [ ] **Step 1: Persist generation authorization**

Create one schema-valid authorization per authorized direction. Bind the exact selection/retrieval/Prompt/payload SHA values, `component_type=cover`, empty `referenced_images`, the exact output relative path, current approval date, and a `fee_action` that truthfully describes the actual tool action without inventing a price.

- [ ] **Step 2: Run path-based generation preflight**

Use `ProjectGenerationEvidencePaths` and `validate_generation_bundle(PROJECT_ROOT, paths)`; require the returned background to equal the committed payload and reference material list to be empty. Call `execution.verify()` immediately before image generation.

- [ ] **Step 3: Use the imagegen skill for authorized directions only**

Read `/Users/edy/.codex/skills/.system/imagegen/SKILL.md` completely in the generation turn. Pass only `execution.background_prompt`; do not pass editable overlay strings. Save each returned background to the authorized `generated/` leaf and call `execution.verify()` again before closing the bundle.

- [ ] **Step 4: Write real version evidence**

Decode the actual output, compute MIME/dimensions/SHA, and create `book-project-image-version` with `V001`, `status=draft`, selected record IDs and the five bound artifact hashes. Schema validation must pass.

- [ ] **Step 5: Compose editable typography without burning it into the background**

Create one SVG per authorized direction with a 145:210 viewBox, linked generated background, and three editable `<text>` elements for title, subtitle and author. Apply only the user-approved font family, weight, tracking and relationships from `typography-choice.json`; include no publisher mark. `cover-comparison.html` displays each SVG at print ratio and labels the direction.

- [ ] **Step 6: Visual and automated verification**

Inspect backgrounds and SVG previews. The test verifies output hashes, dimensions, version schema, exact editable strings in SVG, no editable strings in raster Prompt, and no missing local links.

Run:

```bash
PYTHONPATH=. .venv/bin/python -m unittest tests.test_lost_human_world_cover_project -v
.venv/bin/python scripts/validate_all.py
```

Expected: project tests and full suite pass; 7 Skills pass; cover library remains available at 50 records.

---

### Task 7: Human review, selected evidence, and proposal-only knowledge return

**Files:**
- Create after user picks an exact image/version/hash: `approvals/image-selection.json`
- Create: `reviews/REVIEW-COVER-SELECTED.json`
- Create: `promotions/PROMOTE-COVER-SELECTED.json`
- Modify: `projects/lost-human-world-cover/README.md`

**Interfaces:**
- Consumes: one user-selected V001 image, all project evidence, and seven review checks.
- Produces: project-local selected review and `status=proposed` / `human_approval=pending` / `target_lifecycle=accumulation` proposal; never writes the production KB.

- [ ] **Step 1: Present both final previews for human judgment**

Ask the user to judge restraint, ambiguity, absence of commercial-logo feel, typography fit, subtitle hierarchy, thumbnail recognition and whether the result avoids literal storytelling.

- [ ] **Step 2: Bind explicit image selection**

Only after the user identifies exact direction, image ID, version and image SHA, create `book-project-image-selection-approval`. If neither image is accepted, keep both `draft`; do not fabricate a selected review.

- [ ] **Step 3: Complete the seven-check review**

All checks must be based on the real image and evidence chain:

```text
no_unwanted_text
safe_zones_clear
genome_consistent
reference_transformed
print_crop_valid
truthfulness_valid
provenance_complete
```

Any false check blocks `selected`.

- [ ] **Step 4: Use production project review and promotion APIs**

Call `review_project_image` with the full `ProjectImageEvidencePaths`; then call `prepare_project_promotion` only if review status is selected. Both outputs are new-only project sidecars. The proposal stays pending and does not mutate `knowledge/book-component-libraries/`.

- [ ] **Step 5: Final readback and handoff**

Record absolute paths and SHA values for the design spec, retrieval result, selections, Prompts, backgrounds, versions, SVG previews, selected review and proposal. Rerun:

```bash
.venv/bin/python scripts/book_component_kb/validate_library.py \
  --component-root knowledge/book-component-libraries/cover \
  --registry knowledge/book-component-libraries/source-registry.json \
  --required-count 50
PYTHONPATH=. .venv/bin/python -m unittest discover -s tests -v
```

Expected: cover library remains unchanged and available; all tests pass; README accurately marks approvals and any rejected/draft direction.
