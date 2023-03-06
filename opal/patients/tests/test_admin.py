from django.contrib.admin.sites import AdminSite
from django.http import HttpRequest
from django.test import RequestFactory
from django.urls import reverse

import pytest

from opal.patients.admin import RelationshipTypeAdmin
from opal.users.models import User

from .. import factories, models

pytestmark = pytest.mark.django_db

site = AdminSite()


@pytest.mark.parametrize('role_type', models.PREDEFINED_ROLE_TYPES)
def test_relationshiptype_admin_has_delete_permission_false(role_type: models.RoleType) -> None:
    """Ensure a user cannot delete a restricted permission from the admin portal."""
    relationship_type = models.RelationshipType.objects.get(role_type=role_type)
    admin = RelationshipTypeAdmin(models.RelationshipType, site)
    request = HttpRequest()

    assert not admin.has_delete_permission(request=request, obj=relationship_type)


def test_relationshiptype_admin_has_delete_permission_true(admin_user: User) -> None:
    """Ensure a user can delete a regular permission from the admin portal."""
    admin = RelationshipTypeAdmin(models.RelationshipType, site)
    relationship_type = factories.RelationshipType(role_type=models.RoleType.CAREGIVER)

    request = RequestFactory().post(reverse(
        'admin:patients_relationshiptype_delete',
        kwargs={'object_id': relationship_type.pk},
    ))
    request.user = admin_user

    assert admin.has_delete_permission(request=request, obj=relationship_type)


def test_relationshiptype_admin_has_delete_permission_obj_none_false(admin_user: User) -> None:
    """Ensure admin portal deletion privileges evaluate correctly for nonetype object."""
    admin = RelationshipTypeAdmin(models.RelationshipType, site)
    request = RequestFactory().post(reverse('admin:patients_relationshiptype_changelist'))
    request.user = admin_user

    assert admin.has_delete_permission(request=request, obj=None)
