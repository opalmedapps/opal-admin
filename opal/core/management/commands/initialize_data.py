"""Management command for inserting test data."""
from typing import Any

from django.conf import settings
from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand
from django.db import transaction

from rest_framework.authtoken.models import Token

from opal.caregivers.models import SecurityQuestion
from opal.users.models import User


class Command(BaseCommand):
    """
    Command for initializing the minimum required data.

    Creates the required groups, users, security questions, tokens etc.
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
        if any([
            Group.objects.all().exists(),
            SecurityQuestion.objects.all().exists(),
        ]):
            self.stderr.write(self.style.ERROR('There already exists data'))
        else:
            self._create_data()
            self.stdout.write(self.style.SUCCESS('Data successfully created'))

    def _create_data(self) -> None:  # noqa: WPS210
        """
        Create all test data.

        Takes care of:
            * default security questions
            * groups and their permissions
            * users
            * tokens for system users
        """
        _create_security_questions()

        # groups
        # TODO: if we need French names for groups as well we will create our own Group model
        # maybe this can be done later
        # TODO: TBD: are administrators and superusers the same?
        # then an Administrators group is unnecessary
        medical_records = Group.objects.create(name='Medical Records')
        Group.objects.create(name='Clinicians')
        receptionists = Group.objects.create(name='Receptionists')
        Group.objects.create(name=settings.ORMS_USER_GROUP)

        # users
        # TODO: should non-human users have a different user type (right now it would be clinician/clinical staff)?
        listener = User.objects.create(username='Listener')
        interface_engine = User.objects.create(username='Interface Engine')

        # permissions
        #
        # listener
        view_institution = _find_permission('hospital_settings', 'view_institution')
        view_site = _find_permission('hospital_settings', 'view_site')
        view_caregiver_profile = _find_permission('caregivers', 'view_caregiverprofile')
        view_registration_code = _find_permission('caregivers', 'view_registrationcode')
        view_hospital_patient = _find_permission('patients', 'view_hospitalpatient')
        view_patient = _find_permission('patients', 'view_patient')
        view_relationship = _find_permission('patients', 'view_relationship')

        listener.user_permissions.set([
            view_institution,
            view_site,
            view_caregiver_profile,
            view_hospital_patient,
            view_registration_code,
            view_patient,
            view_relationship,
        ])

        # OIE
        # TODO: determine which permissions are specifically needed

        # Medical Records
        medical_records.permissions.add(_find_permission('patients', 'can_manage_relationships'))

        # Receptionists
        receptionists.permissions.add(_find_permission('patients', 'can_perform_registration'))

        # Clinicians
        # TODO: determine which permissions are specifically needed

        # create tokens for the API users
        token_listener = Token.objects.create(user=listener)
        token_interface_engine = Token.objects.create(user=interface_engine)

        self.stdout.write(f'Listener token: {token_listener}')
        self.stdout.write(f'Interface Engine token: {token_interface_engine}')


def _create_security_questions() -> None:
    questions = [
        ('What is the name of your first pet?', 'Quel est le nom de votre premier animal de compagnie?'),
        (
            'What is the first name of your childhood best friend?',
            "Quel est le prénom de votre meilleur ami d'enfance?",
        ),
        ('What is the name of your eldest niece?', "Quel est le prénom de l'aînée de vos nièces?"),
        ('What is the name of your eldest nephew?', "Quel est le prénom de l'aîné de vos neveux?"),
        (
            'What is the maiden name of your maternal grandmother?',
            'Quel est le nom de jeune fille de votre grand-mère maternelle?',
        ),
        (
            'Where did you go to on your first vacation?',
            'Où êtes-vous allé lors de vos premières vacances?',
        ),
    ]

    security_questions = [
        SecurityQuestion(title=question_en, title_en=question_en, title_fr=question_fr)
        for question_en, question_fr in questions
    ]

    for security_question in security_questions:
        security_question.full_clean()

    SecurityQuestion.objects.bulk_create(security_questions)


def _find_permission(app_label: str, codename: str) -> Permission:
    return Permission.objects.get(content_type__app_label=app_label, codename=codename)
