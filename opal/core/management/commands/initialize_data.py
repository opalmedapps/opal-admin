"""Management command for inserting test data."""
import secrets
from typing import Any

from django.conf import settings
from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand, CommandParser
from django.db import transaction

from rest_framework.authtoken.models import Token

from opal.caregivers.models import SecurityQuestion
from opal.core import constants
from opal.legacy import models as legacy_models
from opal.users.models import ClinicalStaff


def token(value: str) -> str:
    """
    Validate token string.

    Args:
        value: The token string to validate

    Raises:
        ValueError: If the token string is not 40 characters long

    Returns:
        the token string
    """
    if len(value) != constants.TOKEN_LENGTH:
        raise ValueError('Token must be 40 characters long')

    return value


def password(value: str) -> str:
    """
    Validate that the password has a minimum required length.

    Args:
        value: the password string to validate

    Raises:
        ValueError: If the password is too short

    Returns:
        the password string
    """
    minimum_length = constants.ADMIN_PASSWORD_MIN_LENGTH

    if len(value) < minimum_length:
        raise ValueError(f'Password must be at least {minimum_length} characters long')

    return value


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
        password_help = (
            'password for the admin user to be used'
            + f' instead of generating a random one (minimum length: {constants.ADMIN_PASSWORD_MIN_LENGTH}'
        )
        parser.add_argument(
            '--admin-password',
            type=password,
            default=None,
            help=password_help,
        )
        parser.add_argument(
            '--listener-token',
            type=token,
            default=None,
            help='token for the listener user to be used instead of generating a random one (length: 40)',
        )
        parser.add_argument(
            '--listener-registration-token',
            type=token,
            default=None,
            help='token for the listener-registration user to be used instead of generating a random one (length: 40)',
        )
        parser.add_argument(
            '--interface-engine-token',
            type=token,
            default=None,
            help='token for the interface-engine user to be used instead of generating a random one (length: 40)',
        )
        parser.add_argument(
            '--opaladmin-backend-legacy-token',
            type=token,
            default=None,
            help='token for the opaladmin backend user to be used instead of generating a random one (length: 40)',
        )
        if settings.ORMS_ENABLED:
            parser.add_argument(
                '--orms-token',
                type=token,
                default=None,
                help='token for the orms system user to be used instead of generating a random one (length: 40)',
            )

    @transaction.atomic
    def handle(self, *args: Any, **options: Any) -> None:
        """
        Handle execution of the command.

        Creates the required user groups and users.
        Stops if data already exists.

        Args:
            args: additional arguments
            options: the options keyword arguments passed to the command
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

            self._delete_data()

            self.stdout.write(self.style.SUCCESS('Data successfully deleted'))

        self._create_data(**options)
        self._create_legacy_data(**options)

        self.stdout.write(self.style.SUCCESS('Data successfully created'))

    def _delete_data(self) -> None:
        """
        Delete existing data that was initialized.

        Keeps the system users so that they keep their existing API tokens.
        """
        # keep system users
        ClinicalStaff.objects.exclude(
            username__in=[
                constants.USERNAME_LISTENER,
                constants.USERNAME_LISTENER_REGISTRATION,
                constants.USERNAME_INTERFACE_ENGINE,
                constants.USERNAME_BACKEND_LEGACY,
                constants.USERNAME_ORMS,
            ],
        ).delete()
        Group.objects.all().delete()
        SecurityQuestion.objects.all().delete()

    def _create_data(self, **options: Any) -> None:  # noqa: WPS210, WPS213
        """
        Create all initial data.

        Takes care of:
            * default security questions
            * groups and their permissions
            * users
            * tokens for system users

        Args:
            options: the options keyword arguments passed to the command
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
            view_institution,
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

        # get existing or create new tokens for the API users
        predefined_token = options['listener_token']
        token_listener, _ = Token.objects.get_or_create(user=listener, defaults={'key': predefined_token})  # noqa: WPS204, E501

        predefined_token = options['listener_registration_token']
        token_listener_registration, _ = Token.objects.get_or_create(
            user=listener_registration,
            defaults={'key': predefined_token},
        )

        predefined_token = options['interface_engine_token']
        token_interface_engine, _ = Token.objects.get_or_create(
            user=interface_engine,
            defaults={'key': predefined_token},
        )

        predefined_token = options['opaladmin_backend_legacy_token']
        token_legacy_backend, _ = Token.objects.get_or_create(
            user=legacy_backend,
            defaults={'key': predefined_token},
        )

        self.stdout.write(f'{listener.username} token: {token_listener}')
        self.stdout.write(f'{listener_registration.username} token: {token_listener_registration}')
        self.stdout.write(f'{interface_engine.username} token: {token_interface_engine}')
        self.stdout.write(f'{legacy_backend.username} token: {token_legacy_backend}')

        if settings.ORMS_ENABLED:
            self._create_orms_data(**options)

    def _create_orms_data(self, **options: Any) -> None:
        """Create ORMS users, group, and system user token if ORMs is enabled.

        Args:
            options: the options keyword arguments passed to the function
        """
        # ORMS Users and Group
        orms_users = Group.objects.create(name=settings.ORMS_GROUP_NAME)
        orms_users.permissions.set([
            _find_permission('health_data', 'view_quantitysample'),
            _find_permission('health_data', 'change_quantitysample'),
        ])
        # ORMS System User/Token for API auth
        orms, _ = ClinicalStaff.objects.get_or_create(username=constants.USERNAME_ORMS)
        orms.set_unusable_password()
        orms.save()
        predefined_token = options['orms_token']
        token_orms, _ = Token.objects.get_or_create(
            user=orms,
            defaults={'key': predefined_token},
        )
        self.stdout.write(f'{orms.username} token: {token_orms}')

    def _create_legacy_data(self, **options: Any) -> None:
        # create a legacy admin user with the system administrator role
        admin_role = legacy_models.LegacyOARole.objects.get(name_en='System Administrator')
        legacy_models.LegacyOAUser.objects.create(
            username='admin',
            # the password does not matter since legacy OpalAdmin
            # does not support logging in with AD or regular login at the same time
            # i.e., if AD login is enabled a regular log in is not possible
            password=secrets.token_urlsafe(constants.ADMIN_PASSWORD_MIN_LENGTH_BYTES),
            oa_role=admin_role,
            user_type=legacy_models.LegacyOAUserType.HUMAN,
        )

        password_option: str = options['admin_password']
        raw_password = (
            password_option
            if password_option
            else secrets.token_urlsafe(constants.ADMIN_PASSWORD_MIN_LENGTH_BYTES)
        )
        ClinicalStaff.objects.create_superuser(username='admin', email=None, password=raw_password)

        message = 'Created superuser with username "admin"'

        if not password_option:
            message += ' and generated password: {raw_password}'  # noqa: WPS336 (explicit over implicit)

        self.stdout.write(message)


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
