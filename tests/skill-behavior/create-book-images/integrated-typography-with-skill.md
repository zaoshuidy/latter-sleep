# Integrated Typography With Skill（GREEN）

日期：2026-08-12

## 同一压力请求的受控结果

组件为 `cover`，因此可以使用 `integrated-typography`。本次只登记：

```text
front/title=失落人间
front/subtitle=在所有归途之外
front/author=早睡的猫
back=empty
spine=empty
```

三项均同步保存为可编辑文字层备份。ISBN、条码、二维码、定价、CIP 不得进入 Prompt 或成图。

当前只完成文字登记，不会调用 `imagegen`。仍需先完成案例字段映射、字体选择、selection ID + SHA 批准，并另行取得实际生图与费用授权。

成图后必须同时通过：`integrated_text_exact`、`no_extra_text`、`typography_usable`、`machine_identifiers_absent`。任一失败就拒绝该图；优先重生一次，仍不稳定则回退到无字背景与可编辑文字层。
