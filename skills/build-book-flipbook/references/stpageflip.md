# StPageFlip 离线接入

## 固定依赖

- 包：`page-flip@2.0.7`
- 上游：`https://github.com/Nodlik/StPageFlip`
- 许可：MIT
- 浏览器文件：`node_modules/page-flip/dist/js/page-flip.browser.js`

项目目录执行：

```bash
npm install --prefix ebook/vendor page-flip@2.0.7 \
  --save-exact --ignore-scripts --no-audit --no-fund
```

HTML 只引用本地文件，不使用 CDN。

## 最小结构

```html
<div id="book">
  <section class="book-page" data-density="hard">正封</section>
  <section class="book-page">内页</section>
  <section class="book-page" data-density="hard">封底</section>
</div>
<script src="vendor/node_modules/page-flip/dist/js/page-flip.browser.js"></script>
<script>
  const pageFlip = new St.PageFlip(document.getElementById("book"), {
    width: 500,
    height: 724,
    size: "stretch",
    minWidth: 280,
    maxWidth: 500,
    minHeight: 406,
    maxHeight: 724,
    showCover: true,
    usePortrait: true,
    drawShadow: true,
    flippingTime: 850
  });
  pageFlip.loadFromHTML(document.querySelectorAll(".book-page"));
</script>
```

`data-density="hard"` 只给正封和封底。内部纸页保持默认 soft。

## 薄适配层

- `flipNext()` / `flipPrev()`：带动画翻页。
- `turnToPage(index)`：目录直达。
- `flip` 事件：更新页码、按钮、URL hash 与辅助技术提示。
- `changeOrientation`：桌面双页与窄屏单页状态提示。
- 暴露 `window.bookPageFlip`，只用于浏览器验收。

不要自行维护页面旋转角、z-index 或翻页完成状态。

## 离线与失败回退

- `package-lock.json` 必须锁定 2.0.7，许可证随包保留。
- 所有图片与字体使用项目相对路径。
- `.js .book-page { display: none; }` 只在引擎成功前后由脚本控制；`noscript` 或加载失败时让物理页顺序可读。
- 验收时同时用 `file://` 与本地静态服务打开。
