"""Command for Users migration."""
from enum import Enum
from typing import Any

from django.conf import settings
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand

from opal.legacy.models import LegacyModule, LegacyOARole, LegacyOARoleModule, LegacyOAUser
from opal.users.models import ClinicalStaff


class Access(Enum):
    """An enumeration of supported access rights."""

    # Legacy has 0-7 access privileges
    READ = 1
    READ_WRITE = 3
    READ_WRITE_DELETE = 7


class Command(BaseCommand):
    """Command to migrate users from legacy DB to the new backend users."""

    help = 'migrate OAUsers from legacy DB to the new backend'  # noqa: A003

    def handle(self, *args: Any, **kwargs: Any) -> None:
        """
        Handle migrate OAUsers legacy DB to the new backend.

        Print out number of users imported after completion.

        Args:
            args: non-keyword input arguments.
            kwargs:  variable keyword input arguments.
        """
        patient_module = LegacyModule.objects.get(name_en='Patients')
        admin_role = LegacyOARole.objects.get(name_en='System Administrator')

        admin_group = Group.objects.get(name=settings.ADMIN_GROUP_NAME)
        registrant_group = Group.objects.get(name=settings.REGISTRANTS_GROUP_NAME)

        admin_users_counter = 0
        all_users_counter = 0
        staff_users_counter = 0

        legacy_users = LegacyOAUser.objects.exclude(is_deleted=True)
        for legacy_user in legacy_users:
            # create a clinicalstaff user
            clinical_staff_user = ClinicalStaff(
                username=legacy_user.username,
                language=legacy_user.language.lower(),
                date_joined=legacy_user.date_added,
            )

            if legacy_user.oa_role == admin_role:
                clinical_staff_user.is_staff = True
                clinical_staff_user.is_superuser = True

                if self._save_clinical_staff_user(clinical_staff_user):
                    # waiting for fix to be released: https://github.com/typeddjango/django-stubs/pull/1864
                    admin_group.user_set.add(clinical_staff_user)  # type: ignore[attr-defined]
                    admin_users_counter += 1
                    all_users_counter += 1
            else:
                role_module = LegacyOARoleModule.objects.filter(
                    oa_role=legacy_user.oa_role,
                    module=patient_module,
                    access__gte=Access.READ_WRITE.value,
                )

                if self._save_clinical_staff_user(clinical_staff_user):
                    # access codes 0-7
                    if role_module:
                        # waiting for fix to be released: https://github.com/typeddjango/django-stubs/pull/1864
                        registrant_group.user_set.add(clinical_staff_user)  # type: ignore[attr-defined]
                        staff_users_counter += 1

                    all_users_counter += 1
        message = 'Migrated {total} of {total_legacy} users ({admins} system administrators and {staff} registrants)'
        self.stdout.write(message.format(
            total=all_users_counter,
            total_legacy=legacy_users.count(),
            admins=admin_users_counter,
            staff=staff_users_counter,
        ))

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
            self.stderr.write(self.style.ERROR(
                'Error: {msg} when saving username: {username}'.format(
                    msg=exception,
                    username=clinical_staff_user.username,
                ),
            ))
            return False

        clinical_staff_user.save()
        return True
