"""
Characterization tests for forms without page breaks.

Every form in production is a single-step form. These tests pin down what
such a form renders, stores, exposes via the API, emails and how it round-trips
through the admin editor, so that new formbuilder features (e.g. multi-step
forms) provably leave existing forms alone.

Intended changes since:
- after submitting, visitors are redirected to the thank-you page instead of
  getting it as the response to their POST;
- the hint on mandatory fields is shown above the fields, and Reset is a quiet
  link which asks for confirmation (data-reset-confirm).

The snapshots in tests/snapshots/ were recorded before multi-step forms were
added. To re-record them after an intended change:

    UPDATE_SNAPSHOTS=1 pytest wagtail_api_forms/formpages/tests/test_regression.py
"""

import json
import os
import re
from pathlib import Path

import pytest

from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from wagtail.test.utils import WagtailTestUtils
from wagtail.test.utils.form_data import querydict_from_html

from wagtail_api_forms.formpages.models import (
    Attachment,
    CustomFormSubmission,
    UserFormField,
)
from wagtail_api_forms.formpages.tests.utils import page_title


SNAPSHOT_DIR = Path(__file__).parent / "snapshots"

# One field per field type, with the extra attributes editors use
FIELDS = [
    {
        "label": "Name",
        "field_type": "singleline",
        "placeholder": "Name, Vorname",
        "heading": "Personal data",
        "css_classes": "field-secondary",
    },
    {"label": "Message", "field_type": "multiline", "default_value": "Hello"},
    {"label": "Email", "field_type": "email", "help_text": "<p>We reply here.</p>"},
    {"label": "Age", "field_type": "number", "required": False},
    {"label": "Website", "field_type": "url", "required": False},
    {"label": "Consent", "field_type": "checkbox"},
    {
        "label": "Topics",
        "field_type": "checkboxes",
        "choices": "Law\nPolicy\nResearch",
        "css_classes": "to-form-check-inline",
    },
    {"label": "Country", "field_type": "dropdown", "choices": "Germany\nFrance"},
    {"label": "Languages", "field_type": "multiselect", "choices": "German\nEnglish"},
    {"label": "Status", "field_type": "radio", "choices": "Student\nStaff"},
    {"label": "Birthday", "field_type": "date"},
    {"label": "Appointment", "field_type": "datetime", "required": False},
    {"label": "Source", "field_type": "hidden", "default_value": "web"},
    {"label": "CV", "field_type": "document", "required": False},
    {"label": "Photo", "field_type": "image", "required": False},
    {
        "label": "Tags",
        "field_type": "multiplechoicetypeahead",
        "choices": "One\nTwo\nThree",
        "required": False,
    },
]

VALID_DATA = {
    "name": "Doe, Jane",
    "message": "Hi there",
    "email": "jane@example.org",
    "age": "42",
    "website": "https://example.org",
    "consent": "on",
    "topics": ["Law", "Research"],
    "country": "France",
    "languages": ["German", "English"],
    "status": "Staff",
    "birthday": "2001-02-03",
    "appointment": "2026-11-12T10:30",
    "source": "web",
    "tags": ["Two"],
}


def assert_matches_snapshot(name, text):
    path = SNAPSHOT_DIR / name
    if os.environ.get("UPDATE_SNAPSHOTS"):
        SNAPSHOT_DIR.mkdir(exist_ok=True)
        path.write_text(text)
    assert path.is_file(), f"Snapshot {path} is missing, run with UPDATE_SNAPSHOTS=1"
    assert text == path.read_text()


def normalize_html(html):
    """One tag per line, whitespace collapsed, CSRF token blanked."""
    html = re.sub(
        r'name="csrfmiddlewaretoken" value="[^"]+"',
        'name="csrfmiddlewaretoken" value="CSRF"',
        html,
    )
    html = re.sub(r">\s+<", "><", html)
    html = re.sub(r"\s+", " ", html)
    return html.replace("><", ">\n<") + "\n"


def extract_form(html):
    match = re.search(r'<form\s+class="formbuilder-form".*?</form>', html, re.DOTALL)
    assert match, "No formbuilder form in the page"
    return match.group(0)


@pytest.fixture
def rich_form_page(form_page):
    form_page.outro = "<p>Thanks for your patience.</p>"
    form_page.from_address = "forms@example.org"
    form_page.to_address = "inbox@example.org"
    form_page.subject = "New submission"
    form_page.save()
    for sort_order, attrs in enumerate(FIELDS):
        UserFormField.objects.create(page=form_page, sort_order=sort_order, **attrs)
    return form_page


@pytest.mark.django_db
def test_form_html(client, rich_form_page, form_url):
    response = client.get(form_url)

    assert response.status_code == 200
    html = normalize_html(extract_form(response.content.decode()))
    assert_matches_snapshot("single_step_form.html", html)


@pytest.mark.django_db
def test_submission_data(client, rich_form_page, form_url, mailoutbox):
    response = client.post(form_url, VALID_DATA, follow=True)

    assert response.redirect_chain == [(f"{form_url}thank-you/", 302)]
    assert response.templates[0].name == "formpages/form_page_landing.html"
    submission = CustomFormSubmission.objects.get()
    submission.refresh_from_db()

    assert len(mailoutbox) == 1
    email_body = re.sub(
        r"Submitted on: .*", "Submitted on: <now>", mailoutbox[0].body
    )
    data = {
        "form_data": submission.form_data,
        "form_data_api": json.loads(submission.form_data_api),
        "data_fields": [
            [name, str(label)] for name, label in rich_form_page.get_data_fields()
        ],
        "email_subject": mailoutbox[0].subject,
        "email_body": email_body.splitlines(),
    }
    assert_matches_snapshot(
        "single_step_submission.json",
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
    )


@pytest.mark.django_db
def test_invalid_submission_shows_errors(client, rich_form_page, form_url):
    response = client.post(
        form_url, {**VALID_DATA, "email": "not-an-email", "status": ""}
    )

    assert response.status_code == 200
    assert response.templates[0].name == "formpages/form_page.html"
    assert set(response.context["form"].errors) == {"email", "status"}
    assert not CustomFormSubmission.objects.exists()
    html = response.content.decode()
    assert page_title(html).startswith("Error: Contact")
    # The error summary links to the fields, also to radio buttons (no single input)
    assert "There is a problem with 2 fields" in html
    assert 'href="#div_id_email"' in html
    assert 'href="#div_id_status"' in html
    assert 'id="div_id_status"' in html


@pytest.mark.django_db
def test_no_error_summary_without_errors(client, rich_form_page, form_url):
    html = client.get(form_url).content.decode()

    assert "data-error-summary" not in html
    assert page_title(html).startswith("Contact")


@pytest.mark.django_db
def test_upload_is_stored_as_attachment(
    client, rich_form_page, form_url, private_storage
):
    upload = SimpleUploadedFile("cv.txt", b"My CV\n", content_type="text/plain")

    response = client.post(form_url, {**VALID_DATA, "cv": upload})

    assert response.status_code == 302
    submission = CustomFormSubmission.objects.get()
    attachment = Attachment.objects.get()
    assert attachment.form_submission == submission
    assert submission.form_data["cv"].endswith(attachment.file.url)
    assert submission.form_data["photo"] is None
    api_value = {
        item["name"]: item["value"] for item in json.loads(submission.form_data_api)
    }
    assert api_value["cv"] == submission.form_data["cv"]


@pytest.mark.django_db
def test_captcha_is_required_when_enabled(
    client, rich_form_page, form_url, monkeypatch
):
    rich_form_page.use_captcha = True
    rich_form_page.save()

    response = client.post(form_url, VALID_DATA)
    assert "wagtailcaptcha" in response.context["form"].errors
    assert not CustomFormSubmission.objects.exists()

    # Read on import, so the settings fixture can't switch it on
    monkeypatch.setattr("captcha.conf.settings.CAPTCHA_TEST_MODE", True)
    captcha = {"wagtailcaptcha_0": "hash", "wagtailcaptcha_1": "PASSED"}
    response = client.post(form_url, {**VALID_DATA, **captcha})
    assert response.status_code == 302
    submission = CustomFormSubmission.objects.get()
    assert "wagtailcaptcha" not in submission.form_data


def field_values(page):
    return [
        {
            name: getattr(field, name)
            for name in (
                "pk",
                "sort_order",
                "clean_name",
                "label",
                "field_type",
                "required",
                "choices",
                "default_value",
                "placeholder",
                "heading",
                "css_classes",
            )
        }
        for field in UserFormField.objects.filter(page=page).order_by("sort_order")
    ]


@pytest.mark.django_db
def test_admin_edit_round_trip(client, rich_form_page, superuser):
    """Publishing an existing form unchanged in the editor keeps its fields."""
    before = field_values(rich_form_page)
    client.force_login(superuser)
    edit_url = reverse("wagtailadmin_pages:edit", args=[rich_form_page.pk])

    response = client.get(edit_url)
    assert response.status_code == 200
    html = response.content.decode()
    data = querydict_from_html(html, form_id="page-edit-form")
    # Browsers send "on" for a checked checkbox without a value attribute,
    # querydict_from_html sends ""
    soup = WagtailTestUtils.get_soup(html)
    for checkbox in soup.select("#page-edit-form input[type=checkbox][checked]"):
        if "value" not in checkbox.attrs:
            data[checkbox["name"]] = "on"
    data["action-publish"] = "action-publish"

    response = client.post(edit_url, data)
    assert response.status_code == 302, getattr(response, "context", None) and [
        form.errors for form in response.context["form"].formsets["form_fields"]
    ]
    assert field_values(rich_form_page) == before
    email_field = UserFormField.objects.get(page=rich_form_page, clean_name="email")
    assert "We reply here." in email_field.help_text
