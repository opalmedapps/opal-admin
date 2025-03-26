"""Module providing admin functionality for the users app."""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.models import User as DjangoUser
from django.utils.translation import gettext_lazy as _

from .models import Caregiver, ClinicalStaff, User


class UserAdmin(DjangoUserAdmin):
    """Custom user admin that builds on Django's `UserAdmin` and adds the additional `User` fields to the fieldsets."""

    def __init__(self, model: type[DjangoUser], admin_site: admin.AdminSite) -> None:
        """Create admin and add extra fieldsets and list_displays."""  # noqa: DAR101
        super().__init__(model, admin_site)

        # add our additional custom fields to the default fieldset
        new_fieldsets = list(self.fieldsets) if self.fieldsets else []
        new_fieldsets.append((_('Extra'), {'fields': ('type', 'language', 'phone_number')}))

        self.fieldsets = tuple(new_fieldsets)


# use Django's default UserAdmin for now (until the User is actually customized)
admin.site.register(User, UserAdmin)
admin.site.register(Caregiver, UserAdmin)
admin.site.register(ClinicalStaff, UserAdmin)
