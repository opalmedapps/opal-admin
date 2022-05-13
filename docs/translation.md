# Translation

This project utilizes Django's native internationalization hooks called translation strings. For more information see the [Django's Translation Documentation](https://docs.djangoproject.com/en/4.0/topics/i18n/translation/).

To specify a translation string in Python code, use **gettext()** function. For example,

```python
from django.utils.translation import gettext as _

test_variable = _("My test translation string.")
```

To specify a translation string in a template code, include **{% load i18n %}** toward the top of the template. This will provide access to the **translate** and **blocktranslate** template tags. For example,

```html
{% extends "layouts/base.html" %}
{% load static %}
{% load i18n %}

<h1>
    {% translate "First translation string."}

    {% blocktranslate with param="test parameter"%}Second translation string with {{ param }}.{% endblocktranslate %}
</h1>
```

To create or update a message file that keeps all the translations, run this command:

```sh
django-admin makemessages --add-location file -l fr
```

where **fr** is the locale name for the message file you want to create.

Once you have filled in or updated the message file, it must be compiled. Run the following command to compile a new binary file:

```sh
django-admin compilemessages
```

**makemessages** sometimes generates translation entries marked as fuzzy, e.g. when translations are inferred from previously translated strings. By default, fuzzy entries are not processed by **compilemessages**.
