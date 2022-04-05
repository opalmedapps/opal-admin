"""
Module providing models for the users app.

Provides a custom user model based on Django's [django.contrib.auth.models.AbstractUser][].
For more information see the [Django documentation on customizing the user model](https://docs.djangoproject.com/en/dev/topics/auth/customizing/#using-a-custom-user-model-when-starting-a-project)
"""  # noqa: E501
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """Default custom user model."""

    pass  # noqa: WPS420, WPS604
