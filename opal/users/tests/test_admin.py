from django.contrib.admin.sites import AdminSite

from ..admin import UserAdmin
from ..models import User

site = AdminSite()


def test_useradmin_extra_fieldsets() -> None:
    """The custom user model fields are added to the UserAdmin's fieldsets."""
    admin = UserAdmin(User, site)

    last_fieldset = admin.fieldsets[-1]

    expected_fields = ('type', 'language', 'phone_number')
    actual_fields = last_fieldset[1]['fields']

    assert 'Extra' in last_fieldset
    assert actual_fields == expected_fields
