# RED 基线：现有 Skill 无法路由电子样书

- 日期：2026-08-14
- 场景：文学小说已有获批封面、目录、章首页与正文；要求用成熟 GitHub 包制作离线 HTML 翻页书。
- 可用 Skill：仅 `book-production-router` 与 `design-book-editorial`，不提供任何 flipbook 规则。
- 结果：FAIL。

基线 Agent 明确指出：入口 Skill 把网页排除在 V1 之外，编辑设计 Skill 也没有整书装配、翻页引擎、本地依赖或浏览器验收协议，因此“无可解释的下一步 Skill 路由”。随后只能临时推断出 iframe、manifest、页面拆分目录和多份报告，流程明显超过当前交付所需。

需要新 Skill 固定的最小行为：

1. 展示阶段独立于编辑设计。
2. 使用 StPageFlip，不手写状态机。
3. 页面直接嵌入主 HTML，不使用 iframe。
4. 只交付主 HTML、本地依赖与许可证。
5. 保留真实文字与已批准设计，断网验收。
