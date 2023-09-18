# Legacy DB Connection

During the migration period from the legacy backend to this backend there exists a second database connection in this project. This is to facilitate retrieval of data out of the legacy database(s). It is especially useful for new functionality that does not exist yet.

## Setup

The project has an additional database called `legacy` defined in the project settings (see `config.settings.base`). Configuration is done via `.env` with the environment variables prefixed with `LEGACY_DATABASE_`. Please see the [db-docker](https://gitlab.com/opalmedapps/db-docker/) project for how to run the legacy database.

There exists an app named `legacy` with the purpose of containing all legacy models. Instead of having to specify which database to query, a custom database router ([opal.core.dbrouters.LegacyDbRouter][]) is defined for [automatic database routing](https://docs.djangoproject.com/en/dev/topics/db/multi-db/#automatic-database-routing). This router routes all read and write operations of models in the `legacy` app to the `legacy` database.

## Convention

To make it easier to identify which model is legacy and which is not, all legacy models should be prefixed with `Legacy`. For example, `LegacyPatient`.

Each legacy model needs to not be [managed](https://docs.djangoproject.com/en/dev/ref/models/options/#managed) by Django. I.e., the `managed` property of the model's `Meta` class should be set to `False`.

## Creating legacy models

The easiest way to create models is to use the `inspectdb` management command. The [Django documentation](https://docs.djangoproject.com/en/dev/howto/legacy-databases/#auto-generate-the-models) shows a brief example on how models can be auto-generated for an existing table.

Use the following command to generate a model definition for a legacy table: `python manage.py inspectdb --database legacy <tableName>`

!!! important
    Always check the generated model and make adjustments as necessary. This also applies to the field attribute names.

## Testing

Django does not create tables for unmanaged models in the test database. To overcome this and facilitate easier testing, a [pytest fixture](https://docs.pytest.org/en/stable/explanation/fixtures.html) (see module [opal.conftest][]) changes `managed` to `True` for all unmanaged models. Django will then also create tables in the test database when running the tests.

## Resources

* https://www.caktusgroup.com/blog/2010/09/24/simplifying-the-testing-of-unmanaged-database-models-in-django/
* https://hannylicious.com/blog/testing-django/
* https://stackoverflow.com/questions/53289057/how-to-run-django-test-when-managed-false
* https://stackoverflow.com/questions/3519143/django-how-to-specify-a-database-for-a-model
