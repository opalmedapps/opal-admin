"""
Module providing extra filters for Django templates.

Import them into your template with:

```jinja2
{% load extra_filters %}
```
"""
from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()


@register.filter('rsubstring')
@stringfilter
def rsubstring(text: str, separator: str) -> str:
    """
    Return the substring cut off at the right-most separator.

    Args:
        text: the input text
        separator: the separator at which to split the text

    Returns:
        the substring cut off at the right-most separator, the same text if the separator is not present
    """
    first, _separator, last = text.rpartition(separator)

    return first if first else last


@register.filter('startswith')
@stringfilter
def startswith(text: str, prefix: str) -> bool:
    """
    Return whether the text starts with a given prefix.

    Args:
        text: the input text
        prefix: the prefix to search for

    Returns:
        True, if the text starts with the expected prefix, False otherwise
    """
    return text.startswith(prefix)
