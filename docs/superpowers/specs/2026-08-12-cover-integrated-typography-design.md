# 图书封面一体化艺术字模式设计

日期：2026-08-12  
状态：已由用户批准  
适用套件：`book-production-skills-v1`  
首个使用项目：《失落人间》

> 2026-08-12 精简决定：实际第一版只实施项目文字登记、cover-only 双模式、机器信息绝对禁区、四项成图检查和可编辑回退；复用现有生成授权与哈希链，不新增重复的证据层。实施计划见 `docs/superpowers/plans/2026-08-12-cover-integrated-typography-minimal.md`。

## 1. 背景

现有图书图片管线把所有最终文字限制在可编辑 overlay 中，生成模型只能制作无字背景。这一策略适合目录、章首页和正文等需要长期修改、文字量较大或准确性要求高的部件，但也限制了封面艺术字与图像、留白、结构之间的一体化生成。

用户确认需要更新 Skill：封面、封底和书脊可以直接生成项目文字，使字形、排列、尺度、空间和视觉符号共同参与封面表达；ISBN、条码、定价等机器识别信息绝对不得进入生图。

## 2. 目标用户

- 希望题名成为封面核心视觉语言的个人图书设计者。
- 需要正封、封底和书脊文字与图像共同形成构图的中文图书项目。
- 愿意逐字人工审核生成文字，并在失败时重新生成或使用可编辑备份修复的使用者。

## 3. 目标

1. 为 `cover` 组件增加可选的一体化艺术字模式。
2. 允许正封、封底和书脊使用项目已确认的准确文字。
3. 保留现有无字背景模式，确保旧项目继续有效。
4. 只允许结构化项目文字进入生成指令，禁止自由 Prompt 夹带未登记文字。
5. 永久阻止 ISBN、条码、定价及其他机器识别信息进入生成像素。
6. 生图后逐字核验准确性、位置和额外伪文字。
7. 始终保留可编辑文字备份，供修复、改版和排版交接使用。

## 4. 方案比较与选择

### 4.1 采用：封面专用双模式

`cover` 支持：

- `editable-overlay`：现有无字背景模式。
- `integrated-typography`：项目已确认文字直接参与封面生成。

优点是兼容旧项目、边界清晰、可以逐项目选择，并能把文字准确性变成可验证合同。

### 4.2 不采用：删除所有文字守卫

直接删除守卫实现简单，但会让案例原文字、自由 Prompt 文案、模型编造文字和机器识别信息进入像素，无法区分合法项目文字与文字注入。

### 4.3 不采用：始终在生成后栅格化叠字

后期叠字准确且可编辑，但无法满足“文字本身参与模型构图和艺术表达”的目标，只能作为失败修复和备份机制。

## 5. 适用范围

### 5.1 允许

仅当 `component_type=cover` 且项目显式选择 `integrated-typography` 时，以下封面表面可以生成准确文字：

- `front`：书名、副标题、作者名，以及项目确认的短说明。
- `back`：项目确认的封底简介、推荐语和短说明。
- `spine`：书名、作者名和项目确认的短说明。
- `full-wrap`：以上三类表面按明确区域分别绑定。

### 5.2 继续禁止

- `toc`、`chapter-opener`、`illustration-decoration` 的最终文字进入生成像素。
- 正文文字、目录项、章节正文、页码和页眉页脚进入生成像素。
- 案例原书名、原作者、原出版社文字或独特题名组合。
- 模型自行编造的宣传语、奖项、出版社、机构、人物信息或事实。
- 未在结构化文字清单登记的额外文字。

### 5.3 绝对禁止的机器识别信息

以下内容不能因模式、用户 Prompt、封底设计或任何豁免进入生成像素：

- ISBN 及其任何格式变体。
- 一维条码、二维码和其他机器码。
- 定价、币种和价格字段。
- CIP、书号、发行编号及其他机器或出版管理识别信息。

它们必须由后期准确数据层生成，并在正式排版阶段处理。

## 6. 核心合同

### 6.1 模式字段

Prompt 输入新增：

```json
"text_rendering_mode": "editable-overlay | integrated-typography"
```

兼容规则：旧输入缺少该字段时按 `editable-overlay` 处理。

### 6.2 一体化文字清单

`integrated-typography` 必须提供闭合数组：

```json
"integrated_text": [
  {
    "text_id": "TITLE-001",
    "surface": "front",
    "role": "title",
    "value": "失落人间",
    "language": "zh-CN"
  },
  {
    "text_id": "SUBTITLE-001",
    "surface": "front",
    "role": "subtitle",
    "value": "在所有归途之外",
    "language": "zh-CN"
  },
  {
    "text_id": "AUTHOR-001",
    "surface": "front",
    "role": "author",
    "value": "早睡的猫",
    "language": "zh-CN"
  }
]
```

允许的 `surface` 只有 `front/back/spine`。允许的 `role` 只包含项目文字角色，不包含 ISBN、barcode、price 或其他机器字段。

### 6.3 可编辑备份

每个 `integrated_text` 条目必须在 `editable_text_backup` 中存在同一 `text_id` 和同一 `value`。备份不默认覆盖生成图，只用于：

- 错字修复。
- 后续改版。
- 版式和字体替换。
- InDesign 恢复与印前交接。

### 6.4 Prompt 输出

`book-component-prompt` 的 `generation_constraints.readable_text` 扩展为：

- `none`：无字模式。
- `exact-project-text`：仅允许 `integrated_text` 中的准确字符串。

编译器生成独立的 `INTEGRATED_TEXT` 块；文字值不得散落在 `REFERENCE_TRANSFERS`、案例说明或其他自由字段中。

## 7. 守卫设计

### 7.1 保留的守卫

- reference selection 的正向字段仍不得包含项目真实文字或要求复制案例文字。
- 案例文字、模型编造文案和未登记字符串仍拒绝。
- 非 cover 组件遇到 `integrated-typography` 必须 fail closed。
- 输出中的文字集合必须与 `integrated_text` 精确一致，不能多一个或少一个项目条目。

### 7.2 机器识别信息守卫

输入预检同时检查字段角色与文本内容。出现以下任一情况立即拒绝：

- `role` 为 `isbn/barcode/qr-code/price/cip` 等禁止角色。
- 文本符合 ISBN 模式或含明确 ISBN 标签。
- 请求绘制条码、二维码或机器码。
- 请求显示价格、定价或货币金额。

该守卫不能通过把信息放进 `title`、`other_text` 或自由 Prompt 字段绕过。

### 7.3 表面绑定

每个条目只能绑定一个表面。编译器必须保持：

- 正封文字只进入正封说明。
- 封底文字只进入封底说明。
- 书脊文字只进入书脊说明。

模型输出若发生表面串位，人工审核必须拒绝。

## 8. 数据流

```text
项目事实
→ 案例检索与人工字段映射
→ 文字模式选择
→ integrated_text + editable_text_backup
→ schema / 机器信息 / 未登记文字预检
→ 编译含 INTEGRATED_TEXT 的封面 Prompt
→ 用户查看准确文字与生成动作
→ 用户明确授权生图
→ 模型生成封面文字与图像
→ 逐字、逐表面、逐层级人工审核
→ 通过：保留生成字形 + 可编辑备份
→ 失败：拒绝版本，重新生成或启用可编辑备份
```

## 9. 审核合同

原 `no_unwanted_text` 调整为“没有未授权或额外文字”，不是“完全无文字”。一体化模式新增或强化以下检查：

1. `integrated_text_exact`：每个字符串逐字准确。
2. `no_extra_text`：没有额外汉字、拉丁字母、伪文字或乱码。
3. `surface_binding_valid`：正封、封底和书脊文字没有串位。
4. `text_legible`：项目要求可读的文字达到可读标准。
5. `typography_hierarchy_valid`：书名、副标题、作者和封底信息层级符合批准方案。
6. `machine_identifiers_absent`：不存在 ISBN、条码、二维码、价格或其他机器识别信息。
7. `editable_backup_complete`：每个生成文字都有一致的可编辑备份。

任一检查为 false，图像不能进入 `selected`，也不能形成 promotion proposal。

## 10. Skill 更新范围

### 10.1 `design-book-editorial`

- 案例映射阶段仍不允许最终项目文字进入 reference prose。
- 增加封面文字模式选择与表面文字结构设计。
- 字体、字重、字距和题名结构作为 integrated typography 的正式输入。

### 10.2 `create-book-images`

- 从“所有设计图默认无字”改为“封面可显式选择 exact-project-text”。
- 生成授权必须完整回显每个 surface/role/value。
- imagegen adapter 只接收编译后的闭合 Prompt，不接收临时自由文字补充。
- 审核流程增加文字准确性和机器信息缺席门禁。

## 11. 技术影响

- Schema：扩展 Prompt、output spec、generation payload、image review 合同。
- Compiler：增加 cover-only 模式分支和 `INTEGRATED_TEXT` 块，保留旧无字分支。
- Safety：把“全部文字禁止”重构为“模式化白名单 + 机器信息永久黑名单”。
- Tests：增加 cover 正向、非 cover 拒绝、未登记文字拒绝、机器信息绕过拒绝、表面绑定和兼容性测试。
- Project：《失落人间》从无字背景模式迁移为 `integrated-typography`，正封三项文字进入生成；当前只制作正封，因此 back/spine 清单为空。
- Knowledge Base：不修改 50 条案例，不把生成文字反写到来源 record。
- Deployment：源套件通过完整验证后再同步个人安装副本；安装副本必须重复相同行为测试。

## 12. 测试策略

### 12.1 RED 场景

在修改 Skill 和代码前，现有系统应真实拒绝 cover integrated text；测试记录具体失败原因。

### 12.2 GREEN 正向

- cover/front 的 title/subtitle/author 通过。
- cover/back 的已确认简介通过。
- cover/spine 的 title/author 通过。
- 缺省模式仍生成无字 Prompt。
- 《失落人间》三项文字精确进入 `INTEGRATED_TEXT` 和备份。

### 12.3 负向与绕过

- toc/chapter-opener/illustration-decoration 请求 integrated text 均拒绝。
- 未登记额外文字、案例原文字和模型编造文案均拒绝。
- ISBN 带横线、不带横线、全角字符、藏在 `other_text` 中均拒绝。
- 条码、二维码、CIP、价格、货币金额及同义表达均拒绝。
- 正封文字错绑到 spine、封底文案错绑到 front 均拒绝。
- integrated text 与 editable backup 不一致时拒绝。
- 图像审核任一文字检查为 false 时不得 selected 或 promotion。

### 12.4 回归

- 现有无字案例与 Prompt 必须字节级或结构级保持兼容。
- 封面知识库继续 `available`、50 条、`errors=[]`。
- 7 个 Skills 和完整测试套件全部通过。

## 13. 《失落人间》应用

当前项目采用：

```text
component_type = cover
cover_scope = front
text_rendering_mode = integrated-typography
front.title = 失落人间
front.subtitle = 在所有归途之外
front.author = 早睡的猫
back = empty
spine = empty
machine_identifiers = forbidden
```

后续案例与字体选择继续执行，但选择结果将同时控制字形、字距、断行、题名结构和图像构图，不再只生成文字安全区。

## 14. 验收标准

1. 旧无字模式不受影响。
2. 只有 cover 可以启用一体化艺术字。
3. 正封、封底和书脊只生成结构化清单中的项目已确认文字。
4. ISBN、条码、定价和其他机器识别信息在所有路径中均被拒绝。
5. reference mapping 仍不泄漏项目文字或复制案例文字。
6. 每个生成文字都有同值可编辑备份。
7. 审核能够拒绝错字、漏字、多字、伪文字和表面串位。
8. 《失落人间》三项正封文字可进入生成 Prompt，且 back/spine 保持空。
9. 未经用户查看文字清单和明确生成授权，不调用 imagegen。
10. 源套件与安装副本均通过完整测试和 Skill 验证。
