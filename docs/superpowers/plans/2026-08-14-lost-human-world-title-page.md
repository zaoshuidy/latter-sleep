# 《失落人间》扉页 V001 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 生成一张与现有“归途坐标”系统一致、包含纸船工作室标识、全部文字可编辑的扉页 V001，并把“稳定系统下先出可视结果”的规则写入编辑设计 Skill。

**Architecture:** 项目事实保存在 JSON，HTML 是可编辑页面源，Chrome 只负责生成 PNG 视觉预览。项目自动测试复核文字角色、页面隐藏规则、HTML 真文字与预览尺寸；Skill 行为规则通过同一压力场景的 RED/GREEN agent 复测。

**Tech Stack:** JSON、HTML/CSS、Python unittest、Chrome headless、Codex Skill Markdown。

## Global Constraints

- 页面成品尺寸为 145 × 210 mm，原型展示为空白左页加右侧扉页。
- 页面文字只有 `失落人间`、`在所有归途之外`、`早睡的猫`、`纸船工作室`。
- `纸船工作室` 的数据角色固定为 `studio_mark`，不得写成 `publisher`。
- 使用 `#F1EDE4`、`#1C1B19`、`#7A2428`、`#8F887E`，不引入图像或生图调用。
- 扉页隐藏页眉与可见页码；所有文字是可编辑 HTML 真文字。
- 不生成 InDesign、PDF、版权页、ISBN、CIP、定价或出版社 Logo。
- 当前目录和页眉页脚成果不得被修改。

---

### Task 1: 扉页可编辑原型与视觉预览

**Files:**
- Modify: `tests/test_lost_human_world_cover_project.py`
- Create: `projects/lost-human-world-cover/title-page/title-page-v001-layout.json`
- Create: `projects/lost-human-world-cover/title-page/title-page-v001.html`
- Create: `projects/lost-human-world-cover/title-page/title-page-v001-preview.png`
- Create: `projects/lost-human-world-cover/title-page/title-page-v001-review.md`
- Modify: `projects/lost-human-world-cover/README.md`

**Interfaces:**
- Consumes: `projects/lost-human-world-cover/inputs/project.json` 的真实书名、副标题和作者；既有 B 方向色彩。
- Produces: `TITLE-PAGE-LOST-HUMAN-WORLD-V001` 布局数据、1740 × 1260 PNG 和可编辑 HTML。

- [ ] **Step 1: 写入失败测试**

新增 `test_title_page_v001_uses_exact_editable_text_and_studio_mark`，手工断言：

```python
self.assertEqual(
    [
        ("title", "失落人间"),
        ("subtitle", "在所有归途之外"),
        ("author", "早睡的猫"),
        ("studio_mark", "纸船工作室"),
    ],
    [(item["role"], item["value"]) for item in layout["text_layers"]],
)
self.assertNotIn("publisher", json.dumps(layout, ensure_ascii=False))
self.assertEqual([1740, 1260], [meta["width"], meta["height"]])
```

- [ ] **Step 2: 运行 RED**

Run: `.venv/bin/python -m unittest tests.test_lost_human_world_cover_project.LostHumanWorldCoverProjectTests.test_title_page_v001_uses_exact_editable_text_and_studio_mark -v`  
Expected: FAIL，原因是 `title-page-v001-layout.json` 尚不存在。

- [ ] **Step 3: 创建 JSON 与 HTML**

JSON 必须包含：

```json
{
  "layout_id": "TITLE-PAGE-LOST-HUMAN-WORLD-V001",
  "page_trim_mm": [145, 210],
  "spread_trim_mm": [290, 210],
  "left_page": "blank-verso",
  "visible_running_headers": false,
  "visible_folios": false,
  "text_layers": [
    {"role": "title", "value": "失落人间"},
    {"role": "subtitle", "value": "在所有归途之外"},
    {"role": "author", "value": "早睡的猫"},
    {"role": "studio_mark", "value": "纸船工作室"}
  ]
}
```

HTML 使用两个 `.page`，左页不含文字节点；右页以断续暗红纵轴、竖排书名/副标题/作者和底部横排工作室标识构图。每项文字带 `data-role` 与 `data-text-layer="editable"`。

- [ ] **Step 4: 生成 PNG 并视觉检查**

Run:

```bash
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --headless --disable-gpu --hide-scrollbars \
  --window-size=1740,1260 --screenshot="$(pwd)/projects/lost-human-world-cover/title-page/title-page-v001-preview.png" \
  "file://$(pwd)/projects/lost-human-world-cover/title-page/title-page-v001.html"
```

用 `view_image` 检查空白左页、右页层级、书沟安全区、文字对比、无裁切/溢出/滚动条。若不合格，只调整 CSS，不改变文字事实。

- [ ] **Step 5: 写审查记录与项目索引**

记录四项文字边界、studio mark 身份、视觉检查和 JSON/HTML/PNG SHA-256；README 增加扉页段落。

- [ ] **Step 6: 运行 GREEN**

Run: `.venv/bin/python -m unittest tests.test_lost_human_world_cover_project -v`  
Expected: 全部通过。

---

### Task 2: 先出视觉结果的稳定流程规则

**Files:**
- Modify: `skills/design-book-editorial/SKILL.md`
- Test: fresh behavior agent using `skills/design-book-editorial/SKILL.md`

**Interfaces:**
- Consumes: 已有批准视觉系统、已确认真实文字、用户明确委托直接完成。
- Produces: `visual-first prototype` 路由；先生成 V001 并展示，省略单独书面规格确认。

- [ ] **Step 1: 运行 Skill RED 行为样本**

给 agent 场景：项目已有批准的封面、目录、正文和页眉页脚；用户说“你直接完成，新增规则生成后给我看，不需要设计规格过程”。要求 agent 给出下一动作。  
Expected RED: 当前 Skill 仍提出两套方向或要求先确认书面规格，不能稳定直接生成 V001。

- [ ] **Step 2: 最小修改 Skill**

在设计流程中加入条件分支：若同一项目已有批准视觉系统、真实文字齐全且用户明确委托直接完成单一页面家族，则直接生成一版可视 V001 并展示；不另建书面规格确认轮次。若缺真实文字、开本、授权或与现有系统冲突，才集中询问必要事实。规则不跳过成品人工评判、可编辑文字和验证。

- [ ] **Step 3: 运行相同 GREEN 行为样本**

Expected GREEN: agent 直接提出并执行 V001 生成，生成后展示；不要求用户先审阅规格或选择多套方向。

- [ ] **Step 4: 校验并部署**

Run:

```bash
.venv/bin/python /Users/edy/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/design-book-editorial
.venv/bin/python scripts/validate_all.py
.venv/bin/python scripts/install_personal.py --replace
```

Expected: Skill valid，完整测试 exit 0，安装副本与维护源 Skill 哈希一致。
