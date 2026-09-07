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
    width: 1px;
    min-width: 100%;
    border: 0;
  }
</style>
<iframe data-waf-resize src="https://fqdn.com/wagtail/formpage.html?embed=true"></iframe>
<script async src="https://fqdn/static/iframeresizer/iframeResizer.js"></script>
```

Every iframe carrying the `data-waf-resize` attribute is picked up automatically, so no
inline script is needed. To size an iframe yourself instead, call `iframeResize(options,
selector)` once the script has loaded; the options are documented at
<https://iframe-resizer.com/api/parent/>. The v4 spelling `iFrameResize()` still works,
so existing embeds keep running unchanged.

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
