"""Management command for inserting test data."""
from typing import Any

from django.conf import settings
from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand
from django.db import transaction

from rest_framework.authtoken.models import Token

from opal.users.models import User


class Command(BaseCommand):
    """
    Command for initializing the minimum required data.

    Creates the required groups, users etc.
    """

    help = (  # noqa: A003
        'Initialize required data for a new project.'
        + ' Can only be run at the beginning of setting up a project.'
    )

    @transaction.atomic
    def handle(self, *args: Any, **kwargs: Any) -> None:
        """
        Handle execution of the command.

        Creates the required user groups and users.
        Stops if data already exists.

        Args:
            args: additional arguments
            kwargs: additional keyword arguments
        """
        if Group.objects.all().exists():
            self.stderr.write(self.style.ERROR('There already exists data'))

        _create_data()
        self.stdout.write(self.style.SUCCESS('Data successfully created'))


def _create_data() -> None:
    """
    Create all test data.

    Takes care of:
        * groups and their permissions
        * users
    """
    # groups
    # TODO: if we need French names for groups as well we will create our own Group model
    # maybe this can be done later
    admins = Group.objects.create(name='Administrators')
    medical_records = Group.objects.create(name='Medical Records')
    clinicians = Group.objects.create(name='Clinicians')
    receptionists = Group.objects.create(name='Receptionists')
    orms = Group.objects.create(name=settings.ORMS_USER_GROUP)

    # users
    # TODO: should non-human users have a different user type (right now it would be clinician/clinical staff)?
    listener = User.objects.create(username='Listener')
    interface_engine = User.objects.create(username='Interface Engine')

    # permissions
    #
    # listener
    view_institution = _find_permission('hospital_settings', 'view_institutions')
    view_site = _find_permission('hospital_settings', 'view_sites')
    view_caregiver_profile = _find_permission('caregivers', 'view_caregiverprofile')
    view_registration_code = _find_permission('caregivers', 'view_registrationcode')
    view_hospital_patient = _find_permission('patients', 'view_hospitalpatient')
    view_patient = _find_permission('patients', 'view_patient')
    view_relationship = _find_permission('patients', 'view_relationship')

    # OIE
    # TODO: determine which permissions are specifically needed

    # create tokens for the API users
    token_listener = Token.objects.create(user=listener)
    token_interface_engine = Token.objects.create(user=interface_engine)


def _find_permission(app_label: str, codename: str) -> Permission:
    return Permission.objects.get(content_type__app_label=app_label, codename=codename)
