#!/bin/sh
# option pipefail available on alpine sh
# shellcheck disable=SC3040
set -euo pipefail

python /app/manage.py collectstatic --noinput


/usr/local/bin/gunicorn config.wsgi \
    --workers=4 \
    --bind 0.0.0.0:8000  \
    --timeout 90 \
    --chdir=/app
