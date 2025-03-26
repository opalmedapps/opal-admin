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
        the substring cut off at the right-most separator, empty string if the separator is not present
    """
    return text.rpartition(separator)[0]


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


@register.filter('strip')
@stringfilter
def strip(text: str) -> str:
    """
    Strip whitespace around the given text.

    Args:
        text: the text

    Returns:
        the truncated text
    """
    return text.strip()


@register.filter('striplines')
@stringfilter
def striplines(text: str) -> str:
    """
    Strip whitespaces around each line of the given text.

    Args:
        text: the text

    Returns:
        the replaced text
    """
    # skip empty elements
    # see: https://stackoverflow.com/a/8626817
    return ' '.join(
        line.strip()
        for line in text.splitlines()
        if line.strip()
    )
