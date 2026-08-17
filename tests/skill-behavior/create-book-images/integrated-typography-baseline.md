# Integrated Typography Baseline（RED）

日期：2026-08-12
阶段：修改 Skill 与生产实现之前

## 固定压力请求

为 `cover` 生成 integrated typography：

- `front/title=失落人间`
- `front/subtitle=在所有归途之外`
- `front/author=早睡的猫`
- 封底和书脊为空
- 禁止 ISBN、条码、二维码、定价、CIP
- 保留可编辑备份
- 说明成图后的逐字审核与晋升门

## 实际失败

用当前 production compiler 将 `text_rendering_mode`、`integrated_text` 和
`editable_text_backup` 加入现有有效 cover output spec。编译器返回：

```text
ValueError: output_spec has invalid fields; missing=[]; unknown=['editable_text_backup', 'integrated_text', 'text_rendering_mode']
BASELINE_EXIT=17
```

这证明旧系统没有可通过的封面一体化文字合同。当前 Prompt schema 只允许
`generation_constraints.readable_text=none`，review schema 也没有逐字、额外文字、
表面绑定、机器标识和备份完整性检查。因此不能通过删除守卫或手改已编译 JSON
来伪装成已支持。

## 受保护基线

```text
e3ba66bcaa197066d481bf4f7012b1b87d5ae4a1f7ddfb2c296d51eeb3d75944  skills/design-book-editorial/SKILL.md
53cbd43305c90569b800aaf9e0ec2adc65777303431b28f12ef4e30ae2cef2d7  skills/create-book-images/SKILL.md
bc751ac2b2c30e15b1c69449862bc130387f2982294ef1c884749c5eecedffcb  skills/create-book-images/references/component-prompt-pipeline.md
c67f0ca20ff962c1c68fd99a095b60c9bba5f9ccf93e208748aac9a5e8ed0351  knowledge/book-component-libraries/cover/manifest.json
029d80f1b05f674ca42dc7fc630ff701c27bb3a34f5f64e23625fa0847804cfd  cover-library-tree
```

本基线没有调用 `imagegen`，也没有修改知识库。
