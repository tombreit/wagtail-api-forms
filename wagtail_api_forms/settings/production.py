from .base import *
from .ldap import *


# Security
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")

# Email
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = env.str("EMAIL_HOST")
EMAIL_PORT = env.int("EMAIL_PORT")

SENDFILE_BACKEND = 'sendfile.backends.mod_wsgi'

try:
    from .local import *
except ImportError:
    pass
