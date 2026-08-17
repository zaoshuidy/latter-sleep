---
name: book-production-router
description: Use when starting a Chinese book-production project from manuscripts, photos, fixed templates, or mixed materials and the production mode, primary category, intake status, or next workflow must be determined.
---

# 图书生产入口

先建立项目事实，再进入制作。即使素材缺失，也要生成可继续补充的项目壳；不得假装已收到素材或已经成书。

## 建项流程

1. 读取 `references/intake-fields.md`，确认模式、主类别、页数条件和素材状态。
2. 将用户原始文件视为只读源。不得覆盖、改写、校对、删节、扩写或重排正文内容。
3. 只选择一个生产模式：
   - `template`：已有固定页结构，必须给出 `page_plan.fixed_pages`。
   - `memorial`：长文字驱动，必须给出 `page_plan.min_pages` 与 `max_pages`。
   - `hybrid`：两种条件同时存在，必须明确 `primary_mode`，先走主流程，再由另一流程补充。
4. 只选择一个 `primary_category`；其他类型写入 `tags`，不要把多个类别并列为主类别。
5. 每项素材标记 `received`、`missing`、`pending` 或 `unusable`。未知事实写入待确认项，不可补造。
6. 调用脚本生成且只生成三个建项产物：

```bash
python scripts/create_project.py intake.json PROJECT_DIR
```

产物固定为 `project-config.json`、`asset-manifest.json`、`open-items.json`。

## 路由

- `template` → `build-template-book`
- `memorial` → `plan-memorial-book`
- `hybrid` → 先执行 `primary_mode` 对应流程，再调用另一流程处理剩余页型；共享同一项目配置和素材清单。
- 页面系统已经批准，且用户明确要求“可翻阅 HTML、电子样书、flipbook、网页翻书” → `build-book-flipbook`。这是成书展示路由，不改变原生产模式，也不重新设计页面。
- 页面系统和最终页序已经批准，且用户要求 INDD、InDesign 校样或 PDF 校样 → Windows 使用 `build-indesign-book`。先运行 `proof`，只有 300 PPI、真实出血和可编辑排版条件全部满足后才允许 `print`。

不要在入口阶段承诺 DOCX、PDF、INDD 或成书文件。V1.2 不包含文字校对、版权页或交互式 Agent 前端；只有通过前序批准门禁后，才可输出离线 HTML 电子样书或调用 Windows InDesign 校样构建。

## 完成标准

- 三个 JSON 均通过共享 schema 校验。
- 模式、主类别、确认人和页数条件明确。
- 缺失素材进入 `open-items.json`，但不阻止建项。
- 下一步 Skill 路由唯一且可解释。

## 常见错误

- 有模板又有长文字时直接判为纪念书，而未识别 `hybrid`。
- 素材不齐就拒绝创建项目壳。
- 把预计交付物冒充为已生成文件。
- 在入口阶段修改原文或开始视觉设计。
