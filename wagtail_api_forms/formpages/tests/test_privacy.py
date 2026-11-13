"""
What a form tells visitors about their data, and what it stores of them.

Submissions store the visitor's IP address shortened to its network part. A
short privacy notice from the branding settings is shown above the submit
button, also on embedded forms, which have no footer with the policy link.
"""

import importlib

import pytest
from django.apps import apps

from wagtail_api_forms.formpages.constants import PAGE_BREAK
from wagtail_api_forms.formpages.models import CustomFormSubmission, UserFormField
from wagtail_api_forms.formpages.utils import anonymize_ip
from wagtail_api_forms.home.models import BrandingSettings

NOTICE_EN = "We store your answers and your shortened IP address."
NOTICE_DE = "Wir speichern Ihre Angaben und Ihre gekürzte IP-Adresse."


# ----- IP addresses ----------------------------------------------------------


@pytest.mark.parametrize(
    "ip, expected",
    [
        ("192.168.12.34", "192.168.12.0"),
        ("192.168.12.0", "192.168.12.0"),
        ("2001:db8:abcd:12:3456:789a:bcde:f012", "2001:db8:abcd::"),
        ("::ffff:192.0.2.77", "192.0.2.0"),
        (None, None),
        ("", ""),
    ],
)
def test_anonymize_ip(ip, expected):
    assert anonymize_ip(ip) == expected


@pytest.mark.django_db
def test_submission_stores_shortened_ip(client, form_url):
    response = client.post(form_url, {}, REMOTE_ADDR="203.0.113.77")

    assert response.status_code == 302
    assert CustomFormSubmission.objects.get().client_ip == "203.0.113.0"


@pytest.mark.django_db
def test_migration_shortens_stored_ips(form_page):
    migration = importlib.import_module(
        "wagtail_api_forms.formpages.migrations.0015_anonymize_client_ip"
    )
    for ip in ("198.51.100.23", "2001:db8:abcd:12::1", None):
        CustomFormSubmission.objects.create(page=form_page, form_data={}, client_ip=ip)

    migration.anonymize_client_ips(apps, None)

    stored = set(CustomFormSubmission.objects.values_list("client_ip", flat=True))
    assert stored == {"198.51.100.0", "2001:db8:abcd::", None}


# ----- Privacy notice --------------------------------------------------------


@pytest.fixture
def privacy_notice(db):
    settings = BrandingSettings.load()
    settings.privacy_notice_en = f"<p>{NOTICE_EN}</p>"
    settings.privacy_notice_de = f"<p>{NOTICE_DE}</p>"
    settings.save()


@pytest.fixture
def form_with_fields(form_page):
    UserFormField.objects.create(page=form_page, sort_order=0, label="Name", field_type="singleline")
    return form_page


SUBMIT_DESCRIBED = 'type="submit" aria-describedby="formbuilder-privacy-notice"'


@pytest.mark.django_db
@pytest.mark.parametrize("query", ["", "?embed=true"])
def test_notice_is_shown_at_the_form(client, privacy_notice, form_with_fields, form_url, query):
    content = client.get(f"{form_url}{query}").content.decode()

    assert NOTICE_EN in content
    assert NOTICE_DE not in content
    # Right below the submit button, which it describes
    assert content.index('type="submit"') < content.index(NOTICE_EN)
    assert SUBMIT_DESCRIBED in content


@pytest.mark.django_db
def test_notice_goes_with_the_submit_button_on_multistep_forms(
    client, privacy_notice, form_with_fields, form_url
):
    UserFormField.objects.create(page=form_with_fields, sort_order=1, heading="Next", field_type=PAGE_BREAK)
    UserFormField.objects.create(page=form_with_fields, sort_order=2, label="Email", field_type="email")

    content = client.get(form_url).content.decode()

    assert "data-form-steps" in content
    # Below the buttons; form-steps.js shows it on the last step only, with
    # the submit button (without JS all steps are shown)
    assert content.index("data-step-submit") < content.index(NOTICE_EN)
    assert "data-step-privacy-notice" in content
    assert 'data-step-submit aria-describedby="formbuilder-privacy-notice"' in content


@pytest.mark.django_db
def test_no_notice_without_text(client, form_with_fields, form_url):
    content = client.get(form_url).content.decode()

    assert "formbuilder-privacy-notice" not in content
