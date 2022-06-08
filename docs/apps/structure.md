# Creating a new app

For new apps ensure to do the following things:

* define the proper name and verbose_name in `apps.py`
* add the app name to the urls module in `urls.py` (e.g., `app_name = 'patients'`) to ensure that it can be included in the root URL configuration and has a proper namespace
* create a `locale` sub-directory where translation files should be generated to

## API

For apps that expose an API, create a sub-package `api` where serializers, views and viewsets should live.

API URLs are defined in a module in the core app (`core/api_urls.py`).
