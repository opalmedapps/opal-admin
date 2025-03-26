# Opal Backend

[![pipeline status](https://gitlab.com/opalmedapps/backend/badges/main/pipeline.svg)](https://gitlab.com/opalmedapps/backend/-/commits/main) [![coverage report](https://gitlab.com/opalmedapps/backend/badges/main/coverage.svg)](https://gitlab.com/opalmedapps/backend/-/commits/main) [![wemake-python-styleguide](https://img.shields.io/badge/code%20style-wemake-000000.svg)](https://github.com/wemake-services/wemake-python-styleguide) [![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit) [![Docs](https://img.shields.io/badge/documentation-available-brightgreen.svg)](https://opalmedapps.gitlab.io/backend)

## Requirements

This project has the following requirements to be available on your system:

* [Docker Desktop](https://docs.docker.com/desktop/) (or Docker Engine on Linux)
* Python 3.11
* [Git LFS](https://git-lfs.com/)

## Getting Started

After cloning this repo, follow the below steps to get started.

### Configuration

All configuration is stored within the `.env` file to follow the [12factor app methodology](https://12factor.net/config) on storing config in the environment. This means that any setting that depends on the environment the app is run in should be exposed via the `.env`.

Copy the `.env.sample` to `.env` and adjust the values as necessary. You need to at least modify `DATABASE_PASSWORD` and `SECRET_KEY`.

These configuration parameters are read by `docker compose` and by `settings.py` (via [`django-environ`](https://github.com/joke2k/django-environ)).

!!! note
    The legacy database is currently provided by the [`db-docker`](https://gitlab.com/opalmedapps/db-docker/). For information on the legacy database, please see the [Legacy DB Connection](database/legacy_db.md) page.
    Make sure the configuration of the legacy database in your `.env` file matches the value of the one in your `db-docker` setup.

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

    ```sh
    python3.11 -m venv --prompt 'opal' .venv
    source .venv/bin/activate
    ```

=== "Windows"

    ```sh
    python -m venv --prompt 'opal' .venv
    .\.venv\Scripts\activate
    ```

    **Note:**  If activate fails with a security error, run this command to allow local scripts to execute (see [this Stack Overflow discussion](https://stackoverflow.com/q/4037939) for more information): `powershell Set-ExecutionPolicy RemoteSigned -Scope CurrentUser`

??? note "IDE: auto-activate the virtual environment"

    Your IDE can be configured to automatically activate the virtual environment when launching a new terminal.

    === "VSCode"

        VSCode has already been configured with this feature in its project settings.
        This was done by adding the following line to `.vscode/settings.json`:

        ```json
        "python.terminal.activateEnvironment": true,
        ```

    === "PyCharm"

        Navigate to `File > Settings/Preferences > Tools > Terminal` and replace `Shell path` with the following:

        === "Windows"
            ```sh
            powershell -NoExit -File ".\.venv\Scripts\Activate.ps1"
            ```

        If you later encounter any issues with your virtual environment that are causing the terminal to crash on launch,
        simply reset the above field to its default value, fix your virtual environment, and then reset the field back to the value above.

#### Configure your IDE's Python Interpreter

Your IDE should be set up to use the Python interpreter in your virtual environment. This will ensure that your code
is interpreted correctly while developing. The following instructions will help you to check whether your interpreter is
correctly set, and if not, to set it to the correct path.

The steps below refer to an interpreter path, which is the following (depending on your OS):

=== "macOS/Linux"

    ```
    .venv/bin/python
    ```

=== "Windows"

    ```
    .venv\Scripts\python.exe
    ```

---

=== "VSCode"

    1. Make sure that your project folder is open, and open any `.py` file.
    2. In the bottom-right corner of the screen, next to `Python`, you should see your Python version,
       followed by .venv, for example: `3.10.9 ('.venv':venv)`.
    3. If you don't see this, click on the version number or empty field next to `Python`.
    4. Select or browse to the interpreter path above.

=== "PyCharm"

    1. Go to `File > Settings/Preferences > Project: name > Project Interpreter`.
    2. Check whether the value for `Python interpreter` is already set to the interpreter from your virtual environment (`.venv`).
    3. If it isn't, click on the gear icon, click "Add", select the option for adding an existing Virtualenv environment,
       and in the interpreter box, browse to the interpreter path above.

#### Install dependencies

Run the following commands within the virtual environment:

```sh
python -m pip install --upgrade pip
python -m pip install -r requirements/development.txt
```

??? tip "Installing `mysqlclient` fails"

    In case installing the `mysqlclient` package does not provide a binary for your platform it needs to be built. To do so, the mysql client library needs to be installed on the system.

    === "macOS"
        The easiest is to install it via Homebrew:

        ```sh
        brew install mysql-client
        export PATH="/opt/homebrew/opt/mysql-client/bin:$PATH"
        brew install pkg-config
        export PKG_CONFIG_PATH="/opt/homebrew/opt/mysql-client/lib/pkgconfig"
        # install dependencies via pip install
        ```

    === "Windows"
        No detailed steps known. Try to follow the [instructions](https://github.com/PyMySQL/mysqlclient#windows) provided by the `mysqlclient` package.

### Migrate Database and Create Superuser

Before you can start, you need to migrate the database and create a superuser. Ensure at least the database container is running. Execute the following commands either in the virtual environment or in the `app` container.

```sh
python manage.py migrate
python manage.py createsuperuser
```

!!! note

The superuser is an admin user you'll create and can use during local development to have access to every part of the backend on your machine. We don't have access to this type of account in production environments, for security, but on your local machine it's fine to have easy access to everything. Whenever you reset the data in your database, the superuser will be reset also, and you'll need to recreate it.

Once this is done, you can go to [http://localhost:8000](http://localhost:8000) to access the frontend. Go to [http://localhost:8000/admin](http://localhost:8000/admin) to log in to the Django admin site with the superuser you created. [http://localhost:8000/api](http://localhost:8000/api) shows the available REST API endpoints to you.

### Pre-commit

This project contains a configuration for [`pre-commit`](https://pre-commit.com/) (see `.pre-commit-config.yaml`).

Install the `pre-commit` hooks via `pre-commit install`.

??? note "Using pre-commit with a git GUI"

    If you are using a git GUI tool (such as Sourcetree) the path might not be set up correctly and pre-commit might not be able to find `flake8` and `mypy`.

    The current known workaround is to specify the required `PATH` for the `pre-commit` hook. Add the following line at the top of `.git/hooks/pre-commit` (after the first line with the bash interpreter):

    ```export PATH=$PATH:"/C/Users/path/to/.venv/Scripts/"```

### Recommended IDE Extensions

=== "VSCode"

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

=== "PyCharm"

    This project recommends the installation of some PyCharm extensions. These can be installed under `File > Settings/Preferences > Plugins`.

    The following extensions are required or strongly recommended:

    * [EditorConfig by JetBrains s.r.o.](https://plugins.jetbrains.com/plugin/7294-editorconfig) (should come pre-bundled with PyCharm)
    * [Docker by Jetbrains s.r.o.](https://plugins.jetbrains.com/plugin/7724-docker)
    * [Markdown by Jetbrains s.r.o.](https://plugins.jetbrains.com/plugin/7793-markdown)

## Documentation

The documentation is deployed to [https://opalmedapps.gitlab.io/backend](https://opalmedapps.gitlab.io/backend). It is deployed automatically when commits are pushed to `main`.

To view the documentation during development, run the following commands in your virtual environment:

=== "macOS/Linux"

    ```sh
    pip install -r requirements/docs.txt
    mkdocs serve -a localhost:8001
    ```

=== "Windows"

    ```sh
    pip install -r requirements/docs.txt
    python -m mkdocs serve -a localhost:8001
    ```

    For more details on why the command on Windows is prefixed with `python -m`, see the [mkdocs installation notes](https://www.mkdocs.org/user-guide/installation/).

Then open http://localhost:8001 to view the generated documentation site.

## Development

### Dependencies

See the `requirements/` folder for the requirement files depending on the environment.

#### Update dependencies

The dependencies are kept up-to-date by using [Renovate Bot](https://www.whitesourcesoftware.com/free-developer-tools/renovate/). See the file `renovate.json5` for its configuration.

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
    cp docker-compose.ssl.yml docker-compose.override.yml
    ```

    You can verify that it is applied by running `docker compose config`.

    **Note:** [Windows users may have to re-save the `ssl.cnf` as 'read-only'](https://stackoverflow.com/a/51854668) for Docker to actually use the configs listed there.
