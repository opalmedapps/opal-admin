"""Management command for inserting test data."""
from typing import Any

from django.conf import settings
from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand, CommandParser
from django.db import transaction

from rest_framework.authtoken.models import Token

from opal.caregivers.models import SecurityQuestion
from opal.core import constants
from opal.users.models import ClinicalStaff

from .insert_test_data import InstitutionOption, create_institution, create_sites


class Command(BaseCommand):
    """
    Command for initializing the minimum required data.

    Creates the required groups, users, security questions, tokens etc.
    """

    help = (  # noqa: A003
        'Initialize required data for a new project.'
        + ' Can only be run at the beginning of setting up a project.'
    )

    def add_arguments(self, parser: CommandParser) -> None:
        """
        Add arguments to the command.

        Args:
            parser: the command parser to add arguments to
        """
        parser.add_argument(
            '--force-delete',
            action='store_true',
            default=False,
            help='Force deleting existing data first before initializing (default: false)',
        )
        parser.add_argument(
            '--muhc-deployment',
            action='store_true',
            default=False,
            help='Add MUHC deployment-specific data such as the MUHC institution, sites',
        )

    @transaction.atomic
    def handle(self, *args: Any, **options: Any) -> None:
        """
        Handle execution of the command.

        Creates the required user groups and users.
        Stops if data already exists.

        Args:
            args: additional arguments
            options: additional keyword arguments
        """
        if any([
            Group.objects.all().exists(),
            SecurityQuestion.objects.all().exists(),
        ]):
            force_delete: bool = options['force_delete']

            if not force_delete:
                self.stderr.write(self.style.ERROR('There already exists data'))
                return

            self.stdout.write(self.style.WARNING('Deleting existing data'))

            # keep system users
            ClinicalStaff.objects.exclude(
                username__in=[
                    constants.USERNAME_LISTENER,
                    constants.USERNAME_LISTENER_REGISTRATION,
                    constants.USERNAME_INTERFACE_ENGINE,
                    constants.USERNAME_BACKEND_LEGACY,
                ],
            ).delete()
            Group.objects.all().delete()
            SecurityQuestion.objects.all().delete()

            self.stdout.write(self.style.SUCCESS('Data successfully deleted'))

        muhc_deployment: bool = options['muhc_deployment']
        self._create_data(muhc_deployment)

        self.stdout.write(self.style.SUCCESS('Data successfully created'))

    def _create_data(self, muhc_deployment: bool) -> None:  # noqa: WPS210, WPS213
        """
        Create all initial data.

        Takes care of:
            * default security questions
            * groups and their permissions
            * users
            * tokens for system users
            * institution and sites for muhc if flag set

        Args:
            muhc_deployment: whether to insert MUHC specific deployment data
        """
        _create_security_questions()

        # groups
        # TODO: if we need French names for groups as well we will create our own Group model
        # or an extra Group model (with a OneToOneField) with translated names
        # maybe this can be done later
        medical_records = Group.objects.create(name='Medical Records')
        registrants = Group.objects.create(name='Registrants')
        hospital_managers = Group.objects.create(name='Hospital Settings Managers')
        data_exporters = Group.objects.create(name='Questionnaire Data Exporters')
        user_managers = Group.objects.create(name=settings.USER_MANAGER_GROUP_NAME)
        Group.objects.create(name=settings.ORMS_GROUP_NAME)
        Group.objects.create(name=settings.ADMIN_GROUP_NAME)

        # users
        # TODO: should non-human users have a different user type (right now it would be clinician/clinical staff)?
        listener, _ = ClinicalStaff.objects.get_or_create(username=constants.USERNAME_LISTENER)
        listener.set_unusable_password()
        listener.save()
        listener_registration, _ = ClinicalStaff.objects.get_or_create(
            username=constants.USERNAME_LISTENER_REGISTRATION,
        )
        listener_registration.set_unusable_password()
        listener_registration.save()
        interface_engine, _ = ClinicalStaff.objects.get_or_create(username=constants.USERNAME_INTERFACE_ENGINE)
        interface_engine.set_unusable_password()
        interface_engine.save()
        legacy_backend, _ = ClinicalStaff.objects.get_or_create(username=constants.USERNAME_BACKEND_LEGACY)
        legacy_backend.set_unusable_password()
        legacy_backend.save()

        # permissions
        view_institution = _find_permission('hospital_settings', 'view_institution')
        view_patient = _find_permission('patients', 'view_patient')
        view_site = _find_permission('hospital_settings', 'view_site')
        view_securityquestion = _find_permission('caregivers', 'view_securityquestion')

        listener.user_permissions.set([
            view_institution,
            view_site,
            view_securityquestion,
        ])

        listener_registration.user_permissions.set([
            view_institution,
            view_securityquestion,
        ])

        legacy_backend.user_permissions.set([
            view_patient,
        ])

        # Medical Records
        medical_records.permissions.add(_find_permission('patients', 'can_manage_relationships'))

        # Registrants
        registrants.permissions.add(_find_permission('patients', 'can_perform_registration'))

        # Hospital Settings Managers
        hospital_managers.permissions.set([
            _find_permission('patients', 'can_manage_relationshiptypes'),
            _find_permission('hospital_settings', 'can_manage_institutions'),
            _find_permission('hospital_settings', 'can_manage_sites'),
        ])

        # Questionnaire Data Exporters
        data_exporters.permissions.set([
            _find_permission('questionnaires', 'export_report'),
        ])

        # User Managers
        user_managers.permissions.set([
            _find_permission('users', 'view_clinicalstaff'),
            _find_permission('users', 'add_clinicalstaff'),
            _find_permission('users', 'change_clinicalstaff'),
        ])

        if muhc_deployment:
            institution = create_institution(InstitutionOption.omi)
            create_sites(InstitutionOption.omi, institution)

        # get existing or create new tokens for the API users
        token_listener, _ = Token.objects.get_or_create(user=listener)
        token_listener_registration, _ = Token.objects.get_or_create(user=listener_registration)
        token_interface_engine, _ = Token.objects.get_or_create(user=interface_engine)
        token_legacy_backend, _ = Token.objects.get_or_create(user=legacy_backend)

        self.stdout.write(f'{listener.username} token: {token_listener}')
        self.stdout.write(f'{listener_registration.username} token: {token_listener_registration}')
        self.stdout.write(f'{interface_engine.username} token: {token_interface_engine}')
        self.stdout.write(f'{legacy_backend.username} token: {token_legacy_backend}')


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
