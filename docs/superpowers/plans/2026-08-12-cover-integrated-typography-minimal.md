# 封面一体化文字最小稳定方案

日期：2026-08-12  
状态：已完成并安装

## 目标

让封面能够直接生成已确认的书名、副标题、作者或封面短文，同时保持结果可审核、失败可回退。

## 只保留五个环节

1. **项目文字登记**：生成模型只能使用项目中已经确认的文字。
2. **封面专用编译**：仅 `cover` 可以选择 `integrated-typography`；其他图书部件继续使用可编辑文字。
3. **绝对禁区**：ISBN、条码、二维码、定价、CIP 和机器编号永远不能进入生图。
4. **四项成图检查**：文字准确、没有多余文字、文字清晰可用、没有机器信息。任一失败就拒绝。
5. **可编辑回退**：保留同样的文字备份；模型文字不稳定时，使用无字背景加可编辑文字层，不反复修补错误图。

## 复用现有能力

- 继续使用现有案例检索、2—3 个案例字段映射和人工批准。
- 继续使用现有 Prompt、generation payload、authorization 和版本哈希链。
- 继续使用现有项目内图片审核与 pending promotion。
- 不再增加新的多层授权对象、路径协议或重复的竞态防线。

## 最小数据

```json
{
  "text_rendering_mode": "integrated-typography",
  "integrated_text": [
    {"text_id": "TITLE-001", "surface": "front", "role": "title", "value": "失落人间", "language": "zh-CN"},
    {"text_id": "SUBTITLE-001", "surface": "front", "role": "subtitle", "value": "在所有归途之外", "language": "zh-CN"},
    {"text_id": "AUTHOR-001", "surface": "front", "role": "author", "value": "早睡的猫", "language": "zh-CN"}
  ],
  "editable_text_backup": {
    "TITLE-001": "失落人间",
    "SUBTITLE-001": "在所有归途之外",
    "AUTHOR-001": "早睡的猫"
  }
}
```

## 四项审核

```text
integrated_text_exact
no_extra_text
typography_usable
machine_identifiers_absent
```

四项必须全部为真，才允许用户选择；否则直接重生无字背景或转可编辑文字层。

## 实施顺序

1. 用测试锁定旧模式兼容和新模式边界。
2. 实现最小文字守卫与双模式 Prompt。
3. 加入四项审核门。
4. 精简更新两个相关 Skills。
5. 将《失落人间》登记为正封三项文字，验证后回到案例和字体选择。

## 本阶段不做

- 不调用 `imagegen`。
- 不制作封底和书脊内容。
- 不生成 ISBN、条码、二维码、定价或 CIP。
- 不执行 InDesign。
- 不开发网页前端。
- 不修改 50 条封面知识库。
