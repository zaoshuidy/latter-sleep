---
name: evolve-book-skills
description: Use when approved book-production cases, repeated corrections, failed reviews, accepted images, weekly knowledge maintenance, candidate Skill evaluation, version proposals, or rollback decisions need to be managed.
---

# 图书 Skill 进化

每周维护知识库；有证据时提出升级，但绝不自动覆盖正式 Skill。上游完整原件不可修改，旧案例和负面案例只归档、不删除。

## 每周维护

1. 收集本周新增的已确认案例、人工认可图片、失败审核和重复纠正。
2. 运行 `scripts/weekly_maintenance.py` 生成 `weekly-report.md` 与归档移动清单。
3. 认可图片可自动进入知识库索引；过期、重复和负面案例进入归档计划，保留原路径、目标路径和原因。
4. 报告只列新增、归档、失效索引、上游更新候选和进化候选；不得永久删除。
5. `knowledge/upstream/` 内的完整快照不移动、不修改。新上游版本另存新目录，只提出索引切换候选。

## 候选评估

运行：

```bash
python scripts/evaluate_candidate.py baseline.json candidate.json evolution-proposal.json
```

升级门槛全部满足才可得到 `proposed`：

- 同一组确认案例不少于 15 个；
- 候选平均分相对正式版提升至少 10%；
- 任何单例都不能回归；
- 具有可用回滚路径。

指标通过仍只是 `proposed`，`human_approval` 保持 `pending`。只有负责人正式批准后，提案状态才能改为 `approved`；执行切换和保留旧版是后续受控发布动作。

## 评估记录

按 `references/evaluation-record.md` 保存案例 ID、评分依据、基线 / 候选分数、回归列表、人工决定和回滚位置。不能用星标数量替代行为测试；GitHub 星标只用于发现成熟机制。

## 完成标准

- 每周报告和归档清单可追溯。
- 负面案例仍可用于回归测试。
- 进化提案通过 schema，阈值计算可复现。
- 未经人工批准不改正式版本。
- 上游原件逐文件哈希不变。
