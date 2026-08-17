(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.StPageFlipHiDpi = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function () {
  'use strict';

  function normalizeRatio(value) {
    const numeric = Number(value);
    if (!Number.isFinite(numeric)) return 1;
    return Math.min(2, Math.max(1, numeric));
  }

  function resizeCanvasForPixelRatio(canvas, devicePixelRatio) {
    const rect = canvas.getBoundingClientRect();
    const ratio = normalizeRatio(devicePixelRatio);
    const width = Math.max(1, Math.round(rect.width * ratio));
    const height = Math.max(1, Math.round(rect.height * ratio));
    const changed = canvas.width !== width || canvas.height !== height;

    if (changed) {
      canvas.width = width;
      canvas.height = height;
      const context = canvas.getContext('2d');
      if (context) context.setTransform(ratio, 0, 0, ratio, 0, 0);
    }

    return { changed, ratio, width, height };
  }

  function install(pageFlip, bookElement) {
    const view = bookElement.ownerDocument.defaultView;
    let scheduledFrame = 0;

    const apply = function () {
      const canvas = bookElement.querySelector('canvas');
      if (!canvas) return null;
      const result = resizeCanvasForPixelRatio(canvas, view.devicePixelRatio || 1);
      bookElement.dataset.canvasPixelRatio = String(result.ratio);
      if (result.changed) pageFlip.update();
      return result;
    };

    const schedule = function () {
      if (scheduledFrame) view.cancelAnimationFrame(scheduledFrame);
      scheduledFrame = view.requestAnimationFrame(function () {
        scheduledFrame = 0;
        apply();
      });
    };

    view.addEventListener('resize', schedule, { passive: true });
    bookElement.ownerDocument.addEventListener('fullscreenchange', schedule);
    apply();

    return {
      apply,
      destroy: function () {
        if (scheduledFrame) view.cancelAnimationFrame(scheduledFrame);
        view.removeEventListener('resize', schedule);
        bookElement.ownerDocument.removeEventListener('fullscreenchange', schedule);
      }
    };
  }

  return { resizeCanvasForPixelRatio, install };
});
