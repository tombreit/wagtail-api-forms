# CHANGELOG

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
