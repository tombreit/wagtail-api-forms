"""
Form fields in the admin: the attributes of a form field are only shown for
the field types they apply to, and page breaks need no label.
"""

import json

import pytest

from django.core.exceptions import ValidationError
from django.urls import reverse

from wagtail.test.utils import WagtailTestUtils
from wagtail.test.utils.form_data import (
    inline_formset,
    nested_form_data,
    querydict_from_html,
    rich_text,
)

from wagtail_api_forms.formpages.constants import PAGE_BREAK
from wagtail_api_forms.formpages.models import FormPage, UserFormField


def get_form_data(client, url):
    """The data of the page editor's form, as a browser would submit it."""
    response = client.get(url)
    assert response.status_code == 200
    html = response.content.decode()
    form_id = "page-edit-form"
    data = querydict_from_html(html, form_id=form_id)
    # Browsers send "on" for a checked checkbox without a value attribute
    soup = WagtailTestUtils.get_soup(html)
    for checkbox in soup.select(f"#{form_id} input[type=checkbox][checked]"):
        if "value" not in checkbox.attrs:
            data[checkbox["name"]] = "on"
    return data


def with_form_fields(data, fields, initial=0):
    data = data.copy()
    for key in list(data):
        if key.startswith("form_fields-"):
            del data[key]
    empty_field = {
        "label": "",
        "heading": "",
        "required": "on",
        "help_text": rich_text(""),
        "choices": "",
        "default_value": "",
        "placeholder": "",
        "css_classes": "",
    }
    data.update(
        nested_form_data(
            {
                "form_fields": inline_formset(
                    [{**empty_field, **field} for field in fields], initial=initial
                )
            }
        )
    )
    data["action-publish"] = "action-publish"
    return data


@pytest.fixture
def admin_client(client, superuser):
    client.force_login(superuser)
    return client


@pytest.fixture
def add_url(container_page):
    return reverse(
        "wagtailadmin_pages:add", args=("formpages", "formpage", container_page.pk)
    )


def add_form_page(client, add_url, fields):
    data = get_form_data(client, add_url)
    data["title"] = "Survey"
    data["slug"] = "survey"
    return client.post(add_url, with_form_fields(data, fields))


# ----- Model -----------------------------------------------------------------


def test_label_is_required_for_questions():
    with pytest.raises(ValidationError):
        UserFormField(label="", field_type="singleline").clean()


def test_label_is_optional_for_page_breaks():
    UserFormField(label="", field_type=PAGE_BREAK).clean()


# ----- Show/hide per field type ----------------------------------------------


def rules_of(soup, field_name, prefix):
    """The field types a FieldTypePanel of a form field is shown for."""
    panel_input = soup.find(attrs={"name": f"form_fields-{prefix}-{field_name}"})
    assert panel_input is not None, field_name
    panel = panel_input.find_parent(attrs={"data-w-rules-target": "show"})
    if panel is None:
        return None  # Always shown
    return json.loads(panel["data-w-rules"])[f"form_fields-{prefix}-field_type"]


@pytest.mark.django_db
def test_attributes_are_shown_per_field_type(admin_client, form_page):
    UserFormField.objects.create(page=form_page, label="Colour", field_type="radio")
    edit_url = reverse("wagtailadmin_pages:edit", args=[form_page.pk])

    response = admin_client.get(edit_url)

    html = response.content.decode()
    assert 'data-controller="w-rules waf-form-fields"' in html
    assert 'data-action="change-&gt;w-rules#resolve ' in html
    # The Stimulus controller for the form fields, with its values
    assert 'type="module" src="/static/formpages/admin/form-fields.' in html
    assert 'data-waf-form-fields-page-break-value="pagebreak"' in html
    assert 'data-waf-form-fields-step-label-value="Step %(number)s"' in html
    # The poll setting, named so editors find it
    assert "Show poll results after submitting" in html
    soup = WagtailTestUtils.get_soup(html)
    # Saved form fields and the template for newly added ones
    for prefix in ("0", "__prefix__"):
        assert rules_of(soup, "field_type", prefix) is None
        assert rules_of(soup, "heading", prefix) is None
        assert PAGE_BREAK not in rules_of(soup, "label", prefix)
        assert "hidden" not in rules_of(soup, "help_text", prefix)
        assert rules_of(soup, "choices", prefix) == [
            "checkboxes",
            "dropdown",
            "multiselect",
            "radio",
            "multiplechoicetypeahead",
        ]
        assert "document" not in rules_of(soup, "default_value", prefix)
        assert "date" not in rules_of(soup, "placeholder", prefix)
        assert "singleline" in rules_of(soup, "css_classes", prefix)


@pytest.mark.django_db
def test_attributes_order(admin_client, form_page):
    """The field type, the required attributes, the common ones, then those
    specific to some field types: the same order for all field types."""
    UserFormField.objects.create(page=form_page, label="Colour", field_type="radio")
    edit_url = reverse("wagtailadmin_pages:edit", args=[form_page.pk])

    html = admin_client.get(edit_url).content.decode()

    names = [
        "field_type",
        "label",
        "help_text",
        "required",
        "heading",
        "css_classes",
        "choices",
        "default_value",
        "placeholder",
    ]
    positions = [html.index(f'name="form_fields-0-{name}"') for name in names]
    assert positions == sorted(positions)


# ----- Saving ----------------------------------------------------------------


@pytest.mark.django_db
def test_page_breaks_need_no_label(admin_client, add_url):
    response = add_form_page(
        admin_client,
        add_url,
        [
            {"label": "Question", "field_type": "singleline"},
            {"field_type": PAGE_BREAK, "heading": "Part 2"},
            {"label": "Comment", "field_type": "multiline"},
            {"field_type": PAGE_BREAK},
            {"label": "Rating", "field_type": "number"},
        ],
    )

    assert response.status_code == 302
    page = FormPage.objects.get(slug="survey")
    assert [step.heading for step in page.get_steps()] == ["", "Part 2", ""]
    assert [field.clean_name for field in page.get_form_fields()] == [
        "question",
        "comment",
        "rating",
    ]


@pytest.mark.django_db
def test_questions_need_a_label(admin_client, add_url):
    response = add_form_page(
        admin_client, add_url, [{"label": "", "field_type": "singleline"}]
    )

    assert response.status_code == 200
    assert "This field is required" in response.content.decode()
    assert not FormPage.objects.filter(slug="survey").exists()


@pytest.mark.django_db
@pytest.mark.parametrize(
    "saved, changed",
    [
        ({"label": "", "field_type": PAGE_BREAK}, {"label": "Q", "field_type": "email"}),
        ({"label": "Q", "field_type": "email"}, {"label": "Q", "field_type": PAGE_BREAK}),
    ],
)
def test_saved_fields_cant_switch_between_page_break_and_question(
    admin_client, form_page, saved, changed
):
    UserFormField.objects.create(page=form_page, label="Name", field_type="singleline")
    field = UserFormField.objects.create(page=form_page, sort_order=1, **saved)
    edit_url = reverse("wagtailadmin_pages:edit", args=[form_page.pk])
    data = get_form_data(admin_client, edit_url)
    data["form_fields-1-field_type"] = changed["field_type"]
    data["form_fields-1-label"] = changed["label"]
    data["action-publish"] = "action-publish"

    response = admin_client.post(edit_url, data)

    assert response.status_code == 200
    assert "A page break can&#x27;t be turned into a question" in (
        response.content.decode()
    )
    field.refresh_from_db()
    assert field.field_type == saved["field_type"]


@pytest.mark.django_db
def test_new_fields_can_be_page_breaks_or_questions(admin_client, form_page):
    UserFormField.objects.create(page=form_page, label="Name", field_type="singleline")
    edit_url = reverse("wagtailadmin_pages:edit", args=[form_page.pk])
    data = get_form_data(admin_client, edit_url)
    data["form_fields-0-field_type"] = "email"
    data["form_fields-TOTAL_FORMS"] = "2"
    data.update(
        {
            "form_fields-1-field_type": PAGE_BREAK,
            "form_fields-1-label": "",
            "form_fields-1-ORDER": "1",
            "form_fields-1-DELETE": "",
        }
    )
    data["action-publish"] = "action-publish"

    response = admin_client.post(edit_url, data)

    assert response.status_code == 302
    assert [field.field_type for field in form_page.form_fields.all()] == [
        "email",
        PAGE_BREAK,
    ]
