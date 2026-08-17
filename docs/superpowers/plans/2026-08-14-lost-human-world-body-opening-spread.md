# 《失落人间》正文首跨页实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 使用第一章真实原文生成 A「渐入式」正文首跨页的可编辑 HTML、视觉预览 PNG 和可追溯布局记录。

**Architecture:** 以 Markdown 原文为只读事实源，静态 HTML 承担可编辑排版，Chrome 只负责把 HTML 渲染为审核预览 PNG。JSON 记录源文件哈希、使用段落范围、版式与测试页码；自动测试从 HTML 读回段落并与 Markdown 同序比对。

**Tech Stack:** HTML/CSS、Python 标准库 `unittest`、项目现有 `.venv`、Google Chrome headless、macOS `sips`。

## Global Constraints

- 不修改、润色、校对或重新措辞 `projects/lost-human-world-cover/manuscript/chapter-01.md`。
- 单页成品 145 × 210 mm；首跨页 290 × 210 mm。
- 左页顶部渐入留白约 54 mm，右页正文上版口约 26 mm。
- 正文保持 HTML 真文字；不得把正文生成为图片。
- 首跨页无页眉；页脚采用 `folio-outer`，测试页码不视为最终目录页码。
- 纸色 `#F1EDE4`、正文 `#1C1B19`、一次性引导线 `#7A2428`。
- 不生成 InDesign、PDF、版权页或全书排版。

---

## 文件结构

- Create: `projects/lost-human-world-cover/body-opening/body-opening-v001.html` — 可编辑正文首跨页。
- Create: `projects/lost-human-world-cover/body-opening/body-opening-v001-preview.png` — 审核预览。
- Create: `projects/lost-human-world-cover/body-opening/body-opening-v001-layout.json` — 源哈希、段落范围和版式参数。
- Create: `projects/lost-human-world-cover/body-opening/body-opening-v001-review.md` — 人工可读检查结果。
- Modify: `tests/test_lost_human_world_cover_project.py` — 锁定正文完整性、真文字、版心和页面衔接。

### Task 1: 锁定正文首跨页合同

**Files:**
- Modify: `tests/test_lost_human_world_cover_project.py`
- Test: `tests/test_lost_human_world_cover_project.py`

**Interfaces:**
- Consumes: `projects/lost-human-world-cover/manuscript/chapter-01.md` 的标题后前 10 个非空段落。
- Produces: 对 HTML、布局 JSON 和 PNG 的自动验收合同。

- [ ] **Step 1: 写失败测试**

在 `LostHumanWorldCoverProjectTests` 中新增 `test_body_opening_v001_uses_exact_source_text_and_approved_layout()`：

```python
import hashlib
import html as html_module
import re

def test_body_opening_v001_uses_exact_source_text_and_approved_layout(self):
    source_path = PROJECT / "manuscript/chapter-01.md"
    html_path = PROJECT / "body-opening/body-opening-v001.html"
    layout = self.load("body-opening/body-opening-v001-layout.json")
    page_html = html_path.read_text(encoding="utf-8")
    source_paragraphs = [
        part.strip()
        for part in source_path.read_text(encoding="utf-8").split("\n\n")[1:]
        if part.strip()
    ]
    rendered = [
        html_module.unescape(re.sub(r"<[^>]+>", "", value)).strip()
        for value in re.findall(
            r'<p data-source-index="\d+">(.*?)</p>', page_html, flags=re.S
        )
    ]

    self.assertEqual(source_paragraphs[:10], rendered)
    self.assertEqual(
        hashlib.sha256(source_path.read_bytes()).hexdigest(),
        layout["source_sha256"],
    )
    self.assertEqual([1, 10], layout["source_paragraph_range"])
    self.assertEqual([145, 210], layout["page_trim_mm"])
    self.assertEqual("folio-outer", layout["running_header_template"])
    self.assertEqual("approved", layout["design_spec_status"])
    self.assertIn('data-text-layer="editable"', page_html)
    self.assertNotIn("第一章", page_html)
    self.assertNotIn("车窗里的故乡", page_html)
    self.assertTrue((PROJECT / "body-opening/body-opening-v001-preview.png").is_file())
```

- [ ] **Step 2: 运行测试并确认 RED**

Run:

```bash
.venv/bin/python -m unittest \
  tests.test_lost_human_world_cover_project.LostHumanWorldCoverProjectTests.test_body_opening_v001_uses_exact_source_text_and_approved_layout -v
```

Expected: FAIL，因为 `body-opening-v001-layout.json`、HTML 和 PNG 尚不存在。

### Task 2: 生成可编辑正文首跨页和预览

**Files:**
- Create: `projects/lost-human-world-cover/body-opening/body-opening-v001.html`
- Create: `projects/lost-human-world-cover/body-opening/body-opening-v001-layout.json`
- Create: `projects/lost-human-world-cover/body-opening/body-opening-v001-preview.png`
- Create: `projects/lost-human-world-cover/body-opening/body-opening-v001-review.md`
- Test: `tests/test_lost_human_world_cover_project.py`

**Interfaces:**
- Consumes: Task 1 的验收合同、已批准章首页色彩与 `chapter-01.md` 前 10 段。
- Produces: 可直接浏览的 290 × 210 mm 首跨页，以及机器可验证的来源记录。

- [ ] **Step 1: 写布局 JSON**

布局记录使用以下闭合字段；`source_sha256` 已由 `shasum -a 256` 对当前只读原文计算：

```json
{
  "schema_version": "1.0",
  "layout_id": "BODY-OPENING-LOST-HUMAN-WORLD-CH01-V001",
  "project_id": "BOOK-LOST-HUMAN-WORLD",
  "source_path": "manuscript/chapter-01.md",
  "source_sha256": "380b13c561191e5f3a9b52dcad7c7cbb6976487ef6d58910bc032f214de932b8",
  "source_paragraph_range": [1, 10],
  "page_trim_mm": [145, 210],
  "spread_trim_mm": [290, 210],
  "left_text_start_mm": 54,
  "right_text_start_mm": 26,
  "running_header_template": "folio-outer",
  "test_folios": [6, 7],
  "design_spec_status": "approved",
  "text_layer": "editable-html"
}
```

- [ ] **Step 2: 写可编辑 HTML**

创建固定 290 × 210 mm 跨页。左页放源段落 1—5，右页放源段落 6—10；每段保留 `data-source-index`。CSS 必须包含：

```css
.spread { width: 290mm; height: 210mm; display: grid; grid-template-columns: 145mm 145mm; }
.left-page { padding: 54mm 22mm 24mm 18mm; }
.right-page { padding: 26mm 18mm 24mm 22mm; }
.text { font: 9.5pt/17.5pt "Source Han Serif SC", "Noto Serif CJK SC", "Songti SC", STSong, serif; color: #1C1B19; }
.text p { margin: 0 0 0.55em; text-indent: 2em; }
.entry-line { width: 14mm; border-top: 0.45pt solid #7A2428; margin-bottom: 6mm; }
```

页面根节点添加 `data-text-layer="editable"`；不得出现章号或章题。左页外侧页码为 6，右页外侧页码为 7，并标注为 `data-folio-status="provisional"`。

- [ ] **Step 3: 渲染 PNG 预览**

Run:

```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --headless=new --disable-gpu --hide-scrollbars --allow-file-access-from-files \
  --window-size=1740,1260 --force-device-scale-factor=1 \
  --screenshot="$PWD/projects/lost-human-world-cover/body-opening/body-opening-v001-preview.png" \
  "file://$PWD/projects/lost-human-world-cover/body-opening/body-opening-v001.html"
```

Expected: 1740 × 1260 PNG，左页存在渐入留白和短暗红线，右页为标准正文网格。

- [ ] **Step 4: 写检查记录**

`body-opening-v001-review.md` 必须记录：源 SHA、使用段落 1—10、正文未修改、HTML 真文字、两页无页眉、页码为测试值、无溢出，以及当前未生成 InDesign/PDF。

- [ ] **Step 5: 运行 GREEN 验证**

Run:

```bash
.venv/bin/python -m unittest tests.test_lost_human_world_cover_project -v
sips -g pixelWidth -g pixelHeight \
  projects/lost-human-world-cover/body-opening/body-opening-v001-preview.png
```

Expected: 项目测试全部通过；预览为 1740 × 1260。

- [ ] **Step 6: 运行相关回归**

Run:

```bash
.venv/bin/python -m unittest \
  tests.test_lost_human_world_cover_project \
  tests.test_component_kb_prompts \
  tests.test_component_kb_review -q
```

Expected: 全部通过；既有封面、章首页、Prompt 与 review 合同不回归。

- [ ] **Step 7: 记录版本控制边界**

Run:

```bash
git rev-parse --is-inside-work-tree
```

Expected: 当前目录不是 Git 仓库，因此不执行 `git add` 或 `git commit`；在最终报告中如实说明。
