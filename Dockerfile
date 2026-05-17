# Python runtime on Debian trixie (Debian 13).
FROM python:3.13-slim-trixie

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

# Install system packages required by Wagtail and Django (plus npm to install
# frontend dependencies; the build itself runs at container start via
# scripts/deploy.sh).
RUN apt-get update --yes --quiet \
    && apt-get install --yes --quiet --no-install-recommends \
      build-essential \
      libjpeg62-turbo-dev \
      zlib1g-dev \
      libwebp-dev \
      libldap2-dev \
      libsasl2-dev \
      libmagic-dev \
      gettext \
      npm \
    && rm -rf /var/lib/apt/lists/*

# Install the project requirements.
COPY requirements.txt /
RUN pip install --no-cache-dir --upgrade pip wheel setuptools \
    && pip install --no-cache-dir "gunicorn==20.0.4" \
    && pip install --no-cache-dir -r /requirements.txt

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

# Install npm dependencies at build time so the image layer caches them and
# container start doesn't need npm registry access. The asset build itself,
# collectstatic, compilemessages, docs build, and migrate all run at container
# start via scripts/deploy.sh — single source of truth, shared with the
# bare-metal post-receive deploy.
RUN npm install --quiet

# Runtime command. scripts/deploy.sh runs the app-level deploy steps (build,
# collectstatic, compilemessages, docs, migrate) before gunicorn starts.
# Single-replica deployment by design; for multi-replica setups, move the
# migrate step out of deploy.sh into a release-phase job to avoid races.
CMD ["sh", "-c", "./scripts/deploy.sh && gunicorn wagtail_api_forms.wsgi:application"]
