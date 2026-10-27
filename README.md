# wagtail-api-forms

User friendly html form builder. A customized Django Wagtail app.

Wagtail as a standalone builder for form pages or simply forms.

## Features

*Building upon the feature set of [Wagtail form builder](https://docs.wagtail.org/en/latest/reference/contrib/forms/) and customized to provide the following additional features.*

* Branding with custom Logos, Favicon, colors etc.
* Expose API endpoint for forms, authentification via token (optional, configurable per form)
* Custom form fields:
  * Document file field
  * Image file field
  * Typeahead-Multiselect field ("select2")
  * Datetime and time fields with time picker for Firefox
* Embed page content - without header, footer etc. - via `url?embed=true`. Useful for embedding only the form on third party sites.
  * iFrame autoresizing
  * Handles Content Security Policy (CSP). See `.env`.
* Multilingual
* Captcha (optional, configurable per form)
* Protect uploaded files (images and documents) via
  * filenames prefixed with an UUID
  * files could only be fetched from an authenticated request, and/or a whitelisted IP address
* Validates incoming files for:
  * maximum file size
  * file extension
  * file mime type
  * virus scan (via clamav in docker, done async via task queue `huey`)

### iFrame

Embed a form on a third party page. Note the `?embed=true` parameter, which strips
the navbar and footer, and enables the iFrame autoresizing:

```html
<style>
  iframe[data-waf-resize] {
    width: 100%;
    height: 100vh; /* until the first resize, and a scrollable fallback without JS */
    border: 0;
  }
</style>
<iframe
  data-waf-resize
  title="Contact form"
  src="https://fqdn.com/wagtail/formpage.html?embed=true"
></iframe>
<script async src="https://fqdn/static/iframeresizer/iframeResizer.js"></script>
```

Every iframe carrying the `data-waf-resize` attribute is picked up automatically, so no
inline script is needed. Give each iframe a `title` describing the form for screen
readers; if it is missing, the form page's title is used.

The form page itself takes care of the rest, so embedding sites need no configuration:

* the iframe-resizer license (see below)
* the height calculation: iframe-resizer detects the most suitable method on its own,
  and a `heightCalculationMethod` passed by the embedding page is ignored
* after a submit, the embedding page scrolls to the top of the form, so the validation
  errors or the thank-you text are visible

To size an iframe yourself instead, call `iframeResize(options, selector)` once the
script has loaded, e.g. for an iframe inserted after the page has loaded (only iframes
present on page load are picked up automatically), or `iframeResize({ log: 'expanded' },
'#my-form')` to debug the sizing in the browser console. The options are documented at
<https://iframe-resizer.com/api/parent/>; leave `waitForLoad` off, as it can stop the
asynchronously loaded script from initialising. The v4 spelling `iFrameResize()` still
works, so existing embeds keep running. Options from older snippets that iframe-resizer
5 no longer needs:

| v4 option                                   | iframe-resizer 5                              |
| ------------------------------------------- | --------------------------------------------- |
| `heightCalculationMethod`                   | remove, the method is detected automatically  |
| `minHeight`, `maxHeight`                    | CSS `min-height`, `max-height` on the iframe  |
| `sizeHeight`, `sizeWidth`, `autoResize`     | `direction` (default `'vertical'`)            |

Troubleshooting, see the browser console of the embedding page:

* *has not responded within 5 seconds*: the `src` lacks `?embed=true`, so the form page
  does not load the resizer.
* The browser refuses to display the iframe: the embedding site is missing from
  `FORMBUILDER_CSP_FRAME_ANCESTORS`.
* A *GPLv3 License Version* notice, once per browser session, is expected.

Only form pages can be embedded, and only by the sites listed in
`FORMBUILDER_CSP_FRAME_ANCESTORS` (see `env.template`); all other pages, the admin
included, only allow framing by this site itself.

*Autoresizing is provided by [iframe-resizer](https://iframe-resizer.com) by
[davidjbradshaw](https://github.com/davidjbradshaw/iframe-resizer), used under the terms
of its GPLv3 open source license. The license key is set on the form page, so embedding
sites do not have to configure one.*

## Usage

### Setup

See `docs/setup.md`

### Tests

The test suite uses `pytest` + `pytest-django`. Install the dev dependencies and run:

```bash
pip install -r requirements-dev.in
pytest
```

Config lives in `pytest.ini`; tests live next to the code they cover (e.g. `wagtail_api_forms/formpages/tests/`).

### Hints

* Docs are served at the URL `fqdn/docs/`.
* Attachment file objects could only be fetched with an authenticated request (from whitelisted ip address or basic auth)
* Attachment file objects could only be fetched if its status is ``av_passed=True`` for which the huey task queue must be running (or when virus checking facility is disabled via `FORMBUILDER_USE_ANTIVIR_SERVICE=false` in `.env`)
