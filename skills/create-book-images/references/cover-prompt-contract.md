# 封面标准提示词

封面只选择一种文字模式：

| 模式 | 用途 | 失败处理 |
|---|---|---|
| `editable-overlay` | 稳定的无字底图 | 用可编辑文字层完成书名等内容 |
| `integrated-typography` | 文字需要参与封面构图 | 任一文字检查失败即重生或回退 |

一体化模式必须由 production compiler 输出：

- `generation_constraints.readable_text=exact-project-text`
- 结构化 `integrated_text`
- 同值 `editable_text_backup`
- 独立 `INTEGRATED_TEXT` block

允许的内容只有项目已确认的正封、封底和书脊文字。案例原文字、模型补写文案和未登记字符串全部禁止。ISBN、条码、二维码、定价、CIP 是绝对禁区，即使被塞进 title、short-note 或自由 Prompt 也必须拒绝。

成图后检查：

1. `integrated_text_exact`
2. `no_extra_text`
3. `typography_usable`
4. `machine_identifiers_absent`

四项全部为 true 才能进入人工选择。任一失败时，不反复修补错误图；优先重生一次，仍不稳定就回退到 `editable-overlay` 和可编辑文字层。

两种模式都必须保留参考案例组合与变化记录，不得一比一复刻。
