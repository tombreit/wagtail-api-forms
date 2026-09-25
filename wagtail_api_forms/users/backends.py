# users/backends.py
from django_auth_ldap.backend import LDAPBackend


class EmailOrUsernameLDAPBackend(LDAPBackend):
    """
    Accept either the email address (`mail`) or the account name
    (`sAMAccountName`) at login, see AUTH_LDAP_USER_SEARCH.

    The Django user is always keyed on sAMAccountName, regardless of what was
    typed in. Otherwise an email login would create a second Django user
    for the same person.
    """

    def get_or_build_user(self, username, ldap_user):
        # ldap_user.attrs is a case-insensitive dict
        sam_account_name = ldap_user.attrs.get("sAMAccountName")
        if sam_account_name:
            username = sam_account_name[0]
        return super().get_or_build_user(username, ldap_user)
