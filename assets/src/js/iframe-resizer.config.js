// Child side settings of iframe-resizer. Settings made here take precedence over
// the options an embedding page passes to iframeResize(), so third party
// embedders need no configuration. See https://iframe-resizer.com/api/child/
//
// wagtail-api-forms is licensed under the AGPL-3.0, so iframe-resizer is used
// under the terms of its GPLv3 open source license. See https://iframe-resizer.com/gpl
//
// targetOrigin stays at its default '*': a form can have several embedding sites,
// the frame-ancestors CSP already decides who may frame a form page, and the
// messages to the parent page only carry the page size.
window.iframeResizer = {
  license: 'GPLv3',
  // v5 auto detects the size calculation. This overrides the deprecated
  // heightCalculationMethod (e.g. 'lowestElement') of older embed snippets.
  heightCalculationMethod: 'auto',
  // After a submit the iframe shows the validation errors or the thank-you page,
  // while the embedding page is still scrolled down to the submit button.
  onReady() {
    if (document.body.hasAttribute('data-waf-submitted')) {
      window.parentIframe.scrollToOffset(0, 0);
    }
  },
};
