# CHANGELOG

## 2026

- Upgraded `iframe-resizer` from 4.x to 5.x (`@iframe-resizer/parent` and
  `@iframe-resizer/child`). Upstream relicensed from MIT to GPL-3.0; the GPLv3 open
  source license key is set on the form page, so embedding sites need no configuration.
  Existing embed snippets keep working, and new ones no longer need an inline script:
  add `data-waf-resize` to the iframe. See the README, section "iFrame".
- Embedded forms always use iframe-resizer's automatic height detection; a
  `heightCalculationMethod` from older embed snippets (e.g. `lowestElement`) is ignored.
- Embedded forms scroll the embedding page to the top of the form after a submit, so
  validation errors and the thank-you text are visible.
- Fixed: the "Back to form" link on the thank-you page left embed mode.
- New recommended embed CSS (`width: 100%; height: 100vh`) and a `title` on the iframe.

## 2025

- Set custom document file types per form (not per field). Requires superuser.
- Field help text as richtext fields

## 2024

- Multiline field help texts
- Static assets processing now via `parcel`
- Stop false positives for PUA.Pdf.Trojan.EmbeddedJavaScript-1
- Docs FAQ: Form submissions, form submission email notification
- Fields: Use bootstrap CSS classes like `alert alert-warning`

## 2023

- Use whitenoise for static file serving and for /docs/
- New form customizations: Headings, custom css classes etc.
- Paginated API endpoint
- Attachment upload size configurable

## 2022

- Fields with placeholder text
- help_text als TextField, not upstream CharField
- Accordion-like interface for form fields listing in backend
- new `/docs/` URL hosting the documentation (via django-sphinx-view)
- some initial user facing documentation
- Select2-style multiple choice field
