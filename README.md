# wagtail-api-forms

User friendly html form builder. A customized Django Wagtail app.

## Features

* Expose API endpoint for forms, authentification via token (optional, configurable per form)
* Custom form fields:
  * Document file field
  * Image file field
  * Typeahead-Multiselect field ("select2")
  * Datetime and time fields with time picker for Firefox
* Embed page content - without header, footer etc. - via ``url?embed=true``. Useful for embedding only the form on third party sites.
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
* Branding with custom Logos, Favicon, colors etc.

### iFrame

```html
<style>
  iframe#waf-iframe {
    width: 1px;
    min-width: 100%;
  }
</style>
<iframe id="waf-iframe" src="https://fqdn.com/wagtail/formpage.html"></iframe>
<script src="https://fqdn/static/dist/js/jquery/jquery.min.js"></script>
<script src="https://fqdn/static/dist/js/iframeresizer/iframeResizer.min.js"></script> 
<script>
  iFrameResize({ log: false }, '#waf-iframe')
</script>
```

*Snippet from https://github.com/davidjbradshaw/iframe-resizer#typical-setup. Thanks to [davidjbradshaw](https://github.com/davidjbradshaw/iframe-resizer)*

## Usage

### Setup

See `docs/setup.md`

### Hints

* Docs are served at the URL `fqdn/docs/`.
* Attachment file objects could only be fetched with an authenticated request (from whitelisted ip address or basic auth)
* Attachment file objects could only be fetched if its status is ``av_passed=True`` for which the huey task queue must be running (or when virus checking facility is disabled via `USE_ANTIVIR_SERVICE=false` in `.env`)
