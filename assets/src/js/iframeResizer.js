// Parent side of iframe-resizer, for third party pages embedding a form via
// ?embed=true. Served as /static/iframeresizer/iframeResizer.js - keep both the
// entry filename and the exported function names, existing embeds rely on them.
import iframeResize from '@iframe-resizer/parent';

// Default to the GPLv3 license, matching the child page. An embedder holding a
// commercial key can still pass their own license option to override it.
const resize = (options = {}, target) =>
  iframeResize({ license: 'GPLv3', ...options }, target);

// iframeResize() is the v5 name, iFrameResize() the v4 one.
window.iframeResize = resize;
window.iFrameResize = resize;

// Resize every opted-in iframe, so an embedding page needs no inline script.
const autoInit = () => resize({}, 'iframe[data-waf-resize]');

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', autoInit);
} else {
  autoInit();
}
