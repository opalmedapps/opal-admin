# Opal Backend Pilot

[![pipeline status](https://gitlab.com/opalmedapps/backend-pilot/badges/main/pipeline.svg)](https://gitlab.com/opalmedapps/backend-pilot/-/commits/main) [![coverage report](https://gitlab.com/opalmedapps/backend-pilot/badges/main/coverage.svg)](https://gitlab.com/opalmedapps/backend-pilot/-/commits/main) [![wemake-python-styleguide](https://img.shields.io/badge/code%20style-wemake-000000.svg)](https://github.com/wemake-services/wemake-python-styleguide) [![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit) [![Docs](https://img.shields.io/badge/docs-available-brightgreen.svg)](https://opalmedapps.gitlab.io/docs)

## Requirements

This project has the following requirements to be available on your system:

* [Docker Desktop](https://docs.docker.com/desktop/) (or Docker Engine on Linux)
* Python 3.9 or higher

## Getting Started

After cloning this repo, follow the below steps to get started.

### Configuration

All configuration is stored within the `.env` file to follow the [12factor app methodology](https://12factor.net/config) on storing config in the environment. This means that any setting that depends on the environment the app is run in should be exposed via the `.env`.

Copy the `.env.sample` to `.env` and adjust the values as necessary. You need to at least modify `DATABASE_PASSWORD` and `SECRET_KEY`.

These configuration parameters are read by `docker compose` and by `settings.py` (via [`django-environ`](https://github.com/joke2k/django-environ)).

### Docker

This project comes with a `docker-compose.yml` file providing you with a database and the app in their respective containers.
The Django app is built with a custom image (defined in `Dockerfile`).

Execute the following command to start up the containers: `docker compose up`

If you need to rebuild the app, you can either run `docker compose build` before starting the container or `docker compose up --build` to force a rebuild.

To connect to the app container, run `docker compose exec app bash` (or any specific command instead of `bash`).

### Python virtual environment

??? question "Why a virtual environment when there is already a Docker container?"

    While this is not ideal, it makes it easier to run `pre-commit` with the same setup/dependencies for `flake8` and `mypy`. In addition, `vscode` can make use of the virtual environment to call `flake8` and `mypy` and provide the results directly in the editor. Alternatively, the [Remote Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) could be used to develop fully within the container. If you figure out a proper configuration to have linting, typechecking and `pre-commit` running in there, please provide a merge request.

In order for linting, type checking, unit testing etc. to be available in your IDE, and for `pre-commit` to use the same configuration, we recommend to set up a local virtual environment. This also makes it possible to execute management commands directly from the virtual environment without having to execute them within the container. Otherwise, everything has to be run from inside the container (e.g., by calling `docker compose exec app <command>`).

#### Set up the virtual environment

=== "macOS/Linux"

    1. `python3 -m venv --prompt 'opal' .venv`
    2. `source .venv/bin/activate`

=== "Windows"

    1. `python -m venv --prompt 'opal' .venv`
    2. `.\.venv\Scripts\activate`

    **Note:** If activate fails with a security error, run this command to allow local scripts to execute (see [this Stack Overflow discussion](https://stackoverflow.com/q/4037939) for more information): `powershell Set-ExecutionPolicy RemoteSigned -Scope CurrentUser`

#### Install dependencies

Run the following commands within the virtual environment:

1. `python -m pip install --upgrade pip`
2. `python -m pip install -r requirements/development.txt`

??? tip "Installing `mysqlclient` fails"

    In case installing the `mysqlclient` package does not provide a binary for your platform it needs to be built. To do so, the mysql client library needs to be installed on the system.

    === "macOS"
        The easiest is to install it via Homebrew:

        ```shell
        brew install mysql-client
        export PATH="/opt/homebrew/opt/mysql-client/bin:$PATH"
        # install dependencies via pip install
        ```

    === "Windows"
        No detailed steps known. Try to follow the [instructions](https://github.com/PyMySQL/mysqlclient#windows) provided by the `mysqlclient` package.

### Migrate Database and Create Superuser

Before you can start, you need to migrate the database and create a superuser. Execute the following commands either in the virtual environment or in the `app` container.

1. `python manage.py migrate`
2. `python manage.py createsuperuser`

Once this is done, you can go to [http://localhost:8000](http://localhost:8000) to access the frontend. Go to [http://localhost:8000/admin](http://localhost:8000/admin) to log in to the Django admin site with the superuser you created. [http://localhost:8000/api](http://localhost:8000/api) shows the available REST API endpoints to you.

### Pre-commit

This project contains a configuration for [`pre-commit`](https://pre-commit.com/) (see `.pre-commit-config.yaml`).

Install the `pre-commit` hooks via `pre-commit install`.

??? note "Using pre-commit with a git GUI"

    If you are using a git GUI tool (such as Sourcetree) the path might not be set up correctly and pre-commit might not be able to find `flake8` and `mypy`.

    The current known workaround is to specify the required `PATH` for the `pre-commit` hook. Add the following line at the top of `.git/hooks/pre-commit` (after the first line with the bash interpreter):

    ```export PATH=$PATH:"/C/Users/path/to/.venv/Scripts/"```

### Recommended vscode extensions

This project contains recommendations for vscode extensions (see `.vscode/extensions.json`). You should get a popup about this when you open the project. These extensions are also highlighted in the extensions list.

The following extensions are required or strongly recommended:

* [Python](https://marketplace.visualstudio.com/items?itemName=ms-python.python) and [PyLance](https://marketplace.visualstudio.com/items?itemName=ms-python.vscode-pylance)
* [Django](https://marketplace.visualstudio.com/items?itemName=batisteo.vscode-django)
* [EditorConfig for VSCode](https://marketplace.visualstudio.com/items?itemName=editorconfig.editorconfig)
* [YAML](https://marketplace.visualstudio.com/items?itemName=redhat.vscode-yaml)
* [Docker](https://marketplace.visualstudio.com/items?itemName=ms-azuretools.vscode-docker)
* [GitLens](https://marketplace.visualstudio.com/items?itemName=eamodio.gitlens)
* [ShellCheck](https://marketplace.visualstudio.com/items?itemName=timonwong.shellcheck)
* [markdownlint](https://marketplace.visualstudio.com/items?itemName=DavidAnson.vscode-markdownlint)

??? note "shellcheck on Apple Silicon"

    Currently the *shellcheck* extension does not come with a binary for `arm64`.
    Install `shellcheck` via `brew install shellcheck`.

## Documentation

The documentation is deployed to [https://opalmedapps.gitlab.io/backend-pilot](https://opalmedapps.gitlab.io/backend-pilot). It is deployed automatically when commits are pushed to `main`.

To view the documentation during development, run the following commands in your virtual environment:

1. `pip install -r requirements/docs.txt`
2. `mkdocs serve -a localhost:8001`
3. Open http://localhost:8001

## Development

### Dependencies

See the `requirements/` folder for the requirement files depending on the environment.

#### Update dependencies

The dependencies are kept up-to-date by using [Renovate Bot](https://www.whitesourcesoftware.com/free-developer-tools/renovate/). See the file `renovate.json` for its configuration.

However, you can also manually update dependencies:

1. Install [`pip-upgrader`](https://github.com/simion/pip-upgrader): `pip install pip-upgrader`
2. Run `pip-upgrade` to see new available versions and update the desired dependencies
3. Run linting, type checking and tests with coverage (see below) to ensure that everything still works as expected
4. Commit the updates to the requirements file(s)

### Linting, Testing, Coverage

The configuration (such as which files to exclude) is located in `setup.cfg` and `pytest.ini`. The following commands can all be executed from the project root.

1. Linting with `flake8`: Execute `flake8`
1. Static type checking with `mypy`: Execute `mypy`
1. Execute tests with `pytest`: Execute `pytest`
1. Execute coverage with `coverage`:
    1. Execute tests with coverage: `coverage run -m pytest`
    1. Reporting: `coverage report`
    1. Get HTML report (optional): `coverage html`, then `open htmlcov/index.html` to open the report in the browser
    1. Erase old coverage data: `coverage erase`

`vscode` should pick up the virtual environment and run `flake8` and `mypy` while writing code.
