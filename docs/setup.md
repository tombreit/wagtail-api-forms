# Setup


## Setup

### Requirements

* Assuming Debian GNU/Linux 11+
* ``python 3.9+,``
* ``pip``, preferably in a virtual environment
* ``npm``
* Docker (for clamav)

### Bundle static assets

```bash
npm install && npm run prod
```

### Set environment via .env file

Copy ``env.template`` to ``.env`` and set your environment variables. 

### Start wagtail-api-forms

```bash
source path/to/your/venv/bin/activate
(venv) pip install -r requirements.txt
(venv) ./manage.py createsuperuser
(venv) ./manage.py runserver
```

### Site & Branding

* Set site config via: http://fqdn/admin/sites/
* (In case of multilingualism) Setup root pages for every language version: http://fqdn/admin/pages/
* Set brand name, logo etc via: http://fqdn/admin/settings/home/brandingsettings/1/
* Set footer links (Privacy policy etc.) via: http://fqdn/admin/snippets/home/footerlinks/


## Misc

### API

#### Endpoints

* http://fqdn/api/formsubmission/v2/ (paginated)

#### Add API users

```python
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token

# Add django user without password:
user = get_user_model().objects.create_user("username")
user.save()

# Generate token for that user:
Token.objects.create(user=user)

# or via management command:
# ./manage.py drf_create_token <username>

# or via django-admin:
# http://fqdn/django-admin/authtoken/tokenproxy/
```

...and set this user in wagtail admin for the desired form page in page settings.
For translated forms (e.g. two formpages if EN+DE), the api user must be set for both form pages.


### Documentation

Documentation files are build with Sphinx and served via WhiteNoise from `/docs/`.

Build the documentation with
```bash
make --directory docs/ html

# or with live reload
sphinx-autobuild -a --port 0 docs docs/_build/html
```

### Backup

* ``.env`` - your configured environment
* ``_data/[media|attachments|db]`` - your sqlite database and uploaded files


### Virus scanning

Virus scanning is implemented in a ClamAV docker container and a django task queue (huey).

```{note}
   Virus scanning could be disabled via ``.env`` setting ``FORMBUILDER_USE_ANTIVIR_SERVICE=false``.
```

```bash
docker-compose up
manage.py run_huey
```

### Localization

```bash
./manage.py makemessages --locale de --ignore=assets/* --ignore=node_modules/* --ignore=staticfiles/* --ignore=.venv/*
./manage.py compilemessages --ignore=assets/* --ignore=node_modules/* --ignore=staticfiles/* --ignore=.venv/*
```

## Production environment

```{admonition} Apache+mod_wsgi
* If using apache2 and mod_wsgi, do not store huey database in global ``/tmp/`` as
apache2 is running with ``PrivateTmp`` and the mod_wsgi process could not put
its tasks on the queue (https://stackoverflow.com/questions/68185057/huey-db-task-successfully-registered-by-consumer-but-does-not-receive-execut).
* Apache/mod_wsgi: ``WSGIPassAuthorization On`` (https://www.django-rest-framework.org/api-guide/authentication/#apache-mod_wsgi-specific-configuration)
```


### Configuration examples

```{admonition} Webserver and media /attachments directory
:class: danger

Do **not** allow the webserver to serve ``_data/attachments/`` files - these files are served by Django to check for various criteria (is authenticated, from whitelisted remote ip, virus checked etc.).
```

#### Webserver (Apache)

```{literalinclude} configs/apache.conf
:language: apacheconf
```

#### Task Queue (huey)

```{literalinclude} configs/wagtailapiforms-huey.service
:language: ini
```

#### Production deployment steps (eg. git post receive hook) 

```{literalinclude} configs/git-post-receive-hook.sh
:language: bash
```
