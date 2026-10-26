"""
Content Security Policy tests.

Form pages are embedded on third party sites via iframe. The browser only
renders the iframe if the form page's CSP `frame-ancestors` lists the
embedding site (FORMBUILDER_CSP_FRAME_ANCESTORS); without a CSP it falls back
to `X-Frame-Options: DENY`. Every other response, the admins included, must
only be frameable by ourselves.
"""

import pytest

from django.conf import settings
from django.utils.csp import CSP

from wagtail.models import Site


def frame_ancestors(resp):
    policy = resp.headers["Content-Security-Policy"]
    directives = [d.strip() for d in policy.split(";")]
    return next(d for d in directives if d.startswith("frame-ancestors "))


@pytest.mark.django_db
@pytest.mark.parametrize(
    "path", ["/api/formsubmission/v2/", "/admin/", "/django-admin/"]
)
def test_non_form_responses_are_only_frameable_by_self(client, path):
    resp = client.get(path)

    assert "default-src 'self'" in resp.headers["Content-Security-Policy"]
    assert frame_ancestors(resp) == "frame-ancestors 'self'"


@pytest.mark.django_db
def test_form_page_is_frameable_by_third_party_sites(client, form_page, monkeypatch):
    # FormPage.serve's csp_override holds a reference to this dict, so pinning
    # a host here keeps the test independent of FORMBUILDER_CSP_FRAME_ANCESTORS.
    monkeypatch.setitem(
        settings.FORMBUILDER_FORMPAGE_CSP,
        "frame-ancestors",
        [CSP.SELF, "https://embedder.example.org"],
    )
    site = Site.objects.get(is_default_site=True)
    site.root_page = form_page.get_parent().get_parent()
    site.save()

    # Without ?embed=true: the policy applies to every FormPage response, and
    # embed mode additionally needs the npm-built iframe-resizer asset.
    resp = client.get(form_page.url)

    assert resp.status_code == 200
    assert frame_ancestors(resp) == (
        "frame-ancestors 'self' https://embedder.example.org"
    )
