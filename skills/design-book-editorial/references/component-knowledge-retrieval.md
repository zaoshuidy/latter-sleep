# 组件知识库检索与人工映射

封面、目录、章首页和插画装饰进入正式视觉方向前执行本协议。组件知识库只作内部参考和字段借用，不是可整体复制的模板库。

## 1. 从当前 Skill 解析套件路径

不要假定当前工作目录。先取得正在执行的 `SKILL.md` 绝对路径，再解析维护源套件；项目 query 仍使用当前项目中的绝对路径：

```bash
SKILL_FILE="/absolute/path/to/current/skills/design-book-editorial/SKILL.md"
SUITE_ROOT="$(cd -P "$(dirname "$SKILL_FILE")/../.." && pwd)"
SUITE_PYTHON="$SUITE_ROOT/.venv/bin/python"
PROJECT_QUERY="/absolute/path/to/current/project/query.json"
```

先检查正式案例索引。脚本位于本 Skill 的 `scripts/`，不是套件顶层 `scripts/`：

```bash
"$SUITE_ROOT/.venv/bin/python" \
  "$SUITE_ROOT/skills/design-book-editorial/scripts/check_case_library.py" \
  "$SUITE_ROOT/knowledge/indexes/design-case-index.json"
```

## 2. 校验目标组件库

`component_type` 必须与当前部件完全一致。封面只能使用 `cover` 记录，不得混入 `toc`、`chapter-opener` 或其他部件；其他部件同理。封面维护源命令为：

```bash
"$SUITE_PYTHON" "$SUITE_ROOT/scripts/book_component_kb/validate_library.py" \
  --component-root "$SUITE_ROOT/knowledge/book-component-libraries/cover" \
  --registry "$SUITE_ROOT/knowledge/book-component-libraries/source-registry.json" \
  --required-count 50
```

只有退出码为 0，且报告同时满足 `valid=true`、`status=available`、`record_count>=50`、`errors=[]`，才能继续。目标组件目录缺失、状态 unavailable/building、记录不足或校验失败时必须 **fail closed**：报告真实缺口并停止该部件的正式方向，不得用通用概念、网页灵感或其他 `component_type` 补位。

## 3. 精确检索 5 本不同书

query 必须符合 `book-component-retrieval-query`，并将 `component_type` 固定为目标部件：

```bash
"$SUITE_PYTHON" "$SUITE_ROOT/scripts/book_component_kb/retrieve_references.py" \
  --component-root "$SUITE_ROOT/knowledge/book-component-libraries/cover" \
  --registry "$SUITE_ROOT/knowledge/book-component-libraries/source-registry.json" \
  --query "$PROJECT_QUERY" \
  --limit 5
```

结果必须是 `status=available`、**exactly 5** 个候选和 5 个不同 `book_case_id`。少于 5 本时返回缺口；不得重复一本书凑数，不得换成未经目标组件库验证的候选。

## 4. 展示本地真实资产与本轮可借字段

人工选择前，对每个候选读取对应 record，解析 `asset.relative_path`，并展示本地真实资产。每张图旁必须列出：

- `record_id`、书名、`book_case_id`、完整 `component_profile`；
- `source.source_url` 和本地资产绝对路径，并在界面中直接显示图片；
- 八个可借字段逐项的**匹配值、来源、`field_scores` 和可选性**，不能只列全局字段 enum。

字段值和证据来源固定如下：

| 字段 | 值的来源 |
|---|---|
| `visual_strategy`、`composition`、`title_zone`、`cover_scope` | record 的 `component_profile` |
| `color`、`mood` | record 的 `retrieval_features.color_tags / mood_tags` 与 retrieval 的 `match_explanation` |
| `material`、`book_category` | record 中 visibility 不是 uncertain 的同名 `visual_decomposition.observations` |

只有该候选本次 retrieval 的对应 `field_scores >0`，字段才可写入 `include_fields`；这表示本次 query 与已索引值有匹配证据。分数为 0 时必须显示“不可选”和真实原因。当前《四时来信》这次检索的 5 个候选中，`material`、`book_category` 均为 0，必须标为不可选，不得凭图片推断或让用户选择。

图片只作为内部参考。只能借用被显式选择的字段关系，不得整体复制封面、具体图形、原照片、原文字、原色值或单一案例的独特组合。

## 5. 两阶段人工 reference-mapping 门禁

### 阶段一：简洁 mapping 转写为 draft

先展示 5 张图，再请用户为每个方向从本次结果中选择 2—3 个 record，并简洁写出希望借用的可选字段和调整意图。用户这一步的回复**不是正式 selection**，也不要让用户填写审批状态。

Agent 将回复转写为方向 A、方向 B 两份完整 `book-component-reference-selection` JSON。每份都必须包含：

- `schema_version`、唯一 `selection_id`、本次 `query_id`、目标 `component_type`；
- 2—3 个不同 `record_id`；
- 每个 record 的 `include_fields`、`existing_baseline`、`adjustment_instruction`、`preserve_elements`、`required_changes`、`exclude_fields`；
- 英文契约状态 `status=draft`。

会进入正向像素指令的 `existing_baseline`、`adjustment_instruction`、`preserve_elements`、`required_changes` 只能写“本项目”“项目书名长度”“项目自身内容”等 Prompt-safe 表述，不得写真实书名、作者、studio 或任何最终可读文字，也不得要求在图像中添加或显示文字。真实书名、作者和 studio 只保留在项目 `metadata`／可编辑 `overlay`。

`exclude_fields` 用明确文字排除原书文字、具体图形、图像内容、色值及其他不可复制项。虽然它不是正向生成指令，但完整 `REFERENCE_TRANSFERS` 块也不得出现项目的真实最终文字。两份 draft 保存到当前项目，不保存到知识库。用绝对路径进行 schema 校验：

```bash
PYTHONPATH="$SUITE_ROOT" "$SUITE_PYTHON" "$SUITE_ROOT/scripts/validate_json.py" \
  book-component-reference-selection "/absolute/project/path/reference-selection-A.json"
PYTHONPATH="$SUITE_ROOT" "$SUITE_PYTHON" "$SUITE_ROOT/scripts/validate_json.py" \
  book-component-reference-selection "/absolute/project/path/reference-selection-B.json"
```

schema 校验后、**完整回显前**，必须对每份 draft 及当前项目配置调用公开 production API `ai.book_component_kb.prompts.validate_selection_prompt_safety(project, selection)`。它检查完整 `REFERENCE_TRANSFERS` 中是否泄漏真实项目书名，并对上述四个正向字段运行 readable-text action/object guard：

```python
import json
from pathlib import Path
from ai.book_component_kb.prompts import validate_selection_prompt_safety

project = json.loads(Path("/absolute/project/path/project.json").read_text(encoding="utf-8"))
selection = json.loads(Path("/absolute/project/path/reference-selection-A.json").read_text(encoding="utf-8"))
validate_selection_prompt_safety(project, selection)
```

preflight 失败时不得请求批准：用 Prompt-safe 表述重写 draft，重新运行 schema 与 preflight，并在最终文件落盘后重新计算 SHA。只有两项校验都通过，才向用户**完整回显**两份 JSON，逐份报告 `selection_id`、保存绝对路径和文件 `SHA-256`，然后停止。中文“批准 / 退回”不是契约状态，不能代替 `status`。

### 阶段二：按 ID 和 SHA 二次批准

要求用户二次明确批准每份 draft 对应的 `selection_id + SHA-256`。只有用户回复准确指向这些 ID 和哈希，且磁盘文件复算哈希仍一致时，才把相应 JSON 的唯一状态变更为 `status=approved`，再次运行 schema 校验，并用同一次 retrieval result 调用 `ai.book_component_kb.prompts.validate_selection`。

`validate_selection` 必须同时确认：每方向 2—3 个不同候选、query/component 一致、record 确实来自本次 5 个结果，以及每个 `include_fields` 在该 record 的 `field_scores >0`。任一条件失败就保留门禁，不得形成正式方向。

批准前不得：

- 替用户选择参考或把通用概念当作 record；
- 输出正式两方向、生成 Prompt 或指定生成数量；
- 把候选 record ID 写入 `design-genome.reference_ids`；
- 调用 `imagegen`。

## 6. 批准后的方向绑定

两个 approved selection 通过 `validate_selection` 后，方向 A、B 分别绑定其真实 `record_id`，并逐条保留 `include_fields` 与 `exclude_fields`；两个方向共享同一份项目事实。只有此时才能写正式方向、`design-genome` 并调用 Prompt 编译器。

图片生成不属于本 Skill。作者或工作室标记未由项目提供时，保持 `待确认（可编辑文字层）`，不得发明姓名或机构。

### 封面文字模式

案例 mapping 仍禁止真实项目文字；selection 批准后再决定文字输出。`editable-overlay` 使用无字底图。`integrated-typography` 仅限 `cover`，只登记项目已确认的正封、封底、书脊文字，并同步可编辑备份。所有表面文字要在生图前一次完整回显；ISBN、条码、二维码、定价、CIP 不得登记或进入 Prompt。目录、章首页和插图装饰没有此例外。

## 7. 证据边界

- 视觉纹理不等于材料或印刷工艺；材料、装帧和工艺只使用 record 中有明确证据的观察。
- 没有确定证据时标为待确认，不推断纸张、烫印、压凹、UV 或装订方式。
- 目录、章首页等含文字部件仍输出可编辑真文字；组件图只承担背景、图像或装饰参考。

## 快速验收

| 门禁 | 通过条件 |
|---|---|
| 路径 | 从实际 `SKILL_FILE` 解析 `SUITE_ROOT`，命令不依赖 cwd |
| 库 | 目标 `component_type`，50 条及以上，`status=available` |
| 检索 | exactly 5，且为不同 `book_case_id` |
| 展示 | 真实图片、ID、profile、source、逐候选字段证据齐全 |
| draft | 两份 JSON schema 与 Prompt-safety preflight 均通过，完整回显并报告 selection ID + SHA |
| 批准 | 用户二次批准准确 ID + SHA；改 approved 后通过 `validate_selection` |
| 方向 | 只绑定已批准真实 record ID，无跨组件混用 |
| 边界 | 不整体复制、不虚构文字/工艺、不在本 Skill 生图 |
