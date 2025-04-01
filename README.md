<!--
SPDX-FileCopyrightText: Copyright (C) 2021 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>

SPDX-License-Identifier: AGPL-3.0-or-later
-->

# Opal Admin

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![ci](https://github.com/opalmedapps/opal-admin/actions/workflows/ci.yml/badge.svg)](https://github.com/opalmedapps/opal-admin/actions/workflows/ci.yml)
[![ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)

## Requirements

This project has the following requirements to be available on your system:

* [uv](https://docs.astral.sh/uv/) for Python project management
* [Docker Desktop](https://docs.docker.com/desktop/) (or Docker Engine on Linux)
* [Git LFS](https://git-lfs.com/)
* Legacy Databases set up and its DB server running: https://github.com/opalmedapps/opal-db-management
* macOS/Linux only: Have `mysql-client` and `pkg-config` installed to build the `mysqlclient` package: https://github.com/PyMySQL/mysqlclient#install

## Getting Started

After cloning this repo, follow the below steps to get started.

### Configuration

All configuration is stored within the `.env` file to follow the [12factor app methodology](https://12factor.net/config) on storing config in the environment.
This means that any setting that depends on the environment the app is run in should be exposed via the `.env`.

Copy the `.env.sample` to `.env` and adjust the values as necessary.

```shell
cp .env.sample .env
```

You need to at least generate and add `SECRET_KEY`.
However, we also recommend to change the `DATABASE_PASSWORD`.

These configuration parameters are read by `docker compose` and by the settings in `config/settings/`, such as `base.py` (via [`django-environ`](https://github.com/joke2k/django-environ)).

> [!NOTE]
> The legacy database is currently provided by the [`db-docker`](https://github.com/opalmedapps/opal-db-management/).
> For information on the legacy database connections, please see the [Legacy DB Connection](database/legacy_db.md) page.
> Make sure the configuration of the legacy database connection in your `.env` file matches the values of the one in your `db-management` setup.

### Docker

This project comes with a `compose.yaml` file providing you with a MariaDB and the app in their respective containers.
The Django app is built with a custom image (defined in `Dockerfile`).

First, start up the DB container:

```shell
docker compose up -d db
```

You can run the app in the foreground:

```shell
docker compose up app
```

To connect to the app container or run specific commands, run

```shell
# shell inside the container
docker compose exec app sh
# Django management commands
docker compose exec app python manage.py
```

Instead of running the `app` container you can also run the Django development server directory using `uv`.
See below for details.

### Python virtual environment

In order for linting, type checking, unit testing etc. to be available in your IDE, and for `pre-commit` to use the same configuration, we recommend to set up a local virtual environment.
This also makes it possible to execute management commands directly from the virtual environment without having to execute them within the container.
Otherwise, everything has to be run from inside the container (e.g., by calling `docker compose exec app <command>`).

#### Set up the virtual environment

```shell
uv sync
```

<details>
<summary>Note for Windows Users</summary>

If activate fails with a security error, run this command to allow local scripts to execute (see [this Stack Overflow discussion](https://stackoverflow.com/q/4037939) for more information):

```powershell
powershell Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
```

</details>

> [!NOTE] IDE: auto-activate the virtual environment
> Your IDE can be configured to automatically activate the virtual environment when launching a new terminal.
>
> **VSCode** has already been configured with this feature in its project settings.
> This was done by adding the following line to `.vscode/settings.json`:
>
> ```json
> "python.terminal.activateEnvironment": true,
> ```
>
> **PyCharm**: Navigate to `File > Settings/Preferences > Tools > Terminal` and replace `Shell path` with the following:
>
> ```powershell
> powershell -NoExit -File ".\.venv\Scripts\Activate.ps1"
> ```
>
> If you later encounter any issues with your virtual environment that are causing the terminal to crash on launch,
> simply reset the above field to its default value, fix your virtual environment, and then reset the field back to the value above.

#### Install dependencies

`uv` already created the virtual environment and installed the dependencies (including development dependencies) for you by executing `uv sync`.

> [!TIP] Installing `mysqlclient` fails
> In case installing the `mysqlclient` package does not provide a binary for your platform it needs to be built.
> To do so, the mysql client library needs to be installed on the system.
>
> **macOS:** The easiest is to install it via Homebrew:
>
> ```shell
> brew install mysql-client pkg-config
> brew install pkg-config
> # export PATH and PKG_CONFIG_PATH according to output from installing mysql-client
> # install dependencies
> ```
>
> Use the output from installing `mysql-client` to update the `PATH` and set the `PKG_CONFIG_PATH` environment variables.
> If you've already installed `mysql-client` you can get this information by executing `brew info mysql-client`.

### Migrate Database and Create Superuser

Before you can start, you need to migrate the database and create a superuser.
Ensure at least the database container is running.
Execute the following commands either in the virtual environment or in the `app` container.

```shell
python manage.py migrate
python manage.py createsuperuser
```

Once this is done, you can go to [http://localhost:8000](http://localhost:8000) to access the frontend.
Go to [http://localhost:8000/admin](http://localhost:8000/admin) to log in to the Django admin site with the superuser you created.
[http://localhost:8000/api](http://localhost:8000/api) shows the available REST API endpoints to you.

### Initializing data

For convenience, we provide two commands to initialize initial and test data.

```shell
python manage.py initialize_data
python manage.py insert_test_data OMI
```

See the command's help for more information.

### Pre-commit

This project contains a configuration for [`pre-commit`](https://pre-commit.com/) (see `.pre-commit-config.yaml`).

Install the `pre-commit` hooks via

```shell
uv run pre-commit install
```

<details>
<summary>Using pre-commit with a git GUI</summary>

If you are using a git GUI tool (such as Sourcetree) the path might not be set up correctly and pre-commit might not be able to find `flake8` and `mypy`.

The current known workaround is to specify the required `PATH` for the `pre-commit` hook. Add the following line at the top of `.git/hooks/pre-commit` (after the first line with the bash interpreter):

```shell
export PATH=$PATH:"/C/Users/path/to/.venv/Scripts/"
```

</details>

### Recommended IDE Extensions

* **VSCode:** This project contains recommendations for vscode extensions (see `.vscode/extensions.json`).
  You should get a popup about this when you open the project.
  These extensions are also highlighted in the extensions list.
    * Note: `shellcheck` on Apple Silicon:
      Currently, the *shellcheck* extension does not come with a binary for `arm64`.
      Install `shellcheck` via `brew install shellcheck`.
* **PyCharm:** We recommend the installation of some PyCharm extensions.
  These can be installed under `File > Settings/Preferences > Plugins`.
  The following extensions are required or strongly recommended:
    * [EditorConfig by JetBrains s.r.o.](https://plugins.jetbrains.com/plugin/7294-editorconfig) (should come pre-bundled with PyCharm)
    * [Docker by Jetbrains s.r.o.](https://plugins.jetbrains.com/plugin/7724-docker)
    * [Markdown by Jetbrains s.r.o.](https://plugins.jetbrains.com/plugin/7793-markdown)

## Documentation

The documentation is located in `docs/`.
It is currently not deployed automatically.

To view the documentation during development, run the following commands in your virtual environment:

```shell
uv sync --group docs
uv run mkdocs serve -a localhost:8001
```

Then open http://localhost:8001 to view the generated documentation site.

## Development

### Dependencies

See `pyproject.toml` for the dependencies of this project.

#### Update dependencies

The dependencies are kept up-to-date by using [Renovate Bot](https://docs.renovatebot.com).
See the file `renovate.json5` for its configuration.

However, you can also manually update dependencies using `uv` (see its [documentation](https://docs.astral.sh/uv/guides/projects/#managing-dependencies)).

### Linting, Testing, Coverage

The configuration (such as which files to exclude) is located in `ruff.toml`, `mypy.ini`, and `pytest.ini`.
The following commands can all be executed from the project root.

1. Linting with `ruff`: https://docs.astral.sh/ruff/linter/#ruff-check

    ```shell
    uv run ruff check
    ```

2. Formatting with `ruff`: https://docs.astral.sh/ruff/formatter/

    ```shell
    uv run ruff format
    ```

3. Static type checking with `mypy`:

    ```shell
    uv run mypy opal/
    ```

4. Execute tests with `pytest`:

    ```shell
    uv run pytest
    ```

5. Execute coverage with `coverage`:

    ```shell
    # run tests with coverage
    uv run coverage run -m pytest
    # get the coverage report
    uv run coverage report
    # or get the html report
    uv run coverage html
    open htmlcov/index.html
    # erase old coverage data
    uv run coverage erase
    ```

`vscode` should pick up the virtual environment and run `flake8` and `mypy` while writing code.

## Contributing

### Commit Message Format

*This specification is inspired by [Angular commit message format](https://github.com/angular/angular/blob/master/CONTRIBUTING.md#-commit-message-format)*.

We have very precise rules over how our Git commit messages must be formatted. It is based on the [Conventional Commits specification](https://www.conventionalcommits.org/en/v1.0.0/) which has the following advantages (non-exhaustive list):

* communicates the nature of changes to others
* allows a tool to automatically determine a version bump
* allows a tool to automatically generate the CHANGELOG

Each commit message consists of a **header**, a **body**, and a **footer**.

#### Commit Message Header

```text
<type>(<scope>): <short summary>
  │       │             │
  │       │             └─⫸ Summary in present tense. Not capitalized. No period at the end.
  │       │
  │       └─⫸ Commit Scope: deps|i18n
  │
  └─⫸ Commit Type: build|chore|ci|docs|feat|fix|perf|refactor|style|test
```

The `<type>` and `<summary>` fields are mandatory, the `(<scope>)` field is optional.

**Breaking Changes** must append a `!` after the type/scope.

##### Summary

Use the summary field to provide a succinct description of the change:

* use the imperative, present tense: "change" not "changed" nor "changes"
* don't capitalize the first letter
* no dot (.) at the end

##### Type

Must be one of the following:

* **build**: Changes that affect the build system or external dependencies (i.e., pip, Docker)
* **chore**: Other changes that don't modify source or test files (e.g., a grunt task)
* **ci**: Changes to our CI configuration files and scripts (i.e., GitLab CI)
* **docs**: Documentation only changes
* **feat**: A new feature
* **fix**: A bug fix
* **perf**: A code change that improves performance
* **refactor**: A code change that neither fixes a bug nor adds a feature
* **style**: Changes that do not affect the meaning of the code (whitespace, formatting etc.)
* **test**: Adding missing tests or correcting existing tests

##### Scope

The (optional) scope provides additional contextual information.

The following is the list of supported scopes:

* **deps**: Changes to the dependencies
* **i18n**: Changes to the translations (i18n)

#### Breaking Changes

In addition to appending a `!` after the type/scope in the commit message header, a breaking change must also be described in more detail in the commit message body prefixed with `BREAKING CHANGE:` (see [specification](https://www.conventionalcommits.org/en/v1.0.0/#commit-message-with-both--and-breaking-change-footer)).

## Using the container image

A container image is built and pushed to the container registry of this repository in the pipeline.
It is recommended to not use the `latest` tag but a specific version or commit for reproducible purposes.

The `.env` file needs to be volume mapped into the container.

If the network uses a custom certificate that is not trusted by default, the environment variable `REQUESTS_CA_BUNDLE` can be set with the path to the `ca-certificates.crt` file.

For example:

```yaml
services:
  app:
    image: registry.gitlab.com/opalmedapps/backend:<commit>
    environment:
      - REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
    command: python manage.py runserver 0:8000
    volumes:
      - path/to/ca-certificates.crt:/etc/ssl/certs/ca-certificates.crt
      - $PWD/.env:.env
```

### Running management commands periodically

The following management commands need to be run periodically (e.g., as a cronjob):

* `find_deviations` (once per day): to detect deviations with data stored in the legacy database for patients and caregivers
* `find_questionnaire_respondent_deviations` (once per day): to detect deviations for questionnaire respondents in the legacy questionnaire database
* `expire_relationships` (once per day after midnight): to expire relationships where the patient reached the end age of the relationship type
* `expire_outdated_registration_codes` (every hour or more often): to expire unused registration codes
* `update_daily_usage_statistics` (once per day at 5am): to update daily usage statistics for patients and caregivers

## Running the databases with encrypted connections

If a dev chooses they can also run Django backend using SSL/TLS mode to encrypt all database connections and traffic. This requires installing [db-docker](https://gitlab.com/opalmedapps/db-docker) with the SSL/TLS setup and modifying the setup for Django:

1. In the `db-docker` repository, follow the [Running the databases with encrypted connections](https://gitlab.com/opalmedapps/db-docker/-/tree/use-override-for-ssl#running-the-databases-with-encrypted-connections) section to generate self-signed certificates and set the databases in the SSL/TLS mode.

2. In the `db-docker` project, open a bash CLI and navigate to the `certs/` directory. There should be eight files: two certificate authority (CA) certificates (e.g., `ca-key.pem`, `ca.pem`), three database/server certificates (e.g., `server-cert.pem`, `server-key.pem`, `server-req.pem`), and three OpenSSL configuration files (e.g., `openssl-server.cnf`, `openssl-ca.cnf`, and `v3.ext`).

3. Generate the `django-db` (a.k.a., `backend-db`) certificate:

    ```shell
    # Create the server's private key and a certificate request for the CA
    openssl req -config openssl-server.cnf -newkey rsa:4096 -nodes -keyout backend-db-key.pem -out backend-db-req.pem
    # let the CA issue a certificate for the server
    openssl x509 -req -in backend-db-req.pem -days 3600 -CA ca.pem -CAkey ca-key.pem -set_serial 01 -out backend-db-cert.pem -sha256
    ```

4. Check the validity of the certificate (a message like 'certificate OK' should appear.)

    ```shell
    openssl verify -CAfile ca.pem backend-db-cert.pem
    ```

5. Copy the new certificates (`ca.pem`, `backend-db-key.pem`, and `backend-db-cert.pem`) to the `Django-backend` project and place them in the `certs/` folder. The remaining setup steps should be done within this project.

6. To enable SSL/TLS for Django's database connections, in the .env file, set `DATABASE_USE_SSL=True` and fill in the `SSL_CA` variable with the path to the public key of the certificate authority file (e.g., `/app/certs/ca.pem`).

7. Finally, copy the docker compose SSL override file so that it automatically applies when running compose commands:

    ```shell
    cp compose.ssl.yaml compose.override.yaml
    ```

    You can verify that it is applied by running `docker compose config`.

    **Note:** [Windows users may have to re-save the `ssl.cnf` as 'read-only'](https://stackoverflow.com/a/51854668) for Docker to actually use the configs listed there.
