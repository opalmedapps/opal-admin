#!/bin/sh

# SPDX-FileCopyrightText: Copyright (C) 2021 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

# option pipefail available on alpine sh
# shellcheck disable=SC3040
set -euo pipefail

python /app/manage.py collectstatic --noinput

# store temporary file in memory storage
# https://pythonspeed.com/articles/gunicorn-in-docker/
gunicorn config.wsgi \
    --workers=4 \
    --worker-tmp-dir /dev/shm \
    --bind 0.0.0.0:8000  \
    --timeout 90 \
    --chdir=/app
