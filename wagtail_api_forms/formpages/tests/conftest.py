"""
Shared fixtures for the formpages test suite.

These fixtures intentionally keep the Wagtail page tree minimal: just enough
HomePage / ContainerPage / FormPage to exercise auth and scoping. Anything
that would otherwise reach into Huey or ClamAV is stubbed so tests stay
hermetic and fast.
"""

import pytest

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from wagtail.models import Page, Site

from wagtail_api_forms.formpages.models import (
    Attachment,
    CustomFormSubmission,
    FormPage,
    TokenForm,
    TokenUserProxy,
)
from wagtail_api_forms.home.models import ContainerPage, HomePage


User = get_user_model()


# ----- Hermetic boundaries ---------------------------------------------------


@pytest.fixture(autouse=True)
def _disable_av_task(monkeypatch):
    """Stop Attachment.save() from enqueueing a real virus scan.

    Attachment.save() does a local `from .tasks import schedule_virusscan`,
    so we patch the attribute on the tasks module — that's what the local
    import resolves to at call time.
    """
    monkeypatch.setattr(
        "wagtail_api_forms.formpages.tasks.schedule_virusscan",
        lambda *args, **kwargs: None,
    )


@pytest.fixture(scope="session", autouse=True)
def _collected_staticfiles(tmp_path_factory):
    """Run collectstatic once per session so tests use the same
    WhiteNoise CompressedManifestStaticFilesStorage as production.

    Our error templates (403.html / 404.html) extend _base.html, which
    pulls in {% static 'frontend/app.css' %} and friends. With the
    manifest backend, those files must be present in staticfiles.json,
    which means collectstatic must have run — and that means the npm
    bundle must have been built first. We replicate the production
    pipeline (`npm run build && python manage.py collectstatic`) instead
    of bypassing it.

    WHITENOISE_AUTOREFRESH is set to True per the WhiteNoise docs to skip
    the startup file scan and keep the session fixture fast.
    """
    from pathlib import Path

    from django.conf import settings
    from django.core.management import call_command
    from django.test import override_settings

    bundle = Path(settings.STATICFILES_DIRS[0]) / "frontend" / "app.css"
    if not bundle.is_file():
        pytest.exit(
            "Test setup failed: the frontend bundle is missing.\n"
            f"  Expected file: {bundle}\n"
            "  Run `npm install && npm run build` before pytest.",
            returncode=1,
        )

    static_root = tmp_path_factory.mktemp("staticroot")
    with override_settings(
        STATIC_ROOT=str(static_root),
        WHITENOISE_AUTOREFRESH=True,
    ):
        call_command("collectstatic", "--noinput", "--clear", verbosity=0)
        yield


# ----- Users / tokens --------------------------------------------------------


@pytest.fixture
def api_user(db):
    return User.objects.create_user(username="api-user", password="pw")


@pytest.fixture
def api_token(api_user):
    return Token.objects.create(user=api_user)


@pytest.fixture
def other_api_user(db):
    return User.objects.create_user(username="other-api-user", password="pw")


@pytest.fixture
def other_api_token(other_api_user):
    return Token.objects.create(user=other_api_user)


@pytest.fixture
def superuser(db):
    return User.objects.create_superuser(
        username="root", email="r@example.org", password="pw"
    )


# ----- Page tree -------------------------------------------------------------


@pytest.fixture
def container_page(db):
    """A ContainerPage under a fresh HomePage, ready to host FormPage children."""
    root = Page.objects.get(depth=1)
    home = HomePage(title="Home", slug="home-test")
    root.add_child(instance=home)
    container = ContainerPage(title="Container", slug="container")
    home.add_child(instance=container)
    return container


@pytest.fixture
def form_page(container_page):
    fp = FormPage(title="Contact", slug="contact-test")
    container_page.add_child(instance=fp)
    return fp


@pytest.fixture
def other_form_page(container_page):
    fp = FormPage(title="Other", slug="other-test")
    container_page.add_child(instance=fp)
    return fp


@pytest.fixture
def token_form(api_token, form_page):
    """Bind api_user's token to form_page so the API returns its submissions."""
    proxy = TokenUserProxy.objects.get(pk=api_token.pk)
    return TokenForm.objects.create(form=form_page, api_user=proxy)


# ----- Submissions -----------------------------------------------------------


@pytest.fixture
def form_submission(form_page):
    return CustomFormSubmission.objects.create(
        page=form_page,
        form_data={"email": "user@example.org"},
        form_data_api=(
            '[{"label": "Email", "name": "email", '
            '"type": "email", "value": "user@example.org"}]'
        ),
    )


@pytest.fixture
def other_form_submission(other_form_page):
    return CustomFormSubmission.objects.create(
        page=other_form_page,
        form_data={"email": "leak@example.org"},
        form_data_api=(
            '[{"label": "Email", "name": "email", '
            '"type": "email", "value": "leak@example.org"}]'
        ),
    )


# ----- Attachments -----------------------------------------------------------


@pytest.fixture
def unscanned_attachment(db, tmp_path, settings):
    """Attachment that has NOT been AV-scanned yet (av_passed=False)."""
    settings.PRIVATE_STORAGE_ROOT = str(tmp_path)
    a = Attachment(
        file=SimpleUploadedFile("unscanned.txt", b"data", content_type="text/plain"),
    )
    a.save()
    return a


@pytest.fixture
def clean_attachment(db, tmp_path, settings):
    """Attachment whose AV scan came back clean (av_passed=True)."""
    settings.PRIVATE_STORAGE_ROOT = str(tmp_path)
    a = Attachment(
        file=SimpleUploadedFile("clean.txt", b"data", content_type="text/plain"),
    )
    a.save()
    Attachment.objects.filter(pk=a.pk).update(av_passed=True)
    a.refresh_from_db()
    return a


# ----- Clients ---------------------------------------------------------------


@pytest.fixture
def anonymous_api_client():
    return APIClient()


@pytest.fixture
def token_api_client(api_token):
    c = APIClient()
    c.credentials(HTTP_AUTHORIZATION=f"Token {api_token.key}")
    return c


@pytest.fixture
def other_token_api_client(other_api_token):
    c = APIClient()
    c.credentials(HTTP_AUTHORIZATION=f"Token {other_api_token.key}")
    return c
