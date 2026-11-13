"""
Multi-step forms: page breaks split a form into steps.

All steps are one HTML form, submitted once. Each step is validated on the
server (<form page>/validate-step/) before the browser moves on to the next.
"""

import json

import pytest

from django.contrib.auth.models import AnonymousUser
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client

from wagtail_api_forms.formpages.constants import PAGE_BREAK
from wagtail_api_forms.formpages.models import (
    Attachment,
    CustomFormSubmission,
    UserFormField,
)
from wagtail_api_forms.formpages.steps import split_into_steps


FIELDS = [
    {"label": "Name", "field_type": "singleline"},
    {"label": "Email", "field_type": "email"},
    {"heading": "Documents", "field_type": PAGE_BREAK},
    {"label": "CV", "field_type": "document", "required": False},
    {"heading": "Almost done", "field_type": PAGE_BREAK},
    {"label": "Status", "field_type": "radio", "choices": "Student\nStaff"},
    {"label": "Comment", "field_type": "multiline", "required": False},
]

VALID_DATA = {
    "name": "Jane",
    "email": "jane@example.org",
    "status": "Staff",
    "comment": "",
}


@pytest.fixture
def multistep_page(form_page):
    for sort_order, attrs in enumerate(FIELDS):
        UserFormField.objects.create(page=form_page, sort_order=sort_order, **attrs)
    return form_page


@pytest.fixture
def validation_url(multistep_page, form_url):
    return f"{form_url}validate-step/"


def validate_step(client, url, step, data=None):
    response = client.post(url, {"form_step": step, **(data or {})})
    assert response.status_code == 200
    return response.json()


# ----- Steps -----------------------------------------------------------------


def make_fields(*field_types):
    return [
        UserFormField(label=f"Field {i}", field_type=field_type, heading=f"H{i}")
        for i, field_type in enumerate(field_types)
    ]


def test_without_page_breaks_there_is_one_step():
    steps = split_into_steps(make_fields("singleline", "email"))

    assert len(steps) == 1
    assert steps[0].field_names == ["field_0", "field_1"]


def test_page_breaks_split_into_steps():
    steps = split_into_steps(
        make_fields("singleline", PAGE_BREAK, "email", "number", PAGE_BREAK, "date")
    )

    assert [step.number for step in steps] == [1, 2, 3]
    assert [step.heading for step in steps] == ["", "H1", "H4"]
    assert [step.field_names for step in steps] == [
        ["field_0"],
        ["field_2", "field_3"],
        ["field_5"],
    ]


def test_page_breaks_at_start_and_end_and_in_a_row():
    steps = split_into_steps(
        make_fields(PAGE_BREAK, "singleline", PAGE_BREAK, PAGE_BREAK, "email", PAGE_BREAK)
    )

    # A page break at the start of a step only sets its heading
    assert [step.heading for step in steps] == ["H0", "H3"]
    assert [step.field_names for step in steps] == [["field_1"], ["field_4"]]


# ----- Rendering -------------------------------------------------------------


@pytest.mark.django_db
def test_form_renders_all_steps(client, multistep_page, form_url, validation_url):
    response = client.get(form_url)

    assert response.status_code == 200
    html = response.content.decode()
    assert "data-form-steps" in html
    assert f'data-step-validation-url="{validation_url}"' in html
    assert 'data-initial-step="1"' in html
    for number in (1, 2, 3):
        assert f'data-form-step="{number}"' in html
    assert "Step 2 of 3" in html
    assert (
        '<h2 class="formbuilder-step-heading" id="formbuilder-step-2-heading">'
        "Documents</h2>"
    ) in html
    # Each step is a group named by its position and heading
    assert (
        'aria-labelledby="formbuilder-step-2-count formbuilder-step-2-heading"'
    ) in html
    # Every question is in the one form, no page break is
    for name in ("name", "email", "cv", "status", "comment"):
        assert f'name="{name}"' in html
    assert "page_break" not in html


@pytest.mark.django_db
def test_intro_and_outro_are_shown_on_all_steps(client, multistep_page, form_url):
    multistep_page.intro = "<p>Welcome.</p>"
    multistep_page.outro = "<p>Thanks for your patience.</p>"
    multistep_page.save()

    html = client.get(form_url).content.decode()

    # Outside the steps, which form-steps.js hides
    assert html.count('class="intro"') == 1
    assert html.index('class="intro"') < html.index('data-form-step="1"')
    assert html.count('class="outro"') == 1
    assert html.rindex("</fieldset>") < html.index('class="outro"')
    assert html.index('class="outro"') < html.index("data-step-next")


@pytest.mark.django_db
def test_field_headings_in_steps_are_below_step_headings(client, multistep_page, form_url):
    UserFormField.objects.filter(clean_name="comment").update(heading="Your comment")

    html = client.get(form_url).content.decode()

    assert '<h3 class="h4 my-4">\n        Your comment\n    </h3>' in html


@pytest.mark.django_db
def test_error_summary_links_to_fields_of_all_steps(client, multistep_page, form_url):
    response = client.post(form_url, {**VALID_DATA, "email": "x", "status": ""})

    html = response.content.decode()
    assert "There is a problem with 2 fields" in html
    assert 'href="#div_id_email"' in html
    assert 'href="#div_id_status"' in html
    # The visitor starts at the first step with errors
    assert response.context["initial_step"] == 1


@pytest.mark.django_db
def test_captcha_is_in_last_step(client, multistep_page, form_url):
    multistep_page.use_captcha = True
    multistep_page.save()

    response = client.get(form_url)

    steps = response.context["form_steps"]
    assert [field.name for field in steps[-1].fields] == [
        "status",
        "comment",
        "wagtailcaptcha",
    ]
    assert all(
        field.name != "wagtailcaptcha" for step in steps[:-1] for field in step.fields
    )


@pytest.mark.django_db
def test_page_breaks_are_not_questions(multistep_page):
    names = [field.clean_name for field in multistep_page.get_form_fields()]
    assert names == ["name", "email", "cv", "status", "comment"]
    assert [name for name, label in multistep_page.get_data_fields()] == [
        "submit_time",
        *names,
        "client_ip",
        "referrer",
    ]
    page_break = UserFormField.objects.filter(field_type=PAGE_BREAK).first()
    assert page_break.clean_name.startswith("page_break_")


@pytest.mark.django_db
def test_preview_shows_steps_without_validation(rf, multistep_page):
    request = rf.get("/")
    request.is_preview = True
    request.user = AnonymousUser()

    context = multistep_page.get_preview_context(request, "form")

    assert len(context["form_steps"]) == 3
    assert context["step_validation_url"] == ""


# ----- Step validation -------------------------------------------------------


@pytest.mark.django_db
def test_step_validation_only_checks_fields_of_the_step(client, validation_url):
    result = validate_step(client, validation_url, 1, {"email": "not-an-email"})

    assert result["valid"] is False
    assert set(result["errors"]) == {"name", "email"}
    assert result["errors"]["email"][0]["code"] == "invalid"


@pytest.mark.django_db
def test_valid_step(client, validation_url):
    result = validate_step(client, validation_url, 1, VALID_DATA)

    assert result == {"valid": True, "errors": {}}


@pytest.mark.django_db
def test_step_validation_ignores_captcha(client, multistep_page, validation_url):
    multistep_page.use_captcha = True
    multistep_page.save()

    result = validate_step(client, validation_url, 3, VALID_DATA)

    assert result == {"valid": True, "errors": {}}


@pytest.mark.django_db
def test_step_validation_checks_uploads_but_stores_nothing(
    client, validation_url, private_storage
):
    upload = SimpleUploadedFile("cv.txt", b"My CV\n", content_type="text/plain")
    assert validate_step(client, validation_url, 2, {"cv": upload})["valid"]

    upload = SimpleUploadedFile("cv.exe", b"MZ\x90\x00", content_type="text/plain")
    result = validate_step(client, validation_url, 2, {"cv": upload})
    assert list(result["errors"]) == ["cv"]

    assert not Attachment.objects.exists()
    assert not list(private_storage.iterdir())
    assert not CustomFormSubmission.objects.exists()


@pytest.mark.django_db
def test_step_number_out_of_range_is_clamped(client, validation_url):
    result = validate_step(client, validation_url, 99, {})
    assert set(result["errors"]) == {"status"}

    result = validate_step(client, validation_url, "x", {})
    assert set(result["errors"]) == {"name", "email"}


@pytest.mark.django_db
def test_step_validation_needs_post(client, validation_url):
    assert client.get(validation_url).status_code == 405


@pytest.mark.django_db
def test_step_validation_needs_csrf_token(validation_url):
    client = Client(enforce_csrf_checks=True)

    response = client.post(validation_url, {"form_step": 1})

    assert response.status_code == 403


@pytest.mark.django_db
def test_no_step_validation_for_single_step_forms(client, form_page, form_url):
    UserFormField.objects.create(page=form_page, label="Name", field_type="singleline")

    response = client.post(f"{form_url}validate-step/", {"form_step": 1})

    assert response.status_code == 404


@pytest.mark.django_db
def test_no_step_validation_for_unpublished_forms(client, multistep_page, validation_url):
    multistep_page.unpublish()

    response = client.post(validation_url, {"form_step": 1})

    assert response.status_code == 404


# ----- Submitting ------------------------------------------------------------


@pytest.mark.django_db
def test_submit_creates_one_submission(
    client, multistep_page, form_url, private_storage, mailoutbox
):
    multistep_page.to_address = "inbox@example.org"
    multistep_page.save()
    upload = SimpleUploadedFile("cv.txt", b"My CV\n", content_type="text/plain")

    response = client.post(form_url, {**VALID_DATA, "cv": upload})

    assert response.status_code == 302
    submission = CustomFormSubmission.objects.get()
    names = ["name", "email", "cv", "status", "comment"]
    assert list(submission.form_data) == names
    assert [item["name"] for item in json.loads(submission.form_data_api)] == names
    attachment = Attachment.objects.get()
    assert attachment.form_submission == submission
    assert submission.form_data["cv"].endswith(attachment.file.url)
    assert "page_break" not in mailoutbox[0].body
    assert "Status: Staff" in mailoutbox[0].body


@pytest.mark.django_db
@pytest.mark.parametrize(
    "data, initial_step",
    [
        ({**VALID_DATA, "email": "not-an-email"}, 1),
        ({**VALID_DATA, "status": ""}, 3),
    ],
)
def test_invalid_submit_starts_at_first_step_with_errors(
    client, multistep_page, form_url, data, initial_step
):
    response = client.post(form_url, data)

    assert response.templates[0].name == "formpages/form_page.html"
    assert response.context["initial_step"] == initial_step
    assert f'data-initial-step="{initial_step}"' in response.content.decode()
    assert not CustomFormSubmission.objects.exists()
