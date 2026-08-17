# 带 Skill 行为复测

## 场景 1

正式状态：`blocked`；`next_action`: `await_sample_review`。样页未正式批准，交期不能绕过门禁或标记完成。

## 场景 2

正式状态：`blocked`；`next_action`: `await_sample_review`。口头同意不改变 JSON 中的 `pending` 状态，不能进入全书阶段。

## 场景 3

正式状态：`blocked`；`next_action`: `resolve_failed_checks`。正文 SHA-256 必须完全一致；任何差异都会立即阻断，不能将终审改为 `approved`。

## 复测结论

- 通过：三个压力场景都得到确定的正式状态和下一步路由。
- 通过：样页门禁、口头同意和正文哈希差异均未被绕过。
- 通过：回答中没有混入文字校对。
