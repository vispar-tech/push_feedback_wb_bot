#!/bin/bash

set -o errexit
set -o nounset

rm -f './celerybeat.pid'

cd src

poetry run celery -A core beat -l INFO --scheduler django_celery_beat.schedulers:DatabaseScheduler
