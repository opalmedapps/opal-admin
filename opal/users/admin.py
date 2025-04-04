# SPDX-FileCopyrightText: Copyright (C) 2022 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Module providing admin functionality for the users app."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.models import User as DjangoUser
from django.utils.translation import gettext_lazy as _

from .models import Caregiver, ClinicalStaff, User


# use Django's default UserAdmin for now for all types of caregivers (until the User is actually customized)
@admin.register(User, Caregiver, ClinicalStaff)
class UserAdmin(DjangoUserAdmin[DjangoUser]):
    """Custom user admin that builds on Django's `UserAdmin` and adds the additional `User` fields to the fieldsets."""

    def __init__(self, model: type[DjangoUser], admin_site: admin.AdminSite) -> None:
        """Create admin and add extra fieldsets and list_displays."""
        super().__init__(model, admin_site)

        # add our additional custom fields to the default fieldset
        new_fieldsets = list(self.fieldsets) if self.fieldsets else []
        new_fieldsets.append((_('Extra'), {'fields': ('type', 'language', 'phone_number')}))

        self.fieldsets = tuple(new_fieldsets)
