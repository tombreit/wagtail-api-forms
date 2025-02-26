echo "==================================================="
echo "Ensure docker-compse is up"
echo "==================================================="

docker-compose down
docker-compose up --build --force-recreate --no-deps --detach

echo "==================================================="
echo "Deploy django backend"
echo "==================================================="

echo "[npm] Installing npm requirements..."
npm install --quiet

echo "[npm] Building static assets..."
npm run --silent build

echo "[python] Activate virtual environment..."
source /path/to/venv/bin/activate

echo "[python] Ensure pip and wheel are uptodate..."
pip install --upgrade pip wheel setuptools

echo "[python] Install pip requirements..."
pip install -r requirements.txt

echo "[docs] Build documentation..."
make --directory docs html

echo "[django] Will migrate now..."
python3 manage.py migrate --noinput

echo "[django] Run compilemessages..."
python3 manage.py compilemessages --ignore=assets/* --ignore=node_modules/* --ignore=staticfiles/*

echo "[django] Run collectstatic..."
python3 manage.py collectstatic --noinput

echo "==================================================="
echo "Restart huey"
echo "==================================================="

### needed for systemctl --user restart <wagtail-api-forms>.service
export XDG_RUNTIME_DIR="/run/user/$UID"
export DBUS_SESSION_BUS_ADDRESS="unix:path=${XDG_RUNTIME_DIR}/bus"
systemctl --user restart wagtail_api_forms_huey.service
echo "Huey restarted!"

echo "Reload app..."
touch /path/to/wagtail-api-forms/wagtail_api_forms/wsgi.py

echo "Run check --deploy..."
python3 manage.py check --deploy
