# syntax = docker/dockerfile:1.0-experimental
FROM python:3.9.16-slim-bullseye

# for which environment the build is done: development or production
ARG ENV=development

RUN apt-get update \
  # dependencies for building Python packages
  && apt-get install -y build-essential \
  # install git
  && apt-get install git -y \
  # mysqlclient dependencies
  && apt-get install -y default-libmysqlclient-dev \
  # argon2-cffi dependencies
  && apt-get install -y libffi-dev libssl-dev \
  # Translations dependencies
  && apt-get install -y gettext \
  # cron dependencies
  && apt-get install -y cron \
  # cleaning up unused files
  && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
  && rm -rf /var/lib/apt/lists/*

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE 1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED 1

# Install pip requirements
RUN python -m pip install --upgrade pip
COPY ./requirements /tmp/
RUN python -m pip install --no-cache-dir -r /tmp/${ENV}.txt

EXPOSE 8000

COPY docker/docker-entrypoint.sh /docker-entrypoint.sh

WORKDIR /app

ADD . /app

# Set up the cron jobs
COPY ./scripts/cron/* /etc/cron.d/

# Add new cron jobs to the cron tab
RUN crontab /etc/cron.d/crontab

ENTRYPOINT [ "/docker-entrypoint.sh" ]
