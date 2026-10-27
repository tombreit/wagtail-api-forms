"""
Embed mode tests.

With ?embed=true a form page drops navbar and footer and loads the child side
of iframe-resizer (README, "iFrame"). Embed mode has to survive the submit,
and a submitted page is flagged so iframe-resizer.config.js can scroll the
embedding page to the top of the form.
"""

import pytest


@pytest.mark.django_db
def test_embedded_form_page_loads_iframe_resizer(client, form_url):
    resp = client.get(f"{form_url}?embed=true")

    assert resp.status_code == 200
    content = resp.content.decode()
    assert "iframe-resizer.child" in content
    assert "data-waf-submitted" not in content


@pytest.mark.django_db
def test_standalone_form_page_skips_iframe_resizer(client, form_url):
    resp = client.get(form_url)

    assert resp.status_code == 200
    assert "iframe-resizer.child" not in resp.content.decode()


@pytest.mark.django_db
def test_embedded_landing_page_stays_embedded(client, form_url):
    resp = client.post(f"{form_url}?embed=true", {})

    assert resp.status_code == 200
    assert resp.templates[0].name == "formpages/form_page_landing.html"
    content = resp.content.decode()
    assert "data-waf-submitted" in content
    assert f'href="{form_url}?embed=true"' in content
