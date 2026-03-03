# SPDX-FileCopyrightText: Copyright (C) 2022 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Module providing admin functionality for the users app."""

from typing import TYPE_CHECKING, override

from django.contrib import admin

if TYPE_CHECKING:
    from django.contrib.admin.options import _FieldOpts  # noqa: PLC2701
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.models import User as DjangoUser
from django.http import HttpRequest
from django.utils.translation import gettext_lazy as _

from django_stubs_ext import StrPromise

from .models import Caregiver, ClinicalStaff, User

# see: https://github.com/typeddjango/django-stubs/issues/1960
type Fieldsets = (
    list[tuple[str | StrPromise | None, _FieldOpts]]
    | tuple[tuple[str | StrPromise | None, _FieldOpts], ...]
    | tuple[()]
)


# use Django's default UserAdmin for now for all types of caregivers (until the User is actually customized)
@admin.register(User, Caregiver, ClinicalStaff)
class UserAdmin(DjangoUserAdmin[DjangoUser]):
    """Custom user admin that builds on Django's `UserAdmin` and adds the additional `User` fields to the fieldsets."""

    extra_fieldsets: Fieldsets = ((_('Extra'), {'fields': ('type', 'language', 'phone_number')}),)

    @override
    def get_fieldsets(self, request: HttpRequest, obj: DjangoUser | None = None) -> Fieldsets:
        fieldsets = super().get_fieldsets(request, obj)

        # add our additional custom fields to the default fieldsets
        return (
            *fieldsets,
            *self.extra_fieldsets,
        )
