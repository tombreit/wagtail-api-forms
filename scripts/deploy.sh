#!/usr/bin/env bash
#
# App-level deploy steps shared by bare-metal and container deployments.
# Run from the project root, after Python and npm dependencies are installed.
#
set -euo pipefail

echo "[deploy] npm run build"
npm run --silent build

echo "[deploy] collectstatic"
python manage.py collectstatic --noinput

echo "[deploy] compilemessages"
python manage.py compilemessages \
    --ignore=assets/* \
    --ignore=node_modules/* \
    --ignore=staticfiles/*

echo "[deploy] sphinx-build docs"
sphinx-build -M html docs/ _run/docs -a

echo "[deploy] migrate"
python manage.py migrate --noinput

echo "[deploy] done"
