# Opal Backend Prototype

[![pipeline status](https://gitlab.com/mschoettle/backend-prototype/badges/main/pipeline.svg)](https://gitlab.com/mschoettle/backend-prototype/-/commits/main) [![coverage report](https://gitlab.com/mschoettle/backend-prototype/badges/main/coverage.svg)](https://gitlab.com/mschoettle/backend-prototype/-/commits/main)

## Requirements

This project has the following requirements to be available on your system:

* [Docker Desktop](https://docs.docker.com/desktop/) (or Docker Engine on Linux)
* Python 3.9 or higher

## Getting Started

### Configuration

All configuration is stored within the `.env` file to follow the [12factor app methodology](https://12factor.net/config) on storing config in the environment.

Copy the `.env.sample` and adjust the values.

These configuration parameters are read by `docker compose` and in `settings.py` via [`django-environ`](https://github.com/joke2k/django-environ).

Any setting that depends on the environment it is run in should be exposed via the `.env`.

### Docker

This project comes with a `docker-compose.yml` file providing you with a database and the app in their respective containers.
The Django app is built with a custom image (defined in `Dockerfile`).

Execute the following command to start up the containers: `docker compose up`

If you need to rebuild the app, you can either run `docker compose build` or `docker compose up --build` to force a rebuild.

To connect to the app container, run `docker compose exec app bash` (or any specific command instead of `bash`).

### Python virtual environment

In order for linting, type checking, unit testing etc. to be available in your IDE and for `pre-commit`, we recommend to set up a local virtual environment. This also makes it possible to execute management commands directly from the virtual environment. Otherwise, everything has to be run from inside the container (e.g., by using the [Remote Containers vscode extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers)).

1. `python3 -m venv --prompt 'opal' .venv`
2. `source .venv/bin/activate`
3. `python -m pip install --upgrade pip`
4. `python -m pip install -r requirements/development.txt`

### Pre-commit

This project contains a configuration for [`pre-commit`](https://pre-commit.com/) (see `.pre-commit-config.yaml`).

Install the `pre-commit` hooks via `pre-commit install`.

## Development

### Dependencies

See the `requirements/` folder for the requirement files depending on the environment.

#### Update dependencies

The dependencies are kept up-to-date by using [Renovate Bot](https://www.whitesourcesoftware.com/free-developer-tools/renovate/). See the file `renovate.json` for its configuration.

However, you can also manually update dependencies:

1. Install [`pip-upgrader`](https://github.com/simion/pip-upgrader): `pip install pip-upgrader`
2. Run `pip-upgrade` to update the desired dependencies
3. Run linting, type checking and tests with coverage (see below) to ensure that everything still works as expected
4. Commit the updates to the requirements file(s)

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

`vscode` should pick up the virtual environment and run `flake8` and `mypy` while writing code.
