"""
Tests for the LDAP login with email address or account name.

No LDAP server is needed: the backend is fed a fake LDAP user with the
attributes an Active Directory search would return.
"""

from types import SimpleNamespace

import ldap
import pytest

from django.conf import settings
from django.contrib.auth import get_user_model

from wagtail_api_forms.users.backends import EmailOrUsernameLDAPBackend
from wagtail_api_forms.users.forms import EmailOrUsernameLoginForm


User = get_user_model()


@pytest.fixture
def ldap_user():
    return SimpleNamespace(
        attrs=ldap.cidict.cidict(
            {"sAMAccountName": ["JDoe"], "mail": ["j.doe@example.org"]}
        )
    )


@pytest.mark.django_db
def test_email_login_builds_user_named_after_account_name(ldap_user):
    user, built = EmailOrUsernameLDAPBackend().get_or_build_user(
        "j.doe@example.org", ldap_user
    )

    assert built
    assert user.username == "jdoe"


@pytest.mark.django_db
@pytest.mark.parametrize("typed", ["j.doe@example.org", "jdoe", "JDoe"])
def test_email_and_account_name_resolve_to_existing_user(ldap_user, typed):
    existing = User.objects.create_user(username="jdoe")

    user, built = EmailOrUsernameLDAPBackend().get_or_build_user(typed, ldap_user)

    assert not built
    assert user == existing
    assert User.objects.count() == 1


def test_login_form_labels_email_or_username():
    form = EmailOrUsernameLoginForm()
    field = form.fields["username"]

    assert field.label == "Email or username"
    assert field.widget.attrs["placeholder"] == "Enter your email or username"
    assert "email/username" in form.get_invalid_login_error().message


@pytest.mark.skipif(
    not getattr(settings, "AUTH_LDAP", False), reason="AUTH_LDAP is disabled"
)
def test_ldap_settings_search_by_email_or_account_name():
    filterstrs = [search.filterstr for search in settings.AUTH_LDAP_USER_SEARCH.searches]

    assert "(|(sAMAccountName=%(user)s)(mail=%(user)s))" in filterstrs
    assert settings.AUTHENTICATION_BACKENDS[0] == (
        "wagtail_api_forms.users.backends.EmailOrUsernameLDAPBackend"
    )
    assert settings.WAGTAILADMIN_USER_LOGIN_FORM == (
        "wagtail_api_forms.users.forms.EmailOrUsernameLoginForm"
    )
