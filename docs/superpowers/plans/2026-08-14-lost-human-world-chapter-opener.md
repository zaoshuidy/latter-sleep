# 《失落人间》章首页母版 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 让章首页正式 selection 支持自身七字段，并生成案例 2＋5 的可验证 draft 映射。

**Architecture:** `prompts.py` 按 selection 的 `component_type` 从 `retrieve.COMPONENT_WEIGHTS` 取得允许字段，保持 cover 行为不变。项目目录只新增一份 draft selection；schema、Prompt-safety 和 retrieval evidence 共同构成门禁。

**Tech Stack:** Python 3、unittest、JSON Schema、现有 `ai.book_component_kb` production API。

## Global Constraints

- 只处理 `chapter-opener` 字段兼容与方向 A。
- 参考固定为 `CHO-CN-0006`、`CHO-CN-0011`。
- 真实书名、作者、章号和章题不得进入 reference mapping prose 或背景图。
- 不调用 imagegen，不执行 InDesign，不修改知识库记录。
- 当前目录不是 Git 仓库，因此不创建提交。

---

### Task 1: 组件字段校验与方向 A draft

**Files:**
- Modify: `ai/book_component_kb/prompts.py`
- Modify: `tests/test_component_kb_prompts.py`
- Create: `projects/lost-human-world-cover/chapter-opener/reference-selection-A.json`

**Interfaces:**
- Consumes: `retrieve.COMPONENT_WEIGHTS: dict[str, dict[str, float]]`、`validate_selection_prompt_safety(project, selection)`、`validate_selection(selection, retrieval_result)`。
- Produces: 按 `selection.component_type` 验证 `include_fields` 的 selection 合同；一份 `status=draft` 的章首页映射。

- [ ] **Step 1: 写失败测试**

在 `SelectionValidationTests` 增加章首页 selection fixture，断言七个章首页字段可通过 shape/evidence 校验，同时断言 cover selection 不能使用 `chapter_title_zone`。

- [ ] **Step 2: 运行测试确认 RED**

Run:

```bash
cd /Users/edy/Desktop/book/book-production-skills-v1
PYTHONPATH=. .venv/bin/python -m unittest \
  tests.test_component_kb_prompts.SelectionValidationTests.test_chapter_opener_uses_component_specific_include_fields \
  tests.test_component_kb_prompts.SelectionValidationTests.test_cover_rejects_chapter_opener_include_field -v
```

Expected: 章首页正向测试因 `chapter_title_zone` 等字段被视为 unknown 而失败；cover 负向测试通过。

- [ ] **Step 3: 最小实现**

将 `prompts.py` 的固定 `COVER_WEIGHTS` 允许集合改为从 `COMPONENT_WEIGHTS[selection["component_type"]]` 读取；未知或未实现组件 fail closed。

- [ ] **Step 4: 运行测试确认 GREEN**

Run:

```bash
cd /Users/edy/Desktop/book/book-production-skills-v1
PYTHONPATH=. .venv/bin/python -m unittest tests.test_component_kb_prompts -v
```

Expected: 全部通过。

- [ ] **Step 5: 写入并校验 draft selection**

创建 `SEL-LOST-HUMAN-WORLD-CHAPTER-A-001`，两条 reference 分别只借用本轮 retrieval 中分数大于零的章首页字段。运行：

```bash
cd /Users/edy/Desktop/book/book-production-skills-v1
PYTHONPATH=. .venv/bin/python scripts/validate_json.py \
  book-component-reference-selection \
  projects/lost-human-world-cover/chapter-opener/reference-selection-A.json
```

再用 Python 调用 `validate_selection_prompt_safety`；将内存副本状态改为 `approved` 后调用 `validate_selection`，只验证 retrieval 绑定，不提前修改磁盘 draft 状态。

- [ ] **Step 6: 回归验证**

Run:

```bash
cd /Users/edy/Desktop/book/book-production-skills-v1
PYTHONPATH=. .venv/bin/python -m unittest \
  tests.test_component_kb_prompts \
  tests.test_component_kb_chapter_opener -v
```

Expected: 全部通过；计算并报告 draft selection SHA-256，等待用户一次批准。
