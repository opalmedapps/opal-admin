"""Command for Users migration."""
from enum import Enum
from typing import Any

from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand

from opal.legacy.models import LegacyModule, LegacyOARole, LegacyOARoleModule, LegacyOAUser
from opal.users.models import ClinicalStaff


class Access(Enum):
    """An enumeration of supported access rights."""

    # Legacy has 0-7 access privileges, I only added write with an assumption it is '3'
    WRITE = 3  # noqa: WPS115
    READ = 0  # noqa: WPS115


class Command(BaseCommand):
    """Command to migrate users from legacy DB to the new backend users."""

    help = 'migrate OAUsers from legacy DB to the new backend'  # noqa: A003

    def handle(self, *args: Any, **kwargs: Any) -> None:  # noqa: WPS210
        """
        Handle migrate OAUsers legacy DB to the new backend printout number of users imported.

        Return 'None'.

        Args:
            args: non-keyword input arguments.
            kwargs:  variable keyword input arguments.
        """
        patient_module = LegacyModule.objects.get(name_en='Patient')
        admin_role = LegacyOARole.objects.get(name_en='Administration')
        admin_group = Group.objects.get(name='System Administrators')
        registrant_group = Group.objects.get(name='Registrants')
        admin_users_counter = 0
        all_users_counter = 0
        staff_users_counter = 0

        for legacy_user in LegacyOAUser.objects.all():
            if legacy_user.oaroleid == admin_role:

                clinical_staff_user = ClinicalStaff(
                    username=legacy_user.username,
                    is_staff=True,
                    is_superuser=True,
                    language=legacy_user.language.lower(),
                    date_joined=legacy_user.date_added,
                )

                if self._save_clinical_staff_user(clinical_staff_user):
                    admin_group.user_set.add(clinical_staff_user)
                    admin_users_counter += 1
                    all_users_counter += 1
            else:
                role_module = LegacyOARoleModule.objects.filter(
                    oaroleid=legacy_user.oaroleid,
                    moduleid=patient_module,
                    access=Access.WRITE.value,
                )

                clinical_staff_user = ClinicalStaff(
                    username=legacy_user.username,
                    language=legacy_user.language.lower(),
                    date_joined=legacy_user.date_added,
                )

                if self._save_clinical_staff_user(clinical_staff_user):
                    # access codes 0-7
                    if role_module:
                        registrant_group.user_set.add(clinical_staff_user)  # noqa: WPS220
                        staff_users_counter += 1

                    all_users_counter += 1
        self.stdout.write('Total migrated users: {total} of which {admins} Admins and {staff} Registrants.'.format(
            total=all_users_counter,
            admins=admin_users_counter,
            staff=staff_users_counter,
        ),
        )

    def _save_clinical_staff_user(self, clinical_staff_user: ClinicalStaff) -> bool:
        """
        Save ClinicalStaff User in Users model.

        Args:
            clinical_staff_user: user object of type clinical staff

        Returns:
            True if user is added, False otherwise.
        """
        clinical_staff_user.set_unusable_password()

        try:
            clinical_staff_user.full_clean()

        except ValidationError as exception:
            self.stderr.write(
                'Error: {msg} when saving username: {username}'.format(
                    msg=exception,
                    username=clinical_staff_user.username,
                ),
            )
            return False

        clinical_staff_user.save()
        return True
