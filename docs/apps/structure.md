# App Structure

Each app should follow the following structure (based on the example of the `hospital_settings` app):

```shell
opal/hospital_settings/
├── api                     # API module
│   ├── __init__.py
│   ├── serializers.py      # DRF serializers
│   ├── views.py            # DRF views
│   └── viewsets.py         # DRF viewsets
├── locale                  # translation files
├── management              # management commands
├── migrations              # DB migrations
├── static
│   └── hospital_settings   # app-specific static files
├── templates
│   └── hospital_settings   # app-specific template files
├── tests                   # test files
│   ├── __init__.py         #
│   └── ...                 # also contains API tests (prefix file with test_drf_ instead of test_)
├── __init__.py
├── admin.py                # admin sites
├── apps.py                 # app config
├── conftest.py             # app-specific pytest fixtures
├── constants.py            # app-specific constants
├── factories.py            # factory-boy model factories
├── forms.py
├── models.py
├── tables.py               # table definitions
├── translation.py          # translation options for models
├── urls.py                 # app-specific URLs (with relative paths)
└── views.py
```

!!! note
    The app-specific static and template files are used alongside the ones from the root project folder (`opal/`).

For more details please refer to *Two Scoops of Django* Section 4.4.

## Creating a new app

Execute the following commands to create a new app (here based on an example `foo` app). You can also find more details in the [official Django tutorial](https://docs.djangoproject.com/en/4.0/intro/tutorial01/#creating-the-polls-app).

```sh
mkdir opal/foo/
python manage.py startapp foo "opal/foo/"
```

For new apps ensure to do the following things:

* define the proper name and verbose_name in `apps.py`
    * the name should be prefixed with `opal.` (for our example it would be `opal.foo`)
    * if the plural of the `verbose_name` is not that name suffixed with `s`, define `verbose_name_plural` as well
* add the app name to the urls module in `urls.py` (e.g., `app_name = 'hospital_settings'`) to ensure that it can be included in the root URL configuration and has a proper namespace
* add the app to the `LOCAL_APPS` list in `opal/settings.py`
* delete the `tests.py` file and create a `tests` directory with an empty `__init__.py` file
* create a `locale` sub-directory where translation files should be generated to

## API

For apps that expose an API, create a sub-package `api` where serializers, views and viewsets should live.

API URLs are defined in a module in the core app (`core/api_urls.py`).

## Best Practices

* favour fat models and skinny views, i.e., logic should go into the model, model manager or utility modules instead of the view for reusability. See more information in Two Scoops of Django's preface "Core Concepts: Fat Models, Utility Modules, Thin Views, Stupid Templates".
