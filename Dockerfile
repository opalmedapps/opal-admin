# SPDX-FileCopyrightText: Copyright (C) 2021 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

FROM python:3.12.9-alpine3.20 AS build

# dependencies for building Python packages
RUN apk add --no-cache build-base \
  # install git in case dependencies are installed from version control
  && apk add --no-cache git \
  # mysqlclient dependencies
  && apk add --no-cache mariadb-dev \
  # argon2-cffi dependencies
  && apk add --no-cache libffi-dev

# for which environment the build is done: development or production
ARG ENV=production

# Install pip requirements
COPY ./requirements /tmp/
RUN python -m pip install --no-cache-dir --upgrade pip \
  && python -m pip install --no-cache-dir -r /tmp/${ENV}.txt


FROM python:3.12.9-alpine3.20

RUN apk upgrade --no-cache \
  # mysqlclient runtime dependencies
  && apk add --no-cache mariadb-dev \
  # Translation dependencies
  && apk add --no-cache gettext \
  # kaleido dependencies
  && apk add --no-cache chromium


# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

EXPOSE 8000
WORKDIR /app

RUN addgroup --system appuser \
  && adduser --system --ingroup appuser appuser \
  && chown -R appuser:appuser /app

# get Python packages lib and bin
COPY --from=build /usr/local/bin /usr/local/bin
COPY --from=build /usr/local/lib /usr/local/lib
COPY docker/docker-entrypoint.sh /docker-entrypoint.sh

# copy only the required files
COPY ./config/ ./config
COPY ./opal/ ./opal
COPY ./locale/ ./locale
COPY manage.py .
COPY .env.sample .
COPY docker/start.sh ./start.sh

# Compile messages so translations are baked into the image
RUN cp .env.sample .env \
  && DJANGO_SETTINGS_MODULE=config.settings.test python manage.py compilemessages \
  && rm .env \
  # ensure the uploads directory exists with appuser as the owner
  && mkdir -p ./opal/media/uploads \
  && chown appuser:appuser ./opal/media/uploads \
  # ensure the logs directory exists for production logs
  && mkdir /logs \
  && chown appuser:appuser /logs

USER appuser

ENTRYPOINT [ "/docker-entrypoint.sh" ]
CMD [ "./start.sh" ]
