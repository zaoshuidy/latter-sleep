# 审核输入与门禁

`review-input.json` 包含：

- `version`、`project_id`
- `source_texts[]`: `source_id`、项目内相对路径 `path`、定稿 `expected_sha256`
- `production_checks`: 七个布尔值
- `gates`: 两个正式人工状态

七项制作检查：

| ID | 含义 |
|---|---|
| `toc_complete` | 目录覆盖全部已确认章节且页码对应 |
| `running_headers_consistent` | 页眉页脚内容、隐藏页和左右页规则一致 |
| `fonts_available` | 所选免费字体或方正会员字体在交付环境可用且许可已登记 |
| `no_overflow` | 文字、图片和版心无未处理溢出 |
| `images_resolution_ok` | 最终选图满足目标使用尺寸 |
| `page_numbers_continuous` | 页码逻辑连续，隐藏页不破坏编号 |
| `prompts_complete` | 所有生成图具有独立 Prompt 和版本记录 |

第一次门禁审核代表性样页，第二次门禁审核完整全书。门禁状态必须落入 JSON；聊天、电话或口头意见不改变状态。
