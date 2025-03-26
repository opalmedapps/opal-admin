FROM python:3.11.8-alpine3.19 as build

RUN apk upgrade --no-cache \
  # dependencies for building Python packages
  && apk add --no-cache build-base \
  # install git in case dependencies are installed from version control
  && apk add --no-cache git \
  # mysqlclient dependencies
  && apk add --no-cache mariadb-dev \
  # argon2-cffi dependencies
  && apk add --no-cache libffi-dev

# for which environment the build is done: development or production
ARG ENV=development

# Install pip requirements
COPY ./requirements /tmp/
RUN python -m pip install --no-cache-dir --upgrade pip \
  && python -m pip install --no-cache-dir -r /tmp/${ENV}.txt


FROM python:3.11.8-alpine3.19

RUN apk upgrade --no-cache \
  # mysqlclient runtime dependencies
  && apk add --no-cache mariadb-dev \
  # argon2-cffi dependencies
  # && apt-get install -y libffi-dev libssl-dev \
  # Translations dependencies
  && apk add --no-cache gettext
  # cron dependencies
  # && apk add --no-cache cron

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE 1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED 1

EXPOSE 8000

# get Python packages lib and bin
COPY --from=build /usr/local/bin /usr/local/bin
COPY --from=build /usr/local/lib /usr/local/lib
COPY docker/docker-entrypoint.sh /docker-entrypoint.sh

WORKDIR /app

COPY . /app

# Set up the cron jobs
COPY ./scripts/cron/* /etc/cron.d/

# Add new cron jobs to the cron tab and compile languages
RUN crontab /etc/cron.d/crontab \
  && cp .env.sample .env \
  && DJANGO_SETTINGS_MODULE=config.settings.test python manage.py compilemessages \
  && rm .env

ENTRYPOINT [ "/docker-entrypoint.sh" ]
