"""
Smoke test for the admin CSV export of form submissions.

Builds a FormPage with one field, stores one submission, hits the admin
`?export=csv` endpoint as a superuser, and checks that the field's label
shows up as a column header and its value shows up in a data row.
"""

import csv
from io import StringIO

import pytest

from django.urls import reverse

from wagtail_api_forms.formpages.models import CustomFormSubmission, UserFormField


@pytest.mark.django_db
def test_csv_export_includes_form_field(client, form_page, superuser):
    UserFormField.objects.create(
        page=form_page,
        sort_order=1,
        label="Email",
        field_type="singleline",
        required=True,
    )
    CustomFormSubmission.objects.create(
        page=form_page,
        form_data={"email": "alice@example.org"},
    )

    client.force_login(superuser)
    url = reverse("wagtailforms:list_submissions", args=[form_page.id])
    response = client.get(url, {"export": "csv"})

    assert response.status_code == 200
    body = b"".join(response.streaming_content).decode("utf-8")
    rows = list(csv.reader(StringIO(body)))
    header, *data_rows = rows
    assert "Email" in header
    assert any("alice@example.org" in row for row in data_rows)


@pytest.mark.django_db
def test_csv_export_reflects_renamed_field(client, form_page, superuser):
    field = UserFormField.objects.create(
        page=form_page,
        sort_order=1,
        label="Email",
        field_type="singleline",
        required=True,
    )
    CustomFormSubmission.objects.create(
        page=form_page,
        form_data={"email": "alice@example.org"},
    )

    client.force_login(superuser)
    url = reverse("wagtailforms:list_submissions", args=[form_page.id])

    response = client.get(url, {"export": "csv"})
    body = b"".join(response.streaming_content).decode("utf-8")
    header, *data_rows = list(csv.reader(StringIO(body)))
    assert "Email" in header
    assert any("alice@example.org" in row for row in data_rows)

    # UserFormField.save() intentionally preserves clean_name on rename, so
    # the existing submission's value still resolves under the new header.
    field.label = "Email Address"
    field.save()

    response = client.get(url, {"export": "csv"})
    body = b"".join(response.streaming_content).decode("utf-8")
    header, *data_rows = list(csv.reader(StringIO(body)))
    assert "Email Address" in header
    assert "Email" not in header
    assert any("alice@example.org" in row for row in data_rows)
