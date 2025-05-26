# ldap/ad auth
# see: http://django-auth-ldap.readthedocs.io/en/latest/index.html

import ldap
from django_auth_ldap.config import (
    LDAPSearch,
    LDAPSearchUnion,
    ActiveDirectoryGroupType,
    LDAPGroupQuery,
)
from .base import (
    AUTHENTICATION_BACKENDS,
    env,
)

# WAGTAIL settings
# Disable Wagtail password management features if using LDAP
# https://docs.wagtail.org/en/6.3/reference/settings.html#wagtail-password-reset-enabled
WAGTAIL_PASSWORD_MANAGEMENT_ENABLED = False
WAGTAIL_PASSWORD_RESET_ENABLED = False
WAGTAILUSERS_PASSWORD_ENABLED = False

# LDAP settings
AUTH_LDAP = env.bool("AUTH_LDAP")
AUTH_LDAP_SERVER_URI = env.str("AUTH_LDAP_SERVER_URI")
AUTH_LDAP_BIND_DN = env.str("AUTH_LDAP_BIND_DN")
AUTH_LDAP_BIND_PASSWORD = env.str("AUTH_LDAP_BIND_PASSWORD")
AUTH_LDAP_MIRROR_GROUPS = env.list("AUTH_LDAP_MIRROR_GROUPS")

if env.bool("DEBUG"):
    ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)
    ldap.set_option(ldap.OPT_DEBUG_LEVEL, 255)
    print(f"{AUTH_LDAP=}: against {AUTH_LDAP_SERVER_URI}")

# First check LDAPBackend, than ModelBackend
AUTHENTICATION_BACKENDS = [
    "django_auth_ldap.backend.LDAPBackend"
] + AUTHENTICATION_BACKENDS
AUTH_LDAP_GROUP_TYPE = ActiveDirectoryGroupType()
AUTH_LDAP_FIND_GROUP_PERMS = True


AUTH_LDAP_USER_SEARCH = LDAPSearchUnion(
    LDAPSearch(
        f"{env.str('AUTH_LDAP_USERS_DN')}",
        ldap.SCOPE_SUBTREE,
        "(sAMAccountName=%(user)s)",
    ),
)

AUTH_LDAP_GROUP_SEARCH = LDAPSearch(
    f"{env.str('AUTH_LDAP_USERS_DN')}", ldap.SCOPE_SUBTREE, "(objectClass=group)"
)

AUTH_LDAP_USER_ATTR_MAP = {
    "first_name": "givenName",
    "last_name": "sn",
    "email": "mail",
}

# https://django-auth-ldap.readthedocs.io/en/latest/groups.html#limiting-access
AUTH_LDAP_REQUIRE_GROUP = (
    LDAPGroupQuery(env.str("AUTH_LDAP_GROUP_SUPERUSERS"))
    | LDAPGroupQuery(env.str("AUTH_LDAP_GROUP_STAFF"))
    | LDAPGroupQuery(env.str("AUTH_LDAP_GROUP_EDITORS"))
)

AUTH_LDAP_USER_FLAGS_BY_GROUP = {
    "is_active": (
        LDAPGroupQuery(env.str("AUTH_LDAP_GROUP_SUPERUSERS"))
        | LDAPGroupQuery(env.str("AUTH_LDAP_GROUP_STAFF"))
        | LDAPGroupQuery(env.str("AUTH_LDAP_GROUP_EDITORS"))
    ),
    "is_staff": (
        LDAPGroupQuery(env.str("AUTH_LDAP_GROUP_STAFF"))
        | LDAPGroupQuery(env.str("AUTH_LDAP_GROUP_EDITORS"))
    ),
    "is_superuser": (LDAPGroupQuery(env.str("AUTH_LDAP_GROUP_SUPERUSERS"))),
}
