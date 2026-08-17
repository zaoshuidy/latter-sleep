---
name: design-book-editorial
description: Use when a Chinese book project needs researched visual directions, editable table-of-contents design, a consistent chapter-opener master, reusable running-header templates, category-aware font choices, page families, or representative page samples.
---

# 图书编辑设计

从已确认内容与案例中形成全书视觉系统。目录、章首页、页眉页脚和正文文字必须保留为可编辑真文字；不得把整页生成为位图。

## 启动条件

读取项目配置、内容地图或模板页计划、素材清单、纸船品牌配置、`toc-brief.json` 和正式案例索引。先从当前实际 `SKILL.md` 的绝对路径解析套件根目录，不依赖当前工作目录：

```bash
SKILL_FILE="/absolute/path/to/current/skills/design-book-editorial/SKILL.md"
SUITE_ROOT="$(cd -P "$(dirname "$SKILL_FILE")/../.." && pwd)"
SUITE_PYTHON="$SUITE_ROOT/.venv/bin/python"
"$SUITE_ROOT/.venv/bin/python" \
  "$SUITE_ROOT/skills/design-book-editorial/scripts/check_case_library.py" \
  "$SUITE_ROOT/knowledge/indexes/design-case-index.json"
```

随后读取 `$SUITE_ROOT/knowledge/indexes/approved-project-case-index.json`。只使用 `status=approved-positive`、`page_component` 与当前部件一致且全部 artifact SHA-256 仍匹配的记录，作为经过用户验证的方法证据。它不能替代外部出版案例调查、不能计入下述 `confirmed` 数量，也不得作为一比一套用模板；项目专有文字、页码与精确坐标属于不可复制内容。

任何目标部件少于 10 个 `confirmed` 案例时，列出缺口并继续调查，不得把待核验案例用于正式方向。

涉及封面、目录、章首页或插画装饰时，在形成正式方向前必须完整执行 `references/component-knowledge-retrieval.md`。用户的简洁映射先转写为两份 `status=draft` selection；schema 和 `validate_selection_prompt_safety` 均通过后才完整回显并报告 ID 与 SHA。用户二次批准对应 ID 与 SHA 后才能改为 `status=approved` 并验证。真实最终文字只进入 metadata／可编辑 overlay，不进入 mapping prose。门禁未关闭时只展示候选或报告缺口。本 Skill 不得调用 `imagegen`。

封面方向确定后只增加一个文字模式决定：`editable-overlay`（稳定无字底图）或 `integrated-typography`（文字参与构图）。后者仅限 `cover`，并在生成前完整列出正封、封底、书脊的已确认文字及可编辑备份；ISBN、条码、二维码、定价、CIP 永远不进入生图。非视觉事实一次询问，视觉判断循序渐进；本 Skill 仍只设计和登记，不调用 `imagegen`。

## 直接成稿路由

当同一项目已有经用户批准的稳定视觉系统，目标页面的真实文字、开本、页面角色和操作权限均已齐全，且用户明确委托“直接完成、生成后再看”时，本路由优先于下方标准流程中的双方向与独立规格步骤：沿用已批准系统，直接生成一版可视 V001 并展示给用户，省略单独的书面设计规格和多方向选择轮次。只有真实事实缺失、授权不足或目标页面与既有系统存在实质冲突时，才把全部必要的非视觉问题一次性询问。

该路由不跳过可编辑文字、真实内容、身份边界、页面溢出检查、文件验证、项目登记和生成结果的人工评判；也不解除组件知识库、付费生成、`imagegen`、版权或生产文件原有门禁。用户未明确授权扩展到同类全部页面时，只提交当前 V001，不自动批量扩展。

## 设计流程

1. 按 `references/case-routing.md` 选择多来源案例；组件视觉参考同时服从组件知识库门禁。记录借鉴项与变化项，最终方案不得与单一案例一比一相同。
2. 标准路由用项目真实书名、章节名、目录项、正文片段和已认可图片提出两套视觉方向；直接成稿路由沿用已批准方向，仅生成当前页面的一个 V001。不得用占位文案伪装样页。
3. 标准路由每套输出独立 `design-genome.json`：颜色、字体、网格、目录、一个章首页母版、页眉页脚模板和 5～8 个核心页面家族；直接成稿路由复用项目现有设计基因，不重复制作独立书面规格。
4. 字体遵循 `references/fonts.md`。正文字体、字号和行距按出版基础规则设定，不作为自由创意变量。普通成年读者、145 × 210 mm 文学小说满足默认条件时，直接使用 reference 中的正文基线，不再逐项询问用户；只有读者年龄／无障碍需求、出版社 house style、开本或字体授权发生实质变化时才重新确认。
5. 目录按 `references/toc.md` 单独设计，可为单页、跨页或多页；必须处理长短标题、层级、页码关联和溢出。
6. 同一本书只使用一个章首页母版，图片可选；遵循 `references/chapter-opener.md`。
7. 从三个 JSON 模板中选择页眉页脚结构，只替换项目字体、颜色和内容变量；遵循 `references/running-headers.md`。
8. 生成代表性样页或直接成稿 V001，进入生成结果的人工评判。未确认不得扩展到全书。

## 输出边界

- 标准路由输出两套视觉方向、设计基因、样页规格、页面家族和页眉页脚选择；直接成稿路由只输出当前可视 V001、必要结构数据与验证记录。
- 封面只形成设计概念与标准化提示词所需字段；本 Skill 不生成图片，也不得调用 `imagegen`。
- 不执行文字校对、版权页、InDesign、PDF 或印刷生产。

## 完成标准

- 标准路由的两套方向均使用真实项目内容且来源案例可追溯；直接成稿路由必须引用当前项目已批准视觉系统及真实内容。
- 目录、章首页和正文文字始终保持可编辑；封面若选 `integrated-typography`，仍必须保存同值可编辑备份。
- 目录通过三页或目标页数溢出检查。
- 章首页全书统一，页眉页脚隐藏规则一致。
- 案例借鉴项和至少一项实质变化均已记录。
