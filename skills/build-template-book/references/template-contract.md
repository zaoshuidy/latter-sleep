# 模板契约

## `template-spec.json`

- `version`: 固定为 `1.0`
- `template_id`: 模板唯一标识
- `fixed_pages`: 固定总页数
- `pages[]`: 页定义
  - `page_number`: 从 1 开始的唯一页码
  - `family_id`: 页面家族标识
  - `slots[]`: 槽位定义
    - `slot_id`: 全书唯一
    - `slot_type`: `text` 或 `image`
    - `required`: 是否必填
    - `source_asset_id`: 已选素材；未选时省略
    - 文字槽：`capacity_chars`
    - 图片槽：`aspect_ratio`（宽 / 高）
    - `allow_repeat`: 明确允许复用同一素材时设为 `true`

## `asset-facts.json`

以素材 ID 为键。文字素材提供 `asset_type: text` 和只读统计值 `char_count`；图片素材提供 `asset_type: image` 和 `aspect_ratio`。统计值只用于适配判断，不复制或改写正文。

## 状态

- `ready`: 匹配可用
- `missing_required`: 必填槽未指定素材
- `unfilled_optional`: 可选槽未指定素材
- `missing_asset`: 指定素材不在事实表
- `type_mismatch`: 素材类型错误
- `duplicate_asset`: 未经允许重复使用
- `text_overflow`: 完整原文超出容量
- `ratio_mismatch`: 图片宽高比差异超过 5%
- `page_count_mismatch` / `invalid_template_spec`: 模板级问题
