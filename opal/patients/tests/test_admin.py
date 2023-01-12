from django.contrib.admin.sites import AdminSite
from django.http import HttpRequest

import pytest

from opal.patients.admin import RelationshipTypeAdmin

from .. import factories, models

pytestmark = pytest.mark.django_db

site = AdminSite()


def test_relationshiptype_admin_has_delete_permission_false() -> None:  # noqa: WPS118
    """Ensure a user cannot delete a restricted permission from the admin portal."""
    admin = RelationshipTypeAdmin(models.RelationshipType, site)
    request = HttpRequest()
    request.method = 'POST'
    request.path = '/admin/patients/relationshiptype/'
    request.POST['action'] = 'delete_selected'
    self_relationshiptype = factories.RelationshipType()
    self_relationshiptype.role_type = models.RoleType.SELF

    assert not admin.has_delete_permission(request=request, obj=self_relationshiptype)


def test_relationshiptype_admin_has_delete_permission_true() -> None:  # noqa: WPS118
    """Ensure a user can delete a regular permission from the admin portal."""
    admin = RelationshipTypeAdmin(models.RelationshipType, site)
    request = HttpRequest()
    request.method = 'POST'
    request.path = '/admin/patients/relationshiptype/'
    request.POST['action'] = 'delete_selected'
    caregiver_relationshiptype = factories.RelationshipType()

    assert admin.has_delete_permission(request=request, obj=caregiver_relationshiptype)


def test_relationshiptype_admin_has_delete_permission_obj_none_false() -> None:  # noqa: WPS118
    """Ensure admin portal deletion privileges evaluate correctly for nonetype object."""
    admin = RelationshipTypeAdmin(models.RelationshipType, site)
    request = HttpRequest()
    request.method = 'POST'
    request.path = '/admin/patients/relationshiptype/'
    request.POST['action'] = 'delete_selected'

    assert admin.has_delete_permission(request=request, obj=None)
