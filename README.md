# wagtail_api_forms

User friendly html form builder. A customized Django Wagtail app.

> :warning: Do **not** allow the webserver to serve ``_data/attachments/`` files - these files are served by Django to check for various criteria (is authenticated, from whitelisted remote ip, virus checked etc.).

## Features

* Enable API endpoint for forms, authentification via token
* Custom form fields:
  * Document file field
  * Image file field
  * Typeahead-Multiselect field ("select2")
* Embed page content - without header, footer etc. - via ``url?embed=true``. Useful for iframes.
  * iFrame autoresizing via https://github.com/davidjbradshaw/iframe-resizer
* Protect uploaded files (images and documents) via
  * filenames prefixed with an UUID
  * files could only be fetched from an authenticated request, and/or a whitelisted IP address
* Validates incoming files for: 
  * maximum file size
  * file extension
  * file mime type
  * virus scan (via clamav in docker, done async via task queue `huey`)

### iFrame

*Snippet from https://github.com/davidjbradshaw/iframe-resizer#typical-setup*

```html
<style>
  iframe#waf-iframe {
    width: 1px;
    min-width: 100%;
  }
</style>
<iframe id="waf-iframe" src="https://anotherdomain.com/iframe.html"></iframe>
<script src="https://fqdn/static/dist/js/jquery/jquery.min.js"></script>
<script src="https://fqdn/static/dist/js/iframeresizer/iframeResizer.min.js"></script> 
<script>
  iFrameResize({ log: false }, '#waf-iframe')
</script>
```

## Usage

### Setup

See `docs/setup.md`


### Hints

* Docs are served via `django-sphinx-view` at the URL `fqdn/docs/`.
* Attachment file objects could only be fetched with an authenticated request (from whitelisted ip address or basic auth)
* Attachment file objects could only be fetched if its status is ``av_passed=True`` for which the huey task queue must be running (or when virus checking facility is disabled via `USE_ANTIVIR_SERVICE=false` in `.env`)
