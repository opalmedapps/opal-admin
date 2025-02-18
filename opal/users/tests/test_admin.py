# SPDX-FileCopyrightText: Copyright (C) 2022 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import User as DjangoUser

from ..admin import UserAdmin

site = AdminSite()


def test_useradmin_extra_fieldsets() -> None:
    """The custom user model fields are added to the UserAdmin's fieldsets."""
    admin = UserAdmin(DjangoUser, site)

    assert admin.fieldsets is not None
    last_fieldset = admin.fieldsets[-1]

    expected_fields = ('type', 'language', 'phone_number')
    actual_fields = last_fieldset[1]['fields']

    assert 'Extra' in last_fieldset
    assert actual_fields == expected_fields
