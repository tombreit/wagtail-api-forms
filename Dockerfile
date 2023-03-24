# Use an official Python runtime based on Debian 10 "buster" as a parent image.
FROM python:3.9-slim-buster

# Use virtualenv even in docker container
# https://pythonspeed.com/articles/activate-virtualenv-dockerfile/
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Add user that will be used in the container.
RUN useradd wagtail

# Port used by this container to serve HTTP.
EXPOSE 8000

# Set environment variables.
# 1. Force Python stdout and stderr streams to be unbuffered.
# 2. Set PORT variable that is used by Gunicorn. This should match "EXPOSE"
#    command.
ENV PYTHONUNBUFFERED=1 \
    PORT=8000

# Install system packages required by Wagtail and Django.
RUN apt-get update --yes --quiet \
    && apt-get install --yes --quiet --no-install-recommends \
      build-essential \
      libjpeg62-turbo-dev \
      zlib1g-dev \
      libwebp-dev \
      libldap2-dev \
      libsasl2-dev \
      libmagic-dev \
      npm \
    && rm -rf /var/lib/apt/lists/*

# Install the project requirements.
COPY requirements.txt /
RUN pip install --upgrade pip wheel setuptools \
    && pip install "gunicorn==20.0.4" \
    && pip install -r /requirements.txt \
    && rm -rf /root/.cache/

# Use /app folder as a directory where the source code is stored.
WORKDIR /app

# Set this directory to be owned by the "wagtail" user. This Wagtail project
# uses SQLite, the folder needs to be owned by the user that
# will be writing to the database file.
RUN chown wagtail:wagtail /app

# Copy the source code of the project into the container.
COPY --chown=wagtail:wagtail . .

# Use user "wagtail" to run the build commands below and the server itself.
USER wagtail

# Collect static files.
RUN python manage.py collectstatic --noinput --clear

# Runtime command that executes when "docker run" is called, it does the
# following:
#   1. Migrate the database.
#   2. Start the application server.
# WARNING:
#   Migrating database at the same time as starting the server IS NOT THE BEST
#   PRACTICE. The database should be migrated manually or using the release
#   phase facilities of your hosting platform. This is used only so the
#   Wagtail instance can be started with a simple "docker run" command.
CMD set -xe; \
    python manage.py migrate --noinput; \
    python manage.py collectstatic --noinput; \
    python manage.py compilemessages --ignore=assets/* --ignore=node_modules/* --ignore=staticfiles/*; \
    npm install --quiet; \
    npm run --silent prod; \
    python manage.py collectstatic --noinput; \
    gunicorn wagtail_api_forms.wsgi:application
