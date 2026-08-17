# 评估记录

每个测试案例必须来自已确认项目或保留的负面案例，并包含：

- `case_id`、图书类别、输入摘要和预期行为
- 正式版分数、候选版分数与评分依据
- 是否回归及失败证据
- 评估日期与评估人 / 工具版本

提案记录：`case_count/baseline_score/candidate_score/improvement/regressions/human_approval/rollback_path/status`。改动理由、影响范围和人工决定另行保留。回滚路径必须指向未被覆盖的正式旧版。

人工决定只有 `pending/approved/rejected`。指标通过不等于人工批准。
