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

For more details please refer to *Two Scoops of Django* Section 4.4.

## Creating a new app

For new apps ensure to do the following things:

* define the proper name and verbose_name in `apps.py`
* add the app name to the urls module in `urls.py` (e.g., `app_name = 'hospital_settings'`) to ensure that it can be included in the root URL configuration and has a proper namespace
* create a `locale` sub-directory where translation files should be generated to

## API

For apps that expose an API, create a sub-package `api` where serializers, views and viewsets should live.

API URLs are defined in a module in the core app (`core/api_urls.py`).

## Best Practices

* favour fat models and skinny views, i.e., logic should go into the model, model manager or utility modules instead of the view for reusability. See more information in Two Scoops of Django's preface "Core Concepts: Fat Models, Utility Modules, Thin Views, Stupid Templates".
