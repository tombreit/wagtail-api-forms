echo "Ensure docker-compse is up"
docker-compose down
docker-compose up --build --force-recreate --no-deps --detach

pip install -r requirements.txt

mkdir -p /path/to/wagtail_api_forms/media
mkdir -p /path/to/wagtail_api_forms/staticfiles

python3 manage.py migrate --noinput

echo "Build documentation..."
make --directory=docs/ json

echo "Run collectstatic (first run for having files handy for being included by npm scripts)..."
python3 manage.py collectstatic --noinput

python3 manage.py compilemessages --ignore=assets/* --ignore=node_modules/* --ignore=staticfiles/*

npm install --quiet
npm run --silent prod

echo "Run collectstatic (second, final run)..."
python3 manage.py collectstatic --noinput

systemctl --user restart wagtail_api_forms_huey.service
touch /path/to/wagtail_api_forms/wsgi.py
python3 manage.py check --deploy
