"""This module is used to provide configuration, fixtures, and plugins for pytest."""

import pytest
from rest_framework.test import APIClient


@pytest.fixture()
def api_client() -> APIClient:
    """Fixture providing an instance of Django REST framework's ``APIClient``."""
    return APIClient()
