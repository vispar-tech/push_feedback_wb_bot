#!/bin/bash

set -o errexit
set -o pipefail
set -o nounset

cd src/

poetry run python manage.py migrate
poetry run gunicorn --access-logfile ./logs/gunicorn.log --workers 4 --bind 0.0.0.0:8000 --worker-class gevent --timeout 600 --log-level=debug core.wsgi:application

cd ..
