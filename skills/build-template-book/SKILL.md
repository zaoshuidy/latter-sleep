---
name: build-template-book
description: Use when producing a fixed-format Chinese template book whose page count, text fields, image slots, crop ratios, or required assets are predetermined and must be mapped without rewriting source text.
---

# 模板书制作

把已确认素材映射到固定页面与槽位，先报告冲突，再交由人决定如何处理。模板不是修改原文的许可。

## 输入与产物

读取 `project-config.json`、`asset-manifest.json` 和符合 `references/template-contract.md` 的 `template-spec.json`。生成：

- `page-plan.json`：固定页序、页面家族、素材映射和溢出项。
- `slot-report.json`：每个槽位的状态、原因与可行处理动作。

运行：

```bash
python scripts/validate_slots.py template-spec.json asset-facts.json PROJECT_ID OUTPUT_DIR
```

## 工作顺序

1. 校验固定页数、页码、槽位 ID 和页面家族；正式项目使用 5～8 个页面家族。
2. 按槽位逐项匹配素材，不得静默遗漏必填槽或重复使用素材。
3. 文字槽仅比较完整原文的字符量与容量；不得删字、改写、概括、拆散原段或用不合行业规范的字号硬塞。
4. 图片槽检查素材存在性与宽高比。纪实照片只允许恢复、裁切和基础调整；不得重绘成虚假纪实。
5. 把所有问题写入报告。未解决问题存在时，状态不能写成完成。

## 溢出处理边界

文字溢出只允许建议：增加可变页、换用容量更大的已批准页面家族、保持原文转到后续页，或交由人工处理。不得自动修改正文。

图片比例不符可建议：选择更匹配的图片、在不损害关键内容时调整裁切比例，或交由人工处理。

固定页数确实不可变化时，冲突必须进入人工审核；不得为了“按模板完成”而隐藏问题。

## 完成标准

- 固定页数与页面定义一致。
- 所有必填槽均有明确状态。
- `slot-report` 每项含 `slot_id/status/source_asset_id/reason/suggested_actions`。
- 原文哈希和原始素材不变。
- 版权页、校对、InDesign 执行不在本 Skill 范围内。
