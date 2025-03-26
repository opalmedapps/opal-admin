from django.contrib.admin.sites import AdminSite
from django.http import HttpRequest

import pytest

from opal.users.models import User

from .. import factories
from ..admin import InstitutionAdmin
from ..models import Institution

pytestmark = pytest.mark.django_db
site = AdminSite()


def test_institutionadmin_can_add(admin_user: User) -> None:
    """A new institution can be added if there is no institution yet."""
    admin = InstitutionAdmin(Institution, site)
    request = HttpRequest()
    request.user = admin_user

    assert admin.has_add_permission(request)


def test_institutionadmin_existing_institution_cannot_add() -> None:
    """No new institution can be added if there is already an institution."""
    factories.Institution()
    admin = InstitutionAdmin(Institution, site)
    request = HttpRequest()

    assert not admin.has_add_permission(request)
