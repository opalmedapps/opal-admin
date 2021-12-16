#!/bin/sh
set -eux

python /app/manage.py collectstatic --noinput


/usr/local/bin/gunicorn digitalprint.wsgi:application \
    --workers=3 \
    --bind 0.0.0.0:8000  \
    --timeout 90 \
    --chdir=/app
