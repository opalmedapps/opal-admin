# SPDX-FileCopyrightText: Copyright (C) 2021 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

FROM python:3.13.11-alpine3.22 AS build

COPY --from=ghcr.io/astral-sh/uv:0.10.3 /uv /uvx /bin/

# dependencies for building Python packages
RUN apk add --no-cache build-base \
  # install git in case dependencies are installed from version control
  && apk add --no-cache git \
  # mysqlclient dependencies
  && apk add --no-cache mariadb-dev \
  # argon2-cffi dependencies
  && apk add --no-cache libffi-dev

# for which environment the build is done: dev or prod
ARG ENV=prod

WORKDIR /app

# Install dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    if [ "$ENV" = "prod" ]; then \
      uv sync --locked --no-editable --no-default-groups --extra prod --compile-bytecode; \
    else \
      uv sync --locked --no-editable --no-default-groups --group dev --compile-bytecode; \
    fi


FROM python:3.13.11-alpine3.22

RUN apk upgrade --no-cache \
  # mysqlclient runtime dependencies
  && apk add --no-cache mariadb-dev \
  # Translation dependencies
  && apk add --no-cache gettext \
  # kaleido dependencies
  && apk add --no-cache chromium

# add venv to search path
ENV PATH=/app/.venv/bin:$PATH

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1


EXPOSE 8000
WORKDIR /app

RUN addgroup --system appuser \
  && adduser --system --ingroup appuser appuser \
  && chown -R appuser:appuser /app

# get venv from build stage
COPY --from=build /app/.venv /app/.venv
COPY docker/docker-entrypoint.sh /docker-entrypoint.sh

# copy only the required files
COPY ./config/ ./config
COPY ./opal/ ./opal
COPY ./locale/ ./locale
COPY ./LICENSES ./LICENSES
COPY manage.py .
COPY .env.sample .
COPY docker/start.sh ./start.sh
COPY LICENSE .
COPY REUSE.toml .

# Compile messages so translations are baked into the image
RUN cp .env.sample .env \
  && DJANGO_SETTINGS_MODULE=config.settings.test python manage.py compilemessages --ignore .venv \
  && rm .env \
  # ensure the uploads directory exists with appuser as the owner
  && mkdir -p ./opal/media/uploads \
  && chown appuser:appuser ./opal/media/uploads \
  # ensure the logs directory exists for production logs
  && mkdir /logs \
  && chown appuser:appuser /logs

USER appuser

ENTRYPOINT [ "/docker-entrypoint.sh" ]
CMD [ "/app/start.sh" ]
