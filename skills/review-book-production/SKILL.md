---
name: review-book-production
description: Use when a Chinese book-production project needs source-text integrity, TOC and running-header consistency, font and asset checks, overflow detection, image-record validation, representative-sample approval, or final human review status.
---

# 图书生产审核

审核只判断制作完整性与一致性，不做文字校对，也不修改正文。任何口头同意、交期压力或“只差一点”的哈希差异都不能替代正式门禁。

## 输入与执行

项目根目录提供 `review-input.json`，字段见 `references/review-gates.md`。运行：

```bash
python scripts/review_project.py PROJECT_ROOT
```

输出 `review-report.json` 与 `gate-status.json`。

## 检查顺序

1. 重新计算每份定稿正文 SHA-256；任一不一致立即阻断。
2. 检查目录章节覆盖、页眉对应、字体可用、无溢出、图片分辨率、页码连续和 Prompt 完整。
3. 读取 `sample_review`：只有正式状态 `approved` 才能扩展全书。口头同意可写备注，但不能自动改状态。
4. 全书完成检查后读取 `final_review`：只有正式 `approved` 且所有检查通过，项目才可标记完成。

## 两级门禁

- `sample_review`: `pending/approved/rejected`
- `final_review`: `pending/approved/rejected`

门禁名称固定，不增加“有条件通过”来绕过。`sample_review` 未批准时路由为 `await_sample_review`；样页批准而终审未批准时为 `await_final_review`；检查失败时为 `resolve_failed_checks`。

## 输出边界

报告可指出文件、槽位、页码或素材记录问题，但不得建议改写、润色或校对正文。版权页不属于本审核项。最终门禁正式通过后，批准的物理页可路由到 `build-indesign-book` 生成 Windows InDesign 校样；校样不自动取得印刷批准。

## 完成标准

- 源正文哈希完全一致。
- 七项制作检查全部通过。
- 两个人工门禁均为正式 `approved`。
- `review-report.json` 通过 schema，状态为 `approved` 且下一步为 `complete`。
