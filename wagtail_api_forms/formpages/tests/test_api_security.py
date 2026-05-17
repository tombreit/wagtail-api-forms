"""
Security tests for the /api/formsubmission/v2/ endpoint.

These tests guard the two properties that matter most: an unauthenticated
caller must not see any submissions, and an authenticated token-holder must
only ever see the submissions for the FormPage(s) explicitly linked to their
token via TokenForm. A regression in either direction is a data leak.
"""

import pytest


API_URL = "/api/formsubmission/v2/"


@pytest.mark.django_db
def test_anonymous_request_is_rejected(anonymous_api_client, form_submission):
    resp = anonymous_api_client.get(API_URL)
    assert resp.status_code in (401, 403)
    # Be paranoid: the body must not contain any submitter data either.
    assert "user@example.org" not in resp.content.decode()


@pytest.mark.django_db
def test_invalid_token_is_rejected(anonymous_api_client, form_submission):
    anonymous_api_client.credentials(HTTP_AUTHORIZATION="Token not-a-real-token")
    resp = anonymous_api_client.get(API_URL)
    # DRF returns 401 or 403 depending on the order of auth classes that
    # advertise a WWW-Authenticate header — both are rejections.
    assert resp.status_code in (401, 403)
    assert "user@example.org" not in resp.content.decode()


@pytest.mark.django_db
def test_token_without_tokenform_sees_no_submissions(
    token_api_client, form_submission
):
    """A valid token that has no TokenForm scope must see an empty list."""
    resp = token_api_client.get(API_URL)
    assert resp.status_code == 200
    assert resp.json()["count"] == 0


@pytest.mark.django_db
def test_token_only_sees_its_own_form_submissions(
    token_api_client, token_form, form_submission, other_form_submission
):
    """Token bound to form_page must see form_page's submissions only —
    never another FormPage's submissions."""
    resp = token_api_client.get(API_URL)
    body = resp.json()

    assert resp.status_code == 200
    assert body["count"] == 1
    assert body["results"][0]["form_page_slug"] == form_submission.page.slug
    assert "leak@example.org" not in resp.content.decode()


@pytest.mark.django_db
def test_unrelated_token_does_not_see_other_tenants_data(
    other_token_api_client, token_form, form_submission, other_form_submission
):
    """A token with no TokenForm bindings sees nothing, even when another
    token *is* bound to a different form."""
    resp = other_token_api_client.get(API_URL)
    assert resp.status_code == 200
    assert resp.json()["count"] == 0


@pytest.mark.django_db
def test_serializer_strips_unknown_keys_from_form_data_api(
    token_api_client, token_form
):
    """The serializer must drop keys outside the allow-list (e.g. an
    accidentally-stored internal flag) before exposing form_data_api."""
    from wagtail_api_forms.formpages.models import CustomFormSubmission

    CustomFormSubmission.objects.create(
        page=token_form.form,
        form_data={"email": "ok@example.org"},
        form_data_api=(
            '[{"label": "Email", "name": "email", "type": "email", '
            '"value": "ok@example.org", "internal_secret": "shh"}]'
        ),
    )

    resp = token_api_client.get(API_URL)
    raw = resp.content.decode()
    assert resp.status_code == 200
    assert "internal_secret" not in raw
    assert "shh" not in raw


@pytest.mark.django_db
def test_write_methods_are_not_allowed(token_api_client, token_form):
    """The endpoint is a ListAPIView; mutations must be rejected."""
    for method in ("post", "put", "patch", "delete"):
        resp = getattr(token_api_client, method)(API_URL, data={})
        assert resp.status_code in (403, 405), (
            f"{method.upper()} unexpectedly returned {resp.status_code}"
        )
