# Translation

This project utilizes Django's native internationalization hooks called translation strings. For more information see the [Django's Translation Documentation](https://docs.djangoproject.com/en/4.0/topics/i18n/translation/).

To specify a translation string in Python code, use **gettext()** function. For example,

```python
from django.utils.translation import gettext as _

test_variable = _("My test translation string.")
```

To specify a translation string in a template code, include `{% load i18n %}` toward the top of the template. This will provide access to the **translate** and **blocktranslate** template tags. For example,

```html
{% extends "layouts/base.html" %}
{% load static %}
{% load i18n %}

<h1>
    {% translate "First translation string."}

    {% blocktranslate with param="test parameter"%}Second translation string with {{ param }}.{% endblocktranslate %}
</h1>
```

!!! note

    You can provide additional context which is especially helpful if a word can have several meanings in another language. See the [documentation on contextual markers](https://docs.djangoproject.com/en/dev/topics/i18n/translation/#contextual-markers-1) for more information.

To create or update a message file that keeps all the translations, run this command:

```sh
django-admin makemessages --add-location file -l fr
```

where **fr** is the locale name for the message file you want to create. Note that for a new app you need to first create the `locale` directory within the app directory. Otherwise the translations will be added to the project's translation file.

!!! important

    If translation strings were removed they will only be commented out in the `.po` file. Delete them if they are not needed anymore. Also pay attention to fuzzy strings. This happens when translations are inferred from previously translated strings. Verify them and adjust as necessary. By default, fuzzy entries are not processed by **compilemessages**.

Once you have filled in or updated the message file, it must be compiled. Run the following command to compile a new binary file:

```sh
django-admin compilemessages
```
