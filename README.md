# Opal API Prototype

## Setup

### Python virtual environment

1. `python3.9 -m venv --prompt 'dp' .venv`
1. `source .venv/bin/activate`
1. `python -m pip install --upgrade pip`
1. `python -m pip install -r requirements/development.txt`

### Requirements

See the `requirements/` folder for the requirement files depending on the environment.

### Update dependencies

1. Run `pip-upgrade` to update the desired dependencies
1. Run tests with coverage (see below) to ensure that everything still works as expected
1. Commit the updates to the requirements file(s)

## Configuration files

* `.envs/postgres.dev`: environment variables for the development postgres database
* `.env`: environment variables for the Django app

## Required volumes in Docker container

* `/data/jobs`: directory to store jobs JSON files of new jobs into (e.g., produced by wmd-xml-parser)
* `/data/invoices`: directory to store downloaded invoices to (by wmd-scraper)

## Development

### Run project in development

The easiest way is to use `docker-compose` since the database is required.

`docker-compose up`

This will keep the app in the foreground with the output from `runserver`.

### Linting, Testing, Coverage

The configuration (such as which files to exclude is in `setup.cfg` and `pytest.ini`). The following commands can all be executed from the project root.

1. Linting with `flake8`: Execute `flake8`
1. Static type checking with `mypy`: Execute `mypy`
1. Execute tests with `pytest`: Execute `pytest`
1. Execute coverage with `coverage`:
    1. Execute tests with coverage: `coverage run -m pytest`
    1. Reporting: `coverage report`
    1. Get HTML report (optional): `coverage html`, then `open htmlcov/index.html` to open the report in the browser
    1. Erase old coverage data: `coverage erase`

**Note:** The tests require a database. Therefore, if you use `docker-compose`, while everything is *up*, execute: `docker-compose run app bash -c "coverage run -m pytest && coverage report"` to run tests with coverage and receive a report.

### Load production data into development

1. Optional: Delete existing data in development first: In the shell (`python manage.py shell_plus`): `Complaint.objects.delete()`, then `Job.objects.delete()`
1. Dump from production: `docker-compose exec app python manage.py dumpdata jobs --indent 2 --natural-foreign > jobs.json`
1. Load into dev: `[docker-compose exec app] python manage.py loaddata --app jobs jobs.json`
