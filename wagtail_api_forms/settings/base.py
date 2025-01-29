"""
Django settings for wagtail-api-forms project.

See end of file for development specific settings, triggered by
`DEBUG = True`.
"""

from pathlib import Path
import environ

from django.utils.translation import gettext_lazy as _


# Build paths inside the project like this: BASE_DIR / 'subdir'.
PROJECT_DIR = Path(__file__).resolve().parent.parent
BASE_DIR = PROJECT_DIR.parent
DATA_DIR = BASE_DIR / "_data"
DB_DIR = DATA_DIR / "db"
ASSETS_DIR = BASE_DIR / "_run" / "assets"


# https://django-environ.readthedocs.io/en/latest/quickstart.html
env = environ.Env(
    # set casting, default value
    DEBUG=(bool, False),
    AUTH_LDAP=(bool, False),
)
environ.Env.read_env(BASE_DIR / ".env")

# Make sure directory structure exists
Path(DB_DIR).mkdir(parents=True, exist_ok=True)
Path(ASSETS_DIR).mkdir(parents=True, exist_ok=True)

SECRET_KEY = env.str("SECRET_KEY")
DEBUG = env.bool("DEBUG")

# Application definition
INSTALLED_APPS = [
    # Local apps
    "wagtail_api_forms.users",
    "wagtail_api_forms.home",
    "wagtail_api_forms.formpages",
    # Wagtail apps
    "wagtail.contrib.settings",
    "wagtail.contrib.forms",
    "wagtail.contrib.redirects",
    "wagtail.contrib.routable_page",
    "wagtail.embeds",
    "wagtail.sites",
    "wagtail.users",
    "wagtail.snippets",
    "wagtail.documents",
    "wagtail.images",
    "wagtail.search",
    "wagtail.admin",
    "wagtail",
    # https://docs.wagtail.io/en/latest/reference/contrib/simple_translation.html
    "wagtail.locales",
    "wagtail.contrib.simple_translation",
    # https://github.com/wagtail/wagtail-localize
    # 'wagtail_localize',
    # 'wagtail_localize.locales',  # This replaces 'wagtail.locales'
    # Third party apps
    "wagtail_modeladmin",
    "whitenoise.runserver_nostatic",
    "private_storage",
    # 'cspreports',
    "rest_framework",
    "rest_framework.authtoken",
    "modelcluster",
    "taggit",
    "crispy_forms",
    "crispy_bootstrap5",
    "captcha",
    "huey.contrib.djhuey",
    # Django apps
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

MIDDLEWARE = [
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "csp.middleware.CSPMiddleware",
    "django.middleware.security.SecurityMiddleware",
    # Using our customized WhiteNoiseMiddleware to serve additional
    # static files (here: /docs/)
    # 'whitenoise.middleware.WhiteNoiseMiddleware',
    "wagtail_api_forms.home.middleware.MoreWhiteNoiseMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "wagtail.contrib.redirects.middleware.RedirectMiddleware",
]

ROOT_URLCONF = "wagtail_api_forms.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            PROJECT_DIR / "templates",
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.i18n",
                "wagtail.contrib.settings.context_processors.settings",
                "wagtail_api_forms.home.context_processors.branding",
            ],
        },
    },
]

WSGI_APPLICATION = "wagtail_api_forms.wsgi.application"


# Database
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": DB_DIR / "db.sqlite3",
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

# Cache
# https://docs.djangoproject.com/en/4.0/topics/cache/#database-caching
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    },
}


# Password validation
# https://docs.djangoproject.com/en/3.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

AUTH_USER_MODEL = "users.CustomUser"

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
]


# Internationalization
# https://docs.djangoproject.com/en/3.1/topics/i18n/

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Europe/Berlin"
USE_I18N = True
USE_L10N = True
USE_TZ = True
FIRST_DAY_OF_WEEK = 1
WAGTAIL_I18N_ENABLED = True

WAGTAIL_CONTENT_LANGUAGES = LANGUAGES = [
    ("en", _("English")),
    ("de", _("German")),
]

LOCALE_PATHS = [
    "locale",
]


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.1/howto/static-files/

STATICFILES_FINDERS = [
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
]

STATICFILES_DIRS = [
    ASSETS_DIR,
    PROJECT_DIR / "static",
]

# ManifestStaticFilesStorage is recommended in production, to prevent outdated
# JavaScript / CSS assets being served from cache (e.g. after a Wagtail upgrade).
# See https://docs.djangoproject.com/en/3.1/ref/contrib/staticfiles/#manifeststaticfilesstorage
# Check bootstrap-icons bug: https://github.com/twbs/icons/issues/563

# https://whitenoise.readthedocs.io/en/latest/django.html#add-compression-and-caching-support
# STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",  # "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

STATIC_ROOT = BASE_DIR / "_run" / "staticfiles"
STATIC_URL = "/static/"

MEDIA_ROOT = DATA_DIR / "media"
MEDIA_URL = "/media/"


SITE_ID = 1

# https://docs.wagtail.io/en/stable/reference/settings.html?highlight=sendfile#documents
# SENDFILE_BACKEND = 'sendfile.backends.mod_wsgi'
# https://django-sendfile2.readthedocs.io/en/latest/backends.html#mod-wsgi-backend
# SENDFILE_ROOT = str(BASE_DIR / 'media' / 'images')
# SENDFILE_URL = '/private'

# X_FRAME_OPTIONS = 'SAMEORIGIN'

# https://docs.djangoproject.com/en/dev/ref/settings/#std:setting-CSRF_COOKIE_SAMESITE
# CSRF_COOKIE_SAMESITE='Lax'

# https://docs.djangoproject.com/en/dev/ref/settings/#std:setting-SESSION_COOKIE_SAMESITE
# SESSION_COOKIE_SAMESITE='Lax'


# Email these people full exception information
# https://docs.djangoproject.com/en/1.9/ref/settings/#admins
ADMINS = [x.split(":") for x in env.list("DJANGO_ADMINS")]
MANAGERS = ADMINS
DEFAULT_FROM_EMAIL = env.str("DEFAULT_FROM_EMAIL")
SERVER_EMAIL = env.str("SERVER_EMAIL")
EMAIL_SUBJECT_PREFIX = env.str("EMAIL_SUBJECT_PREFIX")


# Wagtail settings
# https://docs.wagtail.io/en/stable/reference/settings.html
WAGTAIL_SITE_NAME = "wagtail_api_forms"
WAGTAIL_ALLOW_UNICODE_SLUGS = False
WAGTAIL_MODERATION_ENABLED = False
WAGTAILDOCS_EXTENSIONS = ["pdf", "txt"]  # 'docx'
WAGTAILIMAGES_MAX_UPLOAD_SIZE = 5 * 1024 * 1024  # i.e. 5MB
WAGTAILIMAGES_IMAGE_MODEL = "home.CustomImage"
WAGTAILDOCS_DOCUMENT_MODEL = "home.CustomDocument"
WAGTAIL_WORKFLOW_ENABLED = False
WAGTAIL_GRAVATAR_PROVIDER_URL = None
WAGTAILFORMS_HELP_TEXT_ALLOW_HTML = True

# Base URL to use when referring to full URLs within the Wagtail admin backend -
# e.g. in notification emails. Don't include '/admin' or a trailing slash
WAGTAILADMIN_BASE_URL = env.str("WAGTAILADMIN_BASE_URL")


CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"


# REST_FRAMEWORK = {
#     'DEFAULT_PERMISSION_CLASSES': [
#         # 'rest_framework.permissions.IsAuthenticated',
#         'rest_framework.permissions.IsAdminUser',
#     ],
#     'DEFAULT_AUTHENTICATION_CLASSES': (
#         # Admin API returning no pages in Wagtail 2.6 #5585
#         # https://github.com/wagtail/wagtail/issues/5585
#         'rest_framework.authentication.SessionAuthentication',
#         # 'rest_framework_simplejwt.authentication.JWTAuthentication',
#     )
# }


# django-cors-headers
# https://github.com/adamchainz/django-cors-headers#setup
CORS_URLS_REGEX = r"^/api/formsubmission/.*$"


# https://django-csp.readthedocs.io/en/latest/index.html
# https://www.laac.dev/blog/content-security-policy-using-django/
# https://wolfgang.reutz.at/2018/10/12/django-and-content-security-policy/
CSP_REPORT_ONLY = False

CSP_FRAME_ANCESTORS = ("'self'",)
CSP_FRAME_ANCESTORS += tuple(env.list("FORMBUILDER_CSP_FRAME_ANCESTORS"))

CSP_EXCLUDE_URL_PREFIXES = (
    "/admin/",
    "/django-admin/",
    "/docs/",
)
# unsafe-inline needed for inline CSS, e.g. via <style>...</style> or style="":
CSP_STYLE_SRC = (
    "'self'",
    "'unsafe-inline'",
)
CSP_SCRIPT_SRC = (
    "'self'",
    "'unsafe-inline'",
    "'unsafe-eval'",
)

# https://github.com/adamalton/django-csp-reports#how-do-i-use-this-thing
# CSP_REPORT_URI = reverse_lazy('report_csp')
# CSP_REPORTS_EMAIL_ADMINS = False
# CSP_REPORTS_LOG = True
# CSP_REPORTS_SAVE = True
# CSP_REPORTS_LOG_LEVEL = 'debug'


# https://github.com/mbi/django-simple-captcha
# https://starcross.dev/blog/6/customising-django-simple-captcha/
def captcha_challenge():
    import random

    challenge = ""
    response = ""
    for i in range(4):
        digit = random.randint(0, 9)
        challenge += str(digit)
        response += str((digit + 1) % 10)
    return challenge, response


CAPTCHA_FONT_SIZE = 34
CAPTCHA_BACKGROUND_COLOR = "#006c66"
CAPTCHA_FOREGROUND_COLOR = "#ffffff"
CAPTCHA_LETTER_ROTATION = 0
CAPTCHA_NOISE_FUNCTIONS = []
CAPTCHA_CHALLENGE_FUNCT = captcha_challenge


# https://github.com/edoburu/django-private-storage
PRIVATE_STORAGE_ROOT = DATA_DIR / "attachments/"
# PRIVATE_STORAGE_AUTH_FUNCTION = 'private_storage.permissions.allow_authenticated'

SESSION_ENGINE = "django.contrib.sessions.backends.db"

# Task queue huey
# https://huey.readthedocs.io/en/latest/
_HUEY_FILENAME = "wagtailapiforms_huey"
_HUEY_DB_FILEPATH = f"{DATA_DIR}/db/{_HUEY_FILENAME}.sqlite"

HUEY = {
    "huey_class": "huey.SqliteHuey",
    "filename": _HUEY_DB_FILEPATH,
    "name": _HUEY_FILENAME,
    "immediate": False,
    "results": True,
    "store_none": True,
    "consumer": {
        "workers": 2,  # use 2 threads
    },
}

# WhiteNoise
WHITENOISE_INDEX_FILE = True

# Add extra output directories that WhiteNoise can serve as static files
# *outside* of `staticfiles`.
MORE_WHITENOISE = [
    {"directory": BASE_DIR / "_run" / "docs" / "html", "prefix": "docs/"},
]

# Local settings
FORMBUILDER_EMAIL_DATE_FORMAT = "l d.m.Y"
FORMBUILDER_EMAIL_DATETIME_FORMAT = "l d.m.Y H:i"

FORMBUILDER_DEFAULT_CSS_VARIABLES = {
    "primary_accent_color": "rgb(4, 55, 242)",
    "primary_accent_color_darken": "rgb(3, 36, 156)",
    "primary_accent_gray": "rgb(216, 216, 216)",
}

FORMBUILDER_WHITELIST_IPS_ATTACHMENT_REQUEST = env.list(
    "FORMBUILDER_WHITELIST_IPS_ATTACHMENT_REQUEST"
)

# Local settings populated by .env
FORMBUILDER_USE_ANTIVIR_SERVICE = env.bool(
    "FORMBUILDER_USE_ANTIVIR_SERVICE", default=True
)
FORMBUILDER_MAX_UPLOAD_SIZE = (
    env.int("FORMBUILDER_MAX_UPLOAD_MB", default=3) * 1024 * 1024
)
FORMBUILDER_ALLOWED_DOCUMENT_FILE_TYPES = env.list(
    "FORMBUILDER_ALLOWED_DOCUMENT_FILE_TYPES", default=[".pdf", ".txt"]
)
FORMBUILDER_ALLOWED_IMAGE_FILE_TYPES = env.list(
    "FORMBUILDER_ALLOWED_IMAGE_FILE_TYPES", default=[".jpg", ".jpeg", ".png"]
)


# Setting variations between development and production (see end of this settings file)
# Security
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")

# Email
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = env.str("EMAIL_HOST")
EMAIL_PORT = env.int("EMAIL_PORT")

# LDAP
AUTH_LDAP = env.bool("AUTH_LDAP")


if DEBUG:
    print(f"{AUTH_LDAP=}")
    print(
        f"FORMBUILDER_MAX_UPLOAD_SIZE in MegaBytes is {FORMBUILDER_MAX_UPLOAD_SIZE / (1024 * 1024)}"
    )
    print(f"{FORMBUILDER_ALLOWED_DOCUMENT_FILE_TYPES=}")
    print(f"{FORMBUILDER_ALLOWED_IMAGE_FILE_TYPES=}")
    print(f"{FORMBUILDER_USE_ANTIVIR_SERVICE=}")
    print(f"{FORMBUILDER_WHITELIST_IPS_ATTACHMENT_REQUEST=}")
    print(f"{CSP_FRAME_ANCESTORS=}")
    print(f"{ALLOWED_HOSTS=}")

    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
    ALLOWED_HOSTS = ["*"]
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
    # SENDFILE_BACKEND = 'sendfile.backends.development'
