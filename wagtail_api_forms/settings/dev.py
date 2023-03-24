from .base import *
from .ldap import *


ALLOWED_HOSTS = ["*"]

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

INSTALLED_APPS += [
    'django_extensions',
    'wagtail.contrib.styleguide',
]

SENDFILE_BACKEND = 'sendfile.backends.development'

try:
    from .local import *
except ImportError:
    pass
