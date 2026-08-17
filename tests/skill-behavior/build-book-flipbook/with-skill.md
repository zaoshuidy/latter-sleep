# GREEN：电子样书展示 Skill 生效

- 日期：2026-08-14
- 读取：`skills/build-book-flipbook/SKILL.md` 与 `references/stpageflip.md`
- 结果：PASS。

同一场景下，Agent 直接选择本地化 `page-flip@2.0.7` / StPageFlip，并给出以下最小行为：

1. 先核对获批物理页顺序、奇偶页和空白补位。
2. 每个单页直接进入主 HTML 的 `.book-page`，真实文字不栅格化。
3. 正封和封底为 hard，内页为 soft，`showCover: true`。
4. 翻页角度、z-index 与完成状态交给官方引擎；适配层只处理按钮、目录、键盘、页码、全屏和窄屏。
5. 交付主 HTML、本地引擎包、锁文件和 MIT 许可证；不增加 manifest。
6. 同时验收双击、静态服务、断网、末页封底和可选择正文。

Agent 明确拒绝：重做已批准设计、手写状态机、iframe、CDN、后端、数据库和为追求单文件而重写动画。与 RED 中的无路由和过重临时方案相比，行为已收敛到当前需要的展示结果。
