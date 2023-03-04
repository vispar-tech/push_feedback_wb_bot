#!/bin/bash

set -o errexit
set -o nounset

cd src

worker_ready() {
    poetry run celery -A core inspect ping
}

until worker_ready; do
  >&2 echo 'Celery workers not available'
  sleep 1
done
>&2 echo 'Celery workers is available'

poetry run celery -A core --broker="${CELERY_BROKER}" flower
