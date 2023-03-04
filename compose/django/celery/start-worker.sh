#!/bin/bash

set -o errexit
set -o nounset

cd src

poetry run python manage.py celery_worker
