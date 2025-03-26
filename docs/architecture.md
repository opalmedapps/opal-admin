# Architecture

The overall project setup is influenced by [Cookiecutter Django](https://cookiecutter-django.readthedocs.io/en/latest/) as well as the *Two Scoops of Django* book.

The user interface is based on Django templates and views. This allows us to use Django's features, such as form and model validation, authentication, server-side-rendered templates etc., without much extra work. Functionality that is needed to be called from the outside (such as the OIE and requests from the mobile app) are exposed via API endpoints.

!!! note
    If you are unfamiliar with Django please have a look at the [official Django tutorial](https://docs.djangoproject.com/en/stable/intro/tutorial01/) as well as the [Django REST framework tutorial](https://www.django-rest-framework.org/tutorial/1-serialization/).

## Important packages

The following (non-exhaustive) list gives an overview of packages used on top of Django:

* [Django REST Framework](https://www.django-rest-framework.org/) (DRF): API functionality
    * [dj-rest-auth](https://github.com/iMerica/dj-rest-auth): REST API endpoints for authentication
* [Modeltranslation](https://django-modeltranslation.readthedocs.io/en/latest/): Provide the ability to translate model fields. Automatically adds additional fields for each translated field to the model for each language.
* [Django Easy Audit](https://github.com/soynatan/django-easy-audit): Auditing package to log all login, requests and CRUD operations on models. Stores these in the database.
* [Django Crispy Forms](https://github.com/django-crispy-forms/django-crispy-forms): For a simple way to build nice looking templates.
* [Django Filter](https://django-filter.readthedocs.io/en/main/): For filtering querysets via URL parameters.
* [django-tables2](https://django-tables2.readthedocs.io/en/latest/): For a simple way to define tables.

This list only covers an excerpt of the most important packages. Please see the base dependencies in `requirements/base.txt` for the full list.

### Development

* Linting: [flake8](https://flake8.pycqa.org/) with various plugins
* Type checking: [mypy](http://www.mypy-lang.org/)
* Testing: [pytest](https://pytest.org/) with various plugins (and coverage). An important plugin is [pytest-django](https://pytest-django.readthedocs.io/) which provides the integration with Django.
    * [Factory Boy](https://factoryboy.readthedocs.io/): Factories for models to make testing with model test data easier.
* [Pre-Commit](https://pre-commit.com/): To catch problems during commit via pre-commit hooks.

Please see the development dependencies in `requirements/development.txt` for the full list.

### Documentation

Documentation is written in Markdown and generated via [mkdocs](https://www.mkdocs.org/) with the wonderful [mkdocs-material](https://squidfunk.github.io/mkdocs-material/) theme. This theme has a lot of extra features for technical documentation. Please refer to the [README](../#documentation) on how to setup the documentation.

Docstrings in the code are extracted using [mkdocstring](https://mkdocstrings.github.io/) and contained in the same documentation site.

Please see the development dependencies in `requirements/docs.txt` for the full list of plugins.

### Production

This section needs to be completed once the production setup is done.

Please see the development dependencies in `requirements/production.txt` for the full list.

## Project structure

The top-level structure is as follows (some files have been left out for brevity):

```shell
.
├── docker                  # Docker-specific files
├── docs                    # documentation
├── locale                  # project-level translation files
├── opal                    # Django project including all apps
├── requirements            # dependencies per environment
├── .editorconfig           # configuration for the EditorConfig plugin
├── .env.sample             # configurable sample settings
├── .gitlab-ci.yml          # GitLab CI/CD configuration
├── .markdownlint.yml       # Markdown linter configuration
├── .pre-commit-config.yaml # Pre-commit configuration
├── CHANGELOG.md
├── Dockerfile
├── README.md
├── docker-compose.yml
├── manage.py
├── mkdocs.yml              # mkdocs configuration for documentation
├── pytest.ini              # pytest configuration
├── renovate.json5          # Renovate configuration for dependency updates
└── setup.cfg               # development tool configurations
```

The Django project's main content is structured as follows (apps have been left out for brevity):

```shell
opal/
├── core                    # core app for common functionality
│   ├── ...
│   ├── api_urls.py         # the API URL configuration for the complete API
│   └── ...
├── static                  # project-level static files
├── templates               # project-level templates
├── __init__.py
├── asgi.py
├── conftest.py             # project-wide pytest fixtures
├── settings.py             # Django settings
├── urls.py                 # project-level URL configuration
└── wsgi.py
```

[Apps](https://docs.djangoproject.com/en/dev/ref/applications/) provide a way to structure certain functionality. An app should focus on a single aspect of a project. The [App Structure page](apps/structure.md) contains information about how an app is structured.

For more information on app design please see *Two Scoops of Django* Chapter 4.
