# 批准 PNG 的高清流畅翻页模式

适用于封面、目录、章首页和正文已经导出为批准的单页 PNG/JPEG，目标是最大限度保持视觉结果，并让浏览器翻页自然、离线、稳定。

## 已验证基线

- 引擎：项目内本地 `page-flip@2.0.7`，MIT。
- 每个物理页一张同尺寸图片；示例基线为 `1000 × 1448 px`。
- 使用 StPageFlip 原生 `loadFromImages`，不再给动画页叠加 HTML/CSS 视觉元素。
- 初始化前逐张预解码；全部成功后再创建阅读器。
- `flippingTime: 620`、`maxShadowOpacity: 0.20`，保留书页惯性但缩短拖沓感。
- `showCover: true`；不强制鼠标翻角，不手写旋转、阴影、层级或完成状态。

最小示意：

```js
await Promise.all(pageImages.map(async (src) => {
  const image = new Image();
  image.src = src;
  await image.decode();
}));

const pageFlip = new St.PageFlip(book, {
  width: 500,
  height: 724,
  size: "stretch",
  showCover: true,
  usePortrait: true,
  drawShadow: true,
  flippingTime: 620,
  maxShadowOpacity: 0.20
});
pageFlip.loadFromImages(pageImages);
```

## Retina / HiDPI 清晰度

StPageFlip 2.0.7 的 Canvas 默认 backing store 可能只等于 CSS 尺寸，高清 PNG 因此看起来发糊。使用项目内薄适配层修正 Canvas 像素密度，不修改上游依赖包：

1. 读取 Canvas 的 CSS 宽高。
2. 取 `devicePixelRatio`，为兼顾清晰度和内存将比例限制为最大 2。
3. 把 Canvas 实际宽高设为 `CSS 尺寸 × 比例`。
4. 对 2D context 使用 `setTransform(ratio, 0, 0, ratio, 0, 0)`。
5. 初始化、窗口 resize 和全屏切换后重新应用。

示例中单页 CSS 宽 500、高 724；双页 Canvas CSS 宽 1000、高 724。在 2x 屏幕上 backing store 应为 `2000 × 1448`，每个 `1000 × 1448` 源页因此能够按原始像素进入半幅页面。

适配层不得读取磁盘路径来重建或修改批准页面；只修正浏览器已加载图像的画布密度。不得把同一问题误处理为重复放大、锐化或重新生成源图。

## 搜索、文字与辅助功能

Canvas 动画页上不覆盖透明可选文字层，以免命中区域、缩放和翻页层级互相干扰。需要检索时，维护一份与物理页码绑定的**外置文字索引**，搜索结果只负责跳转页码；它不参与页面视觉渲染。

若交付必须直接选择正文或必须呈现硬封壳，请改用 HTML 模式，而不是混合两种渲染结构。

## 离线回退与版本策略

- 引擎、适配器、图片、字体和许可证全部使用项目相对路径，不访问 CDN。
- 图片解码或引擎初始化失败时，显示**顺序图片回退**，保证书页仍可按物理顺序阅读。
- 新的流畅版使用新文件名；保留上一版和源图片，不覆盖已批准文件。
- 版本对比页一次只加载一个 iframe；切换版本时替换 iframe 的 `src`，不要并行运行两套完整引擎。

## 验收清单

- 图片数量、尺寸、顺序和源文件哈希符合批准清单。
- 正封单页开场、桌面跨页、移动端单页、末页封底均正确。
- 画布 backing store 在 HiDPI 设备达到预期比例，且比例最大 2。
- 鼠标、触摸、按钮、左右键、目录跳转和全屏均可用。
- 快速连续翻页不卡死、无重复页、无空白闪烁。
- 断网可打开；无外网请求；引擎失败时顺序图片回退可读。
- 旧版文件哈希不变，可立即回退。
