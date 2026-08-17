---
name: plan-memorial-book
description: Use when a Chinese memoir, life-story, family-history, diary, letter, growth, or collective-memory project needs a content map, multiple narrative structures, chapter-title candidates, or a designed table-of-contents brief without changing finalized body text.
---

# 纪念书策划

先理解材料，再设计结构。正文是只读证据；本 Skill 不校对、不改写、不删节、不扩写，也不把候选目录直接当成已确认目录。

## 产物

- `content-map.json`：人物、时间、地点、事件、主题、图片关联、信息缺口和原文 SHA-256。
- `structure-options.json`：2～3 套由真实材料支持的叙事候选。
- `toc-brief.json`：可供后续版式设计的目录内容与标题来源记录。

可用脚本从结构化输入生成三项产物：

```bash
python scripts/plan_memorial.py plan-input.json OUTPUT_DIR
```

## 工作流程

1. 读取所有定稿文字，按文件或已确认内容单元记录来源 ID；生成原文哈希。
2. 按 `references/content-map.md` 提取可追溯事实。没有来源的内容写“待确认”，不得补造。
3. 基于材料特征提出 2～3 套结构。时间、主题、地点、关系、事件、物件、照片和混合结构地位相同，不设固定优先级。
4. 每套结构只映射内容单元顺序，不改动单元内部文字。说明适配理由、优势、风险和图片机会。
5. 按 `references/title-policy.md` 生成标题候选；始终并列保存原始标题、候选标题、来源单元与确认状态。
6. 形成目录设计 brief，而不是使用文件夹名自动排一张普通列表。目录可规划单页、跨页或多页结构，实际视觉设计交给 `design-book-editorial`。

## 人工确认

由人选择叙事结构和标题后才可锁定目录。未确认候选必须保持 `pending`。内容地图中的缺口不能阻止提出候选，但必须清晰显示不确定性。

## 完成标准

- 三项产物通过 schema。
- 候选为 2～3 套且均引用真实内容单元。
- 目录标题可追溯，未把推测写成事实。
- 生成前后所有源文字 SHA-256 相同。
- 不处理版权页、文字校对、InDesign 或最终排版。
