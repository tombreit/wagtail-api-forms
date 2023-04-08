# Setup

## Configuration - Deployment

To get this project up and running on your host:

### Requirements

* Assuming Debian GNU/Linux 11+
* ``python 3.9+,``, ``pip``, preferably in a virtual environment
* ``npm``
* docker (for clamav)

### Django and Wagtail

1. **Bundle static assets**

   ```bash
   npm install && npm run prod
   ```

1. **Set environment via .env file**: 

   Copy ``env.template`` to ``.env`` and set your environment variables. 

1. **Start wagtail-api-forms**:

   ```bash
   source path/to/your/venv
   (venv) pip install -r requirements.txt
   ```


### Docs

Documentation files are build with Sphinx and served via WhiteNoise from `/docs/`.

Build the documentation with
```bash
make --directory docs/ html

# or with live reload
sphinx-autobuild -a --port 0 docs docs/_build/html
```


### Virus scanning

Virus scanning is implemented in a ClamAV docker container and a django task queue (huey).

```bash
docker-compose up
manage.py run_huey
```

**Note:** Virus scanning could be disabled via ``.env`` setting ``FORMBUILDER_USE_ANTIVIR_SERVICE=false``.

### Localization - App

```bash
./manage.py makemessages --locale de --ignore=assets/* --ignore=node_modules/* --ignore=staticfiles/* --ignore=.venv/*
./manage.py compilemessages --ignore=assets/* --ignore=node_modules/* --ignore=staticfiles/* --ignore=.venv/*
```

### Static assets

```bash
# Build static assets via:
npm run prod
```

### Production environment

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

### Backup

* ``.env`` - your configured environment
* ``_data/[media|attachments|db]`` - your sqlite database and uploaded files


## Configuration - App

### Branding

* Set site config via: http://fqdn/admin/sites/
* Set brand name, logo etc via: http://fqdn/admin/settings/home/brandingsettings/1/
* Set footer links (Privacy policy etc.) via: http://fqdn/admin/snippets/home/footerlinks/

### Localization - Editors
1. Localize page
1. Add localized content

## API

### Endpoints

* ~~http://fqdn/api/formsubmission/v1/~~ (deprecated)
* http://fqdn/api/formsubmission/v2/ (paginated)

### Add API users

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

## External form rendering

* https://github.com/jsonform/jsonform
* https://github.com/BuGlessRB/outperform
* https://brainfoolong.github.io/form-data-json/example/playground.html
