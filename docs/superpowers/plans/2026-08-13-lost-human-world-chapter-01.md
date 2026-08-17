# 《失落人间》第一章执行计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 完成约 3000 字的第一章《车窗里的故乡》，核验叙事边界，并为下一阶段章首页测试提供真实文字。

**Architecture:** 正文与视觉制作分离。本阶段只产生可编辑 Markdown 正文和一份简短核验记录；用户认可正文之后，章首页设计才读取章名与开篇文字，不将正文写入图片。

**Tech Stack:** Markdown、Python 标准库（仅做字数与禁用表达检查）、人工文学复核。

## Global Constraints

- 第三人称限知，主人公无姓名，始终称“他”。
- 场景为夜间长途车上的归乡途中。
- 语言克制、含蓄，以车窗、灯光、空座位和旧电话号码承载情绪。
- 不煽情、不总结主题、不集中交代生平、不模仿特定作者。
- 本阶段不生成章首页图片，不修改已确认封面。

---

### Task 1：创作第一章正文

**Files:**
- Create: `projects/lost-human-world-cover/manuscript/chapter-01.md`

**Interfaces:**
- Consumes: `docs/superpowers/specs/2026-08-13-lost-human-world-chapter-01-design.md`
- Produces: 章名、完整正文、可供章首页测试使用的真实开篇文字。

- [ ] **Step 1：建立章节文件**

文件只包含一级章名和连续正文，不加入创作说明、摘要或占位符。

- [ ] **Step 2：完成开场**

在夜间长途车中呈现父亲去世的短消息；通过人物动作和屏幕状态建立事件，不解释全部家庭背景。

- [ ] **Step 3：完成中段**

使用车窗倒影、沿途灯光、空座位和旧号码触发片段记忆；让城市经验与家庭失去自然浮现，不使用主题口号。

- [ ] **Step 4：完成结尾**

车辆进入故乡辖区；以“认得所有地名，却没有可以直接前往的家”形成章节闭合，不提前写出整部小说结局。

### Task 2：正文核验与交付

**Files:**
- Read: `projects/lost-human-world-cover/manuscript/chapter-01.md`
- Create: `projects/lost-human-world-cover/manuscript/chapter-01-review.md`

**Interfaces:**
- Consumes: Task 1 的完整正文。
- Produces: 字数、视角、姓名、结构和文学边界核验结果。

- [ ] **Step 1：运行机械检查**

运行：

```bash
python3 - <<'PY'
from pathlib import Path
p = Path('projects/lost-human-world-cover/manuscript/chapter-01.md')
text = p.read_text(encoding='utf-8')
body = text.split('\n', 1)[1]
han = sum('\u4e00' <= c <= '\u9fff' for c in body)
assert text.startswith('# 第一章 车窗里的故乡\n')
assert 2400 <= han <= 3600, han
assert 'TODO' not in text and '待补' not in text
print({'han_characters': han, 'heading': 'pass', 'placeholders': 'pass'})
PY
```

预期：标题、篇幅和占位符检查通过。

- [ ] **Step 2：人工复核叙事合同**

逐项确认：主人公无姓名；没有全知视角越界；四个意象自然进入；父亲去世消息出现在开场；结尾落在故乡地名与无处可去的反差；没有“异化”“不被接纳”等主题解释句。

- [ ] **Step 3：记录核验结果**

在 `chapter-01-review.md` 中写明实际汉字数及上述六项 Pass/Fail；发现问题时只修正文，不改变已批准故事入口。

- [ ] **Step 4：交用户审阅**

提供正文文件与核验文件。只有用户认可第一章后，才进入章首页设计与生成。
