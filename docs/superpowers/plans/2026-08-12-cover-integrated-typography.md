# 图书封面一体化文字生成 Implementation Plan

> 状态：已由用户于 2026-08-12 要求精简；本文件保留为工程分析记录，实际执行改用 `2026-08-12-cover-integrated-typography-minimal.md`。

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在保留现有无字背景模式的前提下，为 `cover` 增加可审计的一体化文字生成能力，使正封、封底和书脊能够生成项目已确认文字，同时绝对禁止 ISBN、条码、二维码、定价、CIP 和其他机器识别信息进入像素。

**Architecture:** 新能力采用双模式合同：旧输入缺少模式字段时仍按 `editable-overlay` 执行；只有 `component_type=cover` 且显式选择 `integrated-typography` 时，编译器才接受结构化 `integrated_text`。文字事实从项目配置进入 output spec，经 Prompt、generation payload、generation authorization 和 version 哈希链绑定；生成后通过新增文字审核项逐字、逐表面验收。机器识别信息在 schema、编译器、付费前 preflight、审核与 Skill 指南五层 fail closed。

**Tech Stack:** Python 3.14、JSON Schema Draft 2020-12、现有 `ai.book_component_kb` compiler/evidence chain、`unittest`、Codex `imagegen`、个人安装脚本。

## 需求理解与成功标准

- 业务场景：文学小说等封面需要文字形态与图像、留白和结构共同构图，纯后期 overlay 无法表达完整设计意图。
- 输入：项目结构化文字、已批准的案例字段映射、设计 genome、封面 output spec、真实检索和审批证据。
- 输出：可复现的 integrated-typography Prompt、受授权生成 payload、带准确文字的封面图、可编辑文字备份、人工审核和待晋升 proposal。
- 成功标准：
  1. 旧无字 Prompt、项目和测试零回归。
  2. 仅 cover 可启用一体化文字，toc／章首页／插图仍拒绝。
  3. 只有登记过的正封／封底／书脊项目文字能够进入生成指令。
  4. ISBN、条码、二维码、定价、CIP 等无论放在哪个字段都被拒绝。
  5. Prompt、payload、authorization、version 和 review 对文字清单形成闭合绑定。
  6. 任一错字、漏字、多字、表面串位、不可辨认或机器标识出现，都不能成为 `selected`，也不能产生 promotion proposal。
  7. 《失落人间》以正封三项文字完成首个真实项目验证，封底和书脊本轮保持空白。

## 技术影响与方案选择

- 前端：本阶段无网页前端改动；项目 HTML 选择板只作为人工审批界面，后续 Agent Web 系统再消费相同合同。
- 后端／AI：修改 Prompt compiler、生成前证据链、review/promotion 校验；不改变知识库检索算法和 50 条封面库。
- 数据库：无数据库；JSON sidecar 是唯一事实源，继续使用项目内 new-only 原子文件。
- 权限：实际 `imagegen` 仍需单独明确授权；本计划实施与测试不调用付费生图。
- 部署：先在维护源完成和独立复核，再通过受管安装脚本更新个人安装副本。
- 快速方案（不采用）：直接删除文字守卫。无法区分项目文字、案例文字、幻觉文字与机器标识。
- 工程方案（采用）：双模式、结构化文字、闭合哈希链、多阶段验证、可编辑备份。
- 长期方案：网页 Agent 用同一 schema 呈现文字表面、角色、审核差异和人工批准，不另造一套合同。

## 全局约束

- 唯一设计规格：`docs/superpowers/specs/2026-08-12-cover-integrated-typography-design.md`。
- 现有 `editable-overlay` 是默认且兼容模式；不能要求旧 Prompt 补写新字段。
- `integrated-typography` 只允许 `component_type=cover`。
- 表面枚举只有 `front`、`back`、`spine`；一个条目只能属于一个表面。
- 允许角色：
  - front：`title`、`subtitle`、`author`、`short-note`
  - back：`back-cover-copy`、`recommendation`、`short-note`
  - spine：`title`、`author`、`short-note`
- `integrated_text` 的每个 `text_id + value` 必须在 `editable_text_backup` 中精确存在；ID 和规范化后的值不得重复。
- 禁止角色至少包括 `isbn`、`barcode`、`qr-code`、`price`、`cip`、`book-number`、`machine-identifier`。
- 禁止内容扫描必须覆盖：ISBN-10/13 及有无连字符／空格形式、ISBN 标签、条码／barcode、二维码／QR code、定价／售价／价格、人民币或货币金额、CIP、书号、发行编号、机器码。
- 不得因字段名为 `title`、`other_text`、`short-note`，或因文字被放入自由 Prompt，而绕过机器信息禁令。
- 案例原书名、原作者、原出版社、案例宣传语和模型自行编造文案继续禁止。
- `toc`、`chapter-opener`、`illustration-decoration` 的正文、目录项、页码、页眉页脚仍只使用可编辑文字层。
- 生成适配器只能消费经过 preflight 冻结的 Prompt 和授权引用 bytes，不能重新从可变路径读取或追加自由文字。
- 知识库维持只读：50 条 records/assets/manifest 不因本能力更新发生字节变化。
- 当前工作区没有 Git 元数据；不得伪造 commit。每个任务用测试结果与 SHA-256 清单做检查点。

## File Map

### Contracts

- Modify: `schemas/project-config.schema.json`
- Modify: `schemas/book-component-prompt.schema.json`
- Modify: `schemas/book-project-image-generation-payload.schema.json`
- Modify: `schemas/book-component-image-review.schema.json`
- Create: `schemas/book-component-integrated-text-entry.schema.json`

### AI implementation

- Create: `ai/book_component_kb/integrated_text.py`
- Modify: `ai/book_component_kb/prompts.py`
- Modify: `ai/book_component_kb/review.py`

### Skill documentation

- Modify: `skills/design-book-editorial/SKILL.md`
- Modify: `skills/design-book-editorial/references/component-knowledge-retrieval.md`
- Modify: `skills/create-book-images/SKILL.md`
- Modify: `skills/create-book-images/references/component-prompt-pipeline.md`
- Modify: `skills/create-book-images/references/cover-prompt-contract.md`

### Tests and behavior evidence

- Create: `tests/test_cover_integrated_typography_contracts.py`
- Modify: `tests/test_component_kb_prompts.py`
- Modify: `tests/test_project_image_evidence_chain.py`
- Modify: `tests/test_editorial_design_component_kb_skill.py`
- Modify: `tests/test_create_book_images_component_kb_skill.py`
- Create: `tests/skill-behavior/create-book-images/integrated-typography-baseline.md`
- Create: `tests/skill-behavior/create-book-images/integrated-typography-with-skill.md`

### First real project

- Modify: `projects/lost-human-world-cover/inputs/project.json`
- Create after mapping approval: `projects/lost-human-world-cover/inputs/integrated-text-front.json`
- Modify: `tests/test_lost_human_world_cover_project.py`
- Modify: `docs/superpowers/plans/2026-08-12-lost-human-world-cover.md`

### Delivery evidence

- Create: `.superpowers/sdd/2026-08-12-cover-integrated-typography/task-implementation-report.md`
- Create after independent review: `.superpowers/sdd/2026-08-12-cover-integrated-typography/task-spec-review.md`
- Create after independent review: `.superpowers/sdd/2026-08-12-cover-integrated-typography/task-quality-review.md`

---

## Task 1: Establish RED pressure scenario and immutable baselines

**Files:**
- Create: `tests/skill-behavior/create-book-images/integrated-typography-baseline.md`
- Create: `.superpowers/sdd/2026-08-12-cover-integrated-typography/task-implementation-report.md`

**Interfaces:**
- Consumes current installed/source Skill instructions and current compiler.
- Produces a read-back record proving the old system cannot safely express the approved requirement.

- [ ] **Step 1: Record protected baselines**

Capture SHA-256 for:

```text
skills/design-book-editorial/SKILL.md
skills/create-book-images/SKILL.md
skills/create-book-images/references/component-prompt-pipeline.md
knowledge/book-component-libraries/cover/manifest.json
```

Also compute one aggregate SHA over the sorted `knowledge/book-component-libraries/cover` tree.

- [ ] **Step 2: Run the pre-change pressure scenario**

Use the fixed request:

```text
为 cover 生成 integrated typography：
front/title=失落人间；front/subtitle=在所有归途之外；front/author=早睡的猫。
封底和书脊为空。禁止 ISBN、条码、二维码、定价、CIP。
要求保留可编辑备份，并说明成图后的逐字审核与晋升门。
```

The baseline must record current failures rather than an imagined answer: current schema only accepts `readable_text=none`, compiler rejects project title in pixel Prompt, and review has no integrated-text checks.

- [ ] **Step 3: Confirm baseline is genuinely RED**

Run a minimal current compiler call and schema validation. Expected: no safe integrated-typography artifact can pass. Do not edit production files before this evidence exists.

- [ ] **Step 4: Read the saved baseline back**

Verify the file includes the request, observed failure, exact commands, exit codes and protected hashes.

---

## Task 2: Add project truth and integrated-text schemas

**Files:**
- Modify: `schemas/project-config.schema.json`
- Create: `schemas/book-component-integrated-text-entry.schema.json`
- Modify: `schemas/book-component-prompt.schema.json`
- Modify: `schemas/book-project-image-generation-payload.schema.json`
- Modify: `schemas/book-component-image-review.schema.json`
- Create: `tests/test_cover_integrated_typography_contracts.py`

**Interfaces:**
- `validate_data(data, "project-config") -> list[str]`
- `validate_data(data, "book-component-prompt") -> list[str]`
- `validate_data(data, "book-project-image-generation-payload") -> list[str]`
- `validate_data(data, "book-component-image-review") -> list[str]`

- [ ] **Step 1: Write schema RED tests**

Cover all of these cases:

1. project accepts optional structured `subtitle` and `author` strings.
2. old no-text Prompt without `text_rendering_mode` remains valid.
3. cover integrated Prompt requires `text_rendering_mode=integrated-typography`, `INTEGRATED_TEXT`, non-empty `integrated_text`, exact backup and `readable_text=exact-project-text`.
4. non-cover integrated Prompt is invalid.
5. missing backup, duplicate ID, unknown surface/role and extra field are invalid.
6. generation payload carries the same mode, integrated text and backup.
7. integrated review requires the seven new checks; old review does not.

The integrated review checks are exactly:

```text
integrated_text_exact
no_extra_text
surface_binding_valid
text_legible
typography_hierarchy_valid
machine_identifiers_absent
editable_backup_complete
```

- [ ] **Step 2: Run focused tests and confirm RED**

```bash
PYTHONPATH=. .venv/bin/python -m unittest \
  tests.test_cover_integrated_typography_contracts -v
```

Expected: failures because the new schema and fields do not exist.

- [ ] **Step 3: Add the reusable entry schema**

`book-component-integrated-text-entry.schema.json` must be closed (`additionalProperties=false`) and require:

```json
{
  "text_id": "TITLE-001",
  "surface": "front",
  "role": "title",
  "value": "失落人间",
  "language": "zh-CN"
}
```

Schema enum rejects machine roles. Semantic surface-role compatibility remains in Python because JSON Schema alone would duplicate complex logic.

- [ ] **Step 4: Extend Prompt schema conditionally**

Use optional `text_rendering_mode` for backward compatibility. Add conditional rules:

- absent or `editable-overlay`: existing required blocks and `readable_text=none`.
- `integrated-typography`: `component_type=cover`, require `INTEGRATED_TEXT`, `integrated_text`, `editable_text_backup`, and `readable_text=exact-project-text`.

Do not weaken `logo=none` or `watermark=none`.

- [ ] **Step 5: Extend payload and review schemas**

Generation payload must bind the structured text, not merely a background string. Review must carry `text_rendering_mode` and conditionally require the seven integrated checks while retaining the existing seven general checks.

- [ ] **Step 6: Run focused and existing contract suites**

```bash
PYTHONPATH=. .venv/bin/python -m unittest \
  tests.test_cover_integrated_typography_contracts \
  tests.test_component_kb_contracts \
  tests.test_contracts -v
```

Expected: GREEN, including all old fixtures.

---

## Task 3: Implement closed text policy and absolute machine-identifier guard

**Files:**
- Create: `ai/book_component_kb/integrated_text.py`
- Modify: `tests/test_component_kb_prompts.py`

**Interfaces:**

```python
def validate_integrated_typography(
    project: dict[str, Any],
    component_type: str,
    output_spec: dict[str, Any],
) -> IntegratedTypographyPlan: ...

def contains_machine_identifier(value: str) -> bool: ...
```

- [ ] **Step 1: Write policy RED tests**

Positive:

- front title/subtitle/author exactly match project facts.
- back copy and spine title/author are accepted when registered.
- front-only plan with empty back/spine is accepted.
- old editable-overlay output spec is unchanged.

Negative:

- integrated mode on toc/chapter-opener/illustration-decoration.
- unregistered project text, empty string, duplicate normalized text ID/value.
- front role bound to back, unsupported surface-role pair.
- backup value differs by one character.
- case reference title or invented recommendation enters `integrated_text`.
- forbidden role under any spelling/case/NFKC variant.

Machine-identifier matrix must include at least:

```text
ISBN 978-7-xxxx
9787553784182
7 8 7 5 5 3 7 8 4 1 8 2
条码 / barcode
二维码 / QR code
定价：58.00元
￥58 / RMB 58 / CNY 58
CIP
书号 / 发行编号 / 机器码
```

Place each sample in `title`, `short-note`, `other_text`-style prose and free positive Prompt fields to prove it cannot be hidden.

- [ ] **Step 2: Run tests and confirm RED**

Run only the new policy test class. Expected: import error or missing API, followed by the specific unsafe examples being accepted.

- [ ] **Step 3: Implement normalized policy module**

Use NFKC normalization, explicit enums, compiled patterns and exact project-fact matching. Keep this logic out of `prompts.py` so compiler orchestration and text safety have separate responsibilities.

Do not use a generic number ban: literary titles may contain numerals. Reject only machine identifier patterns, explicit labels and price/currency expressions.

- [ ] **Step 4: Export immutable normalized plan**

Use frozen dataclasses or tuples so later code cannot mutate validated text before compiling. Preserve original user characters in output; normalization is for comparison only.

- [ ] **Step 5: Run policy and prompt safety regression tests**

```bash
PYTHONPATH=. .venv/bin/python -m unittest \
  tests.test_component_kb_prompts -v
```

Expected: all historical short-title, readable-text and safe-zone guards remain GREEN.

---

## Task 4: Compile both text modes deterministically

**Files:**
- Modify: `ai/book_component_kb/prompts.py`
- Modify: `tests/test_component_kb_prompts.py`
- Modify: `tests/test_component_kb_cover_e2e.py`

**Interfaces:**
- Existing: `compile_component_prompt(project, genome, selection, output_spec) -> dict`
- New behavior: same function selects one of two closed modes and remains deterministic.

- [ ] **Step 1: Write compiler RED tests**

Assert:

- old fixture returns byte-for-byte/dict-equal legacy Prompt.
- integrated cover returns `text_rendering_mode`, `INTEGRATED_TEXT`, structured entries, backup and `readable_text=exact-project-text`.
- the independent block groups entries by surface and includes only registered values.
- `REFERENCE_TRANSFERS` never contains final project text.
- no registered text leaks into unrelated free blocks.
- compiler result is deterministic across two runs.
- machine identifiers and invented extra copy fail before a Prompt is returned.

- [ ] **Step 2: Confirm RED**

Expected: current `_OUTPUT_SPEC_FIELDS`, `_FORBIDDEN_PIXEL_TEXT_KEYS`, title guard and fixed block order reject integrated mode.

- [ ] **Step 3: Add mode-aware output spec validation**

Keep the current output spec shape as the editable-overlay branch. The integrated branch requires:

```text
text_rendering_mode
integrated_text
editable_text_backup
```

It may retain `editable_text_overlay`/`editable_text_values` only as the backup representation; the compiler must not describe them as the sole delivery layer.

- [ ] **Step 4: Build mode-specific block order**

For integrated cover, insert `INTEGRATED_TEXT` immediately before `PRINT_AND_CROP`. For legacy mode, preserve the exact existing `EXPECTED_BLOCK_ORDER` and generated bytes.

- [ ] **Step 5: Limit the original title guard instead of deleting it**

The project title is legal only inside the validated `INTEGRATED_TEXT` block and matching structured fields. It remains illegal in reference prose, design genome, composition, image content, color/material, negative constraints or arbitrary output prose.

- [ ] **Step 6: Compile and schema-validate both modes**

Run prompt and cover E2E suites. Recompile committed fixtures and deep-compare, never patch the compiled JSON by hand.

---

## Task 5: Bind integrated text into the paid-generation evidence chain

**Files:**
- Modify: `ai/book_component_kb/review.py`
- Modify: `tests/test_project_image_evidence_chain.py`
- Modify: `tests/test_create_book_images_component_kb_skill.py`

**Interfaces:**
- Existing: `validate_generation_bundle(project_root, evidence_paths) -> GenerationExecutionBundle`
- Existing: frozen snapshot/authorization SHA chain.
- Required: prompt ↔ payload ↔ authorization ↔ version all bind the same integrated text facts.

- [ ] **Step 1: Write evidence-chain RED tests**

Start from a valid integrated fixture, then mutate one artifact at a time:

- one character in title/subtitle/author.
- `surface` front to spine.
- role title to short-note.
- backup mismatch.
- extra text entry.
- payload mode changed to editable-overlay.
- authorization or version hash left stale.
- machine identifier inserted after compile.

Every mutation must fail before the execution bundle is returned.

- [ ] **Step 2: Confirm RED**

Expected: current payload has only background prompt and references, so structured text cannot be bound or compared.

- [ ] **Step 3: Extend generation payload comparison**

Preflight must validate:

```text
prompt.text_rendering_mode == payload.text_rendering_mode
prompt.integrated_text == payload.integrated_text
prompt.editable_text_backup == payload.editable_text_backup
```

Then rely on the existing snapshot and SHA authorization chain to freeze exact bytes.

- [ ] **Step 4: Extend `GenerationExecutionBundle` safely**

Expose immutable integrated text data for the image adapter. The adapter contract must say:

- use `background_prompt` and frozen reference bytes only.
- use only the supplied structured text; never add or rewrite copy.
- never read paths after preflight.
- verify the bundle before and after the model call.

- [ ] **Step 5: Add defense-in-depth machine scan**

Run the same absolute blacklist again immediately before returning the execution bundle, even though compiler validation already ran.

- [ ] **Step 6: Run evidence-chain regression**

```bash
PYTHONPATH=. .venv/bin/python -m unittest \
  tests.test_project_image_evidence_chain \
  tests.test_create_book_images_component_kb_skill -v
```

Expected: integrated and legacy chains both GREEN; no `imagegen` call occurs in tests.

---

## Task 6: Make text accuracy a mandatory review and promotion gate

**Files:**
- Modify: `ai/book_component_kb/review.py`
- Modify: `tests/test_component_kb_review.py`
- Modify: `tests/test_project_image_evidence_chain.py`

**Interfaces:**
- Existing: `review_image(review) -> dict`
- Existing: `review_project_image(...) -> dict`
- Existing: `prepare_project_promotion(...) -> dict`

- [ ] **Step 1: Write review RED tests**

For integrated mode, each of the seven text checks must independently block `selected` and promotion when false. Also reject:

- missing check.
- extra unregistered text observed.
- correct text on wrong surface.
- visually unreadable or ambiguous glyph.
- machine identifier present despite input guard.
- editable backup incomplete.

Legacy no-text reviews must continue to use `no_unwanted_text` and existing checks without the integrated seven.

- [ ] **Step 2: Confirm RED**

Expected: current `review_image` knows only the original seven checks.

- [ ] **Step 3: Add mode-aware review validation**

Review must bind the Prompt mode and integrated text facts from disk evidence, not trust a caller-supplied mode. A caller cannot claim `editable-overlay` for an integrated Prompt to skip the checks.

- [ ] **Step 4: Revalidate at promotion time**

Use the existing stable snapshot and precommit model. Promotion rereads and verifies the selected review, Prompt, payload, authorization, version and image; any text check mutation or evidence drift rejects with no proposal residue.

- [ ] **Step 5: Run review and full evidence-chain tests**

Expected: old and new modes pass; all false-check subtests fail closed.

---

## Task 7: Update the two Skills through RED/GREEN behavior testing

**Files:**
- Modify: `skills/design-book-editorial/SKILL.md`
- Modify: `skills/design-book-editorial/references/component-knowledge-retrieval.md`
- Modify: `skills/create-book-images/SKILL.md`
- Modify: `skills/create-book-images/references/component-prompt-pipeline.md`
- Modify: `skills/create-book-images/references/cover-prompt-contract.md`
- Modify: `tests/test_editorial_design_component_kb_skill.py`
- Modify: `tests/test_create_book_images_component_kb_skill.py`
- Create: `tests/skill-behavior/create-book-images/integrated-typography-with-skill.md`

**Skill requirements:**

- `design-book-editorial` asks the text mode only after component type and concept are known; it groups non-visual factual questions, while visual choices remain progressive.
- It presents exact proposed front/back/spine text before approval.
- It never treats case text as borrowable design content.
- `create-book-images` refuses actual generation without valid selection, compiled Prompt, generation approval and preflight bundle.
- It passes integrated text only from the frozen bundle.
- It requires explicit paid-generation authorization separately from design approval.
- It requires character-by-character human review and an editable backup.
- It states the absolute ISBN/barcode/QR/price/CIP ban in both the main Skill and focused reference.

- [ ] **Step 1: Add behavior contract tests before editing Skills**

Tests must read actual Skill/reference files and assert presence of operational instructions, commands/API names and failure behavior—not just keywords.

- [ ] **Step 2: Run behavior tests and confirm RED**

Expected: missing dual-mode route, integrated preflight and text-review rules.

- [ ] **Step 3: Edit Skill files minimally**

Keep main `SKILL.md` concise and route detail to references. Do not duplicate the entire schema in prose. Explain when to choose each mode, the approval sequence and hard failure rules.

- [ ] **Step 4: Repeat the same pressure scenario with updated Skill**

Produce `integrated-typography-with-skill.md` from the same request used in Task 1. It passes only if the response:

- preserves exact three project strings.
- binds them to front.
- leaves back/spine empty.
- provides editable backup.
- refuses all machine identifiers.
- stops before paid generation.
- names the post-generation review gate.

- [ ] **Step 5: Run Skill validators and behavior suites**

```bash
PYTHONPATH=. .venv/bin/python -m unittest \
  tests.test_editorial_design_component_kb_skill \
  tests.test_create_book_images_component_kb_skill -v

PYTHONPATH=. .venv/bin/python scripts/quick_validate_skill.py \
  skills/design-book-editorial
PYTHONPATH=. .venv/bin/python scripts/quick_validate_skill.py \
  skills/create-book-images
```

If the validator CLI differs, inspect `--help` and use the repository-supported syntax; do not alter validation to manufacture a pass.

---

## Task 8: Migrate 《失落人间》 to the new project truth without generating

**Files:**
- Modify: `projects/lost-human-world-cover/inputs/project.json`
- Create: `projects/lost-human-world-cover/inputs/integrated-text-front.json`
- Modify: `tests/test_lost_human_world_cover_project.py`
- Modify: `docs/superpowers/plans/2026-08-12-lost-human-world-cover.md`

**Project text:**

```text
front/title: 失落人间
front/subtitle: 在所有归途之外
front/author: 早睡的猫
back: empty
spine: empty
```

- [ ] **Step 1: Write project RED tests**

Assert structured `project.author` and `project.subtitle`, exact integrated entries and backups, front-only surfaces, no machine identifiers, and absence of generated images before a new explicit generation approval.

- [ ] **Step 2: Confirm RED**

Expected: current project stores author/subtitle only in tags and has no integrated text artifact.

- [ ] **Step 3: Migrate project facts**

Add `author` and `subtitle` to project JSON. Remove redundant `author:` and `subtitle:` tags if they would create two truth sources; retain thematic tags only.

- [ ] **Step 4: Create the front text artifact**

The file must contain exactly three integrated entries and matching backup. It is not a generation approval.

- [ ] **Step 5: Revise the original cover plan**

Replace its blanket no-text constraint and SVG-only overlay assumption with the approved integrated front mode. Keep:

- user case-field mapping approval.
- typography choice approval.
- selection SHA approval.
- separate actual generation authorization.
- editable backup and final comparison page.

Do not skip the still-pending user choice among the five retrieved cases and three typography structures.

- [ ] **Step 6: Run the project suite**

Expected: project facts and integrated text are valid; `generated/` remains absent or contains no new output.

---

## Task 9: Verify source, protect the knowledge base and obtain independent approval

**Files:**
- Update: `.superpowers/sdd/2026-08-12-cover-integrated-typography/task-implementation-report.md`
- Create: `.superpowers/sdd/2026-08-12-cover-integrated-typography/task-spec-review.md`
- Create: `.superpowers/sdd/2026-08-12-cover-integrated-typography/task-quality-review.md`

- [ ] **Step 1: Run focused suites**

```bash
PYTHONPATH=. .venv/bin/python -m unittest \
  tests.test_cover_integrated_typography_contracts \
  tests.test_component_kb_prompts \
  tests.test_component_kb_review \
  tests.test_project_image_evidence_chain \
  tests.test_editorial_design_component_kb_skill \
  tests.test_create_book_images_component_kb_skill \
  tests.test_lost_human_world_cover_project -v
```

- [ ] **Step 2: Run full validation**

```bash
PYTHONPATH=. .venv/bin/python scripts/validate_all.py
```

Expected: exit 0, all seven Skills pass, cover library remains `valid=true`, `status=available`, `record_count=50`, `errors=[]`.

- [ ] **Step 3: Compare protected hashes**

The cover KB aggregate SHA from Task 1 must be unchanged. Any knowledge asset, record or manifest change is out of scope and fails the task.

- [ ] **Step 4: Run independent spec review**

Reviewer checks exact requirement coverage, legacy compatibility, component boundary, project-text provenance, evidence binding and absolute machine-identifier ban. It edits only `task-spec-review.md`.

- [ ] **Step 5: Run independent quality/adversarial review**

Reviewer independently attempts:

- field-name bypasses.
- Unicode/NFKC and spacing variants.
- ISBN/price obfuscation covered by the defined threat model.
- prompt/payload/review mode mismatch.
- one-character mutation and surface swap.
- review/promotion evidence races and hardlink/path aliases already governed by the chain.

It edits only `task-quality-review.md`.

- [ ] **Step 6: Fix and re-review until both are APPROVED**

No Important or Critical finding may remain. Tests passing alone does not override a valid review finding.

---

## Task 10: Install the approved source and verify the personal Mac copy

**Files:**
- Runtime target: `/Users/edy/.codex/book-production-skills-v1`
- Skill entries: `/Users/edy/.codex/skills/design-book-editorial`
- Skill entries: `/Users/edy/.codex/skills/create-book-images`
- Verify: `LOCATION-INDEX.json` and `BOOK-PRODUCTION-LOCATION.json`

- [ ] **Step 1: Inspect installer help and preflight**

```bash
PYTHONPATH=. .venv/bin/python scripts/install_personal.py --help
```

Confirm the target is the managed runtime and `--replace` is required. Do not overwrite unmanaged paths.

- [ ] **Step 2: Test a temporary installation first**

Install into a temporary runtime and temporary skill home with dependencies skipped. Verify:

- all seven Skill symlinks resolve inside the temp runtime.
- both updated Skill references exist.
- source and installed schema/API tests pass against the temp root.
- installed cover manifest remains available/50.

- [ ] **Step 3: Update the managed personal installation**

After source tests and both reviews are approved, run the repository-supported `install_personal.py --replace` command. This is an authorized Skill update, not permission to call `imagegen`.

- [ ] **Step 4: Read back the real installation**

Verify canonical paths, updated Skill text, schema hashes, runtime marker, location index, cover count and installed quick validation. Compare the installed integrated typography files to source by SHA-256.

- [ ] **Step 5: Final report**

Report:

1. 完成内容。
2. 修改文件。
3. 双模式和绝对禁区的技术决策。
4. focused/full/temp-install/real-install/independent-review 结果。
5. 未调用 imagegen、未执行 InDesign、未开发网页前端。
6. 下一步回到《失落人间》：展示 5 个案例和字体结构，请用户批准字段映射与字体后，再准备正式生成授权。

## Acceptance Matrix

| Requirement | Automated evidence | Human/independent evidence |
|---|---|---|
| 旧无字模式兼容 | legacy Prompt deep-equal + full suite | spec review |
| 仅 cover 放开 | schema + compiler negative tests | spec review |
| 正封/封底/书脊准确绑定 | surface-role matrix tests | case review |
| 仅结构化项目文字 | project truth + compiler tests | spec review |
| 机器信息绝对禁止 | bypass matrix + preflight tests | adversarial review |
| 逐字审核 | seven-check false matrix | quality review |
| 可编辑备份完整 | schema + mismatch tests | project artifact read-back |
| 生成证据闭合 | evidence-chain mutation tests | quality review |
| 知识库不变 | aggregate SHA | implementation report |
| 个人安装同步 | temp + real install read-back | final handoff |

## Explicit Non-goals

- 本计划不调用 `imagegen`，不产生付费请求。
- 本计划不确定《失落人间》的最终案例字段映射或最终字体；这些仍需用户视觉判断。
- 本计划不制作封底或书脊内容，只建立可复用能力；《失落人间》首版只用正封文字。
- 本计划不生成 ISBN、条码、二维码、定价或 CIP，也不负责印前数据层。
- 本计划不执行 InDesign，不开发网页前端，不修改 50 条知识库内容。
