# 建项字段

## 六类图书

`primary_category` 必须且只能取一个：

| 值 | 含义 |
|---|---|
| `life-memorial` | 人生纪念 |
| `family-memorial` | 家庭纪念 |
| `letters-diaries` | 书信 / 日记 |
| `essays-poetry` | 散文 / 诗歌 |
| `growth-memorial` | 成长纪念 |
| `collective-memorial` | 集体纪念 |

交叉属性写入 `tags`。不得为了分类而改动正文。

## 最小输入

- 项目：`project_id`、`title`、`confirmer`
- 路由：`mode`、`primary_mode`（仅混合模式）、`primary_category`、`tags`
- 页数：模板书固定页数；纪念书页数区间
- 素材：唯一 ID、类型、原始路径或预计路径、状态；可附来源、人物、时期与备注

素材路径是登记值，不代表文件已经存在。状态不是 `received` 时必须形成待确认项。

## 判断顺序

1. 固定页面槽位是否主导内容进入方式？是则有模板属性。
2. 大量文字是否需要先建立叙事与章节候选？是则有纪念书属性。
3. 两者皆是则选择 `hybrid`，由用户或项目负责人指定 `primary_mode`。
4. 信息不足时可创建草案，但缺失的决定必须进入 `open-items.json`；schema 所需的核心路由字段仍需在执行脚本前确认。
