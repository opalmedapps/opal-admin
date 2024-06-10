#!/bin/sh
# option pipefail available on alpine sh
# shellcheck disable=SC3040
set -euo pipefail

python /app/manage.py collectstatic --noinput

# store temporary file in memory storage
# https://pythonspeed.com/articles/gunicorn-in-docker/
/usr/local/bin/gunicorn config.wsgi \
    --workers=4 \
    --worker-tmp-dir /dev/shm \
    --bind 0.0.0.0:8000  \
    --timeout 90 \
    --chdir=/app
