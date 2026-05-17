#!/bin/bash

set -o errexit

# Derived at runtime — assumes:
#   - bare repo is named <project_name>.git (CWD when this hook fires)
#   - work tree lives at $HOME/<project_name>
#   - Django package name = project_name with hyphens converted to underscores
project_name="$(basename "$PWD" .git)"
project_pkg="${project_name//-/_}"
worktree="$HOME/$project_name"

GIT_WORK_TREE="$worktree" git checkout -f main

echo "Change directory to: $worktree ..."
cd "$worktree"

echo "==================================================="
echo "Environment"
echo "==================================================="
echo "user:         $(whoami)"
echo "home:         $HOME"
echo "pwd:          $PWD"
echo "project_name: $project_name"
echo "project_pkg:  $project_pkg"
echo "worktree:     $worktree"

echo "==================================================="
echo "Ensure docker-compse is up"
echo "==================================================="

docker-compose down
docker-compose up --build --force-recreate --no-deps --detach

echo "==================================================="
echo "Deploy django backend"
echo "==================================================="

echo "Activate virtual environment..."
source "$HOME/venv/bin/activate"

echo "Ensure pip and wheel are uptodate..."
pip install --upgrade pip wheel setuptools

echo "Install pip requirements..."
pip install -r requirements.txt

echo "[npm] Installing npm requirements..."
npm install --quiet

echo "Running app-level deploy steps (scripts/deploy.sh)..."
./scripts/deploy.sh

echo "==================================================="
echo "Restart huey"
echo "==================================================="

# Required for `systemctl --user` from a non-login shell.
export XDG_RUNTIME_DIR="/run/user/$UID"
export DBUS_SESSION_BUS_ADDRESS="unix:path=${XDG_RUNTIME_DIR}/bus"
systemctl --user restart "${project_pkg}_huey.service"
echo "Huey restarted!"

echo "Reload app..."
touch "$worktree/$project_pkg/wsgi.py"
echo "Reloaded app!"

echo "Run check --deploy..."
python3 manage.py check --deploy
echo "Done running check --deploy"
