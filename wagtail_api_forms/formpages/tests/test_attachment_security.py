"""
Security tests for AttachmentDownloadView.

The view layers three gates:

1. AV scan: when FORMBUILDER_USE_ANTIVIR_SERVICE is on, an attachment
   whose av_passed flag is still False MUST NOT be served — even to an
   authenticated user or a whitelisted IP.
2. Authentication: an authenticated session may fetch an AV-passed file.
3. IP whitelist: a request from a whitelisted IP may fetch an AV-passed
   file without authentication (used by an internal puller).

These tests exercise can_access_file directly (so we don't depend on the
private-storage URL plumbing) and add one end-to-end HTTP test for the
anonymous-deny case.
"""

import pytest

from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.test import RequestFactory

from wagtail_api_forms.formpages.views import AttachmentDownloadView


def _private_file(user=None, ip="9.9.9.9"):
    """Build the duck-typed object the view's can_access_file expects."""
    rf = RequestFactory()
    req = rf.get("/attachments/dummy")
    req.user = user if user is not None else AnonymousUser()
    req.META["REMOTE_ADDR"] = ip
    pf = type("PrivateFile", (), {"request": req})()
    return pf


def _view_for(attachment):
    view = AttachmentDownloadView()
    view.object = attachment
    return view


# ----- AV gate ---------------------------------------------------------------


@pytest.mark.django_db
def test_unscanned_attachment_denied_to_authenticated_user(
    api_user, unscanned_attachment, settings
):
    """av_passed=False blocks even an authenticated request when AV is on."""
    settings.FORMBUILDER_USE_ANTIVIR_SERVICE = True
    view = _view_for(unscanned_attachment)

    with pytest.raises(PermissionDenied, match="Suspicious"):
        view.can_access_file(_private_file(user=api_user))


@pytest.mark.django_db
def test_unscanned_attachment_denied_to_whitelisted_ip(
    unscanned_attachment, settings
):
    """An IP whitelist must not override the AV gate."""
    settings.FORMBUILDER_USE_ANTIVIR_SERVICE = True
    settings.FORMBUILDER_WHITELIST_IPS_ATTACHMENT_REQUEST = ["10.0.0.7"]
    view = _view_for(unscanned_attachment)

    with pytest.raises(PermissionDenied, match="Suspicious"):
        view.can_access_file(_private_file(ip="10.0.0.7"))


@pytest.mark.django_db
def test_av_disabled_bypasses_scan_gate(api_user, unscanned_attachment, settings):
    """With AV disabled, av_passed is ignored — auth alone is enough."""
    settings.FORMBUILDER_USE_ANTIVIR_SERVICE = False
    view = _view_for(unscanned_attachment)

    assert view.can_access_file(_private_file(user=api_user)) is True


# ----- Auth / IP gates -------------------------------------------------------


@pytest.mark.django_db
def test_anonymous_request_denied_when_not_whitelisted(
    clean_attachment, settings
):
    settings.FORMBUILDER_USE_ANTIVIR_SERVICE = True
    settings.FORMBUILDER_WHITELIST_IPS_ATTACHMENT_REQUEST = []
    view = _view_for(clean_attachment)

    with pytest.raises(PermissionDenied):
        view.can_access_file(_private_file(ip="9.9.9.9"))


@pytest.mark.django_db
def test_authenticated_user_can_access_clean_attachment(
    api_user, clean_attachment, settings
):
    settings.FORMBUILDER_USE_ANTIVIR_SERVICE = True
    view = _view_for(clean_attachment)

    assert view.can_access_file(_private_file(user=api_user)) is True


@pytest.mark.django_db
def test_whitelisted_ip_can_access_clean_attachment(clean_attachment, settings):
    """A puller from a whitelisted IP needs no session."""
    settings.FORMBUILDER_USE_ANTIVIR_SERVICE = True
    settings.FORMBUILDER_WHITELIST_IPS_ATTACHMENT_REQUEST = ["10.0.0.7"]
    view = _view_for(clean_attachment)

    assert view.can_access_file(_private_file(ip="10.0.0.7")) is True


# ----- HTTP-level smoke test -------------------------------------------------


@pytest.mark.django_db
def test_anonymous_http_get_returns_403(client, clean_attachment, settings):
    """End-to-end: hitting the attachment URL from a non-whitelisted IP
    without auth is rejected with 403 (PermissionDenied)."""
    settings.FORMBUILDER_USE_ANTIVIR_SERVICE = True
    settings.FORMBUILDER_WHITELIST_IPS_ATTACHMENT_REQUEST = []

    resp = client.get(
        f"/attachments/{clean_attachment.file.name}", REMOTE_ADDR="9.9.9.9"
    )
    assert resp.status_code == 403
