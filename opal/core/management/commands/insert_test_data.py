"""Management command for inserting test data."""
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any, Optional

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from dateutil.relativedelta import relativedelta

from opal.caregivers.models import CaregiverProfile, SecurityAnswer
from opal.hospital_settings.models import Institution, Site
from opal.patients.models import HospitalPatient, Patient, Relationship, RelationshipStatus, RelationshipType
from opal.users.models import Caregiver

DIRECTORY_FILES = Path('opal/core/management/commands/files')
PARKING_URLS = ('https://muhc.ca/patient-and-visitor-parking', 'https://cusm.ca/stationnement')


class Command(BaseCommand):
    """
    Command for inserting test data.

    Inserts an institution, sites, patients, caregivers and relationships between the patients and caregivers.
    """

    help = 'Insert data for testing purposes. Data includes patients, caregivers, relationships.'  # noqa: A003

    @transaction.atomic
    def handle(self, *args: Any, **kwargs: Any) -> None:
        """
        Handle execution of the command.

        Prompts whether existing data shall be deleted if there is existing data.
        Creates test data if there is no existing data or the prompt was confirmed.

        Args:
            args: additional arguments
            kwargs: additional keyword arguments
        """
        if any([
            Relationship.objects.all().exists(),
            Patient.objects.all().exists(),
            Caregiver.objects.all().exists(),
            Institution.objects.all().exists(),
            SecurityAnswer.objects.all().exists(),
        ]):
            confirm = input(
                'Database already contains data.\n'
                + 'To continue, existing data has to be deleted.\n'
                + 'Are you sure you want to do this?\n'
                + '\n'
                + "Type 'yes' to continue, or 'no' to cancel: ",
            )

            if confirm != 'yes':
                self.stdout.write('Test data insertion cancelled')
                return

            _delete_existing_data()
            self.stdout.write('Existing test data deleted')

        _create_test_data()
        self.stdout.write(self.style.SUCCESS('Test data successfully created'))


def _delete_existing_data() -> None:
    """Delete all the existing test data."""
    Relationship.objects.all().delete()
    Patient.objects.all().delete()
    # also deletes security answers
    CaregiverProfile.objects.all().delete()
    Caregiver.objects.all().delete()
    # also deletes Sites
    Institution.objects.all().delete()


def _create_test_data() -> None:
    """
    Create all test data.

    Takes care of:
        * institution
        * sites
        * patients
        * caregivers
        * relationships between the patients and caregivers
    """
    today = date.today()

    # hospital settings
    institution = _create_institution()
    rvh = _create_site(
        institution,
        'Royal Victoria Hospital',
        'Hôpital Royal Victoria',
        'RVH',
        PARKING_URLS,
        ('https://muhc.ca/getting-glen-site', 'https://cusm.ca/se-rendre-au-site-glen'),
        Decimal('45.473435'),
        Decimal('-73.601611'),
    )
    mgh = _create_site(
        institution,
        'Montreal General Hospital',
        'Hôpital général de Montréal',
        'MGH',
        PARKING_URLS,
        ('https://muhc.ca/how-get-montreal-general-hospital', 'https://cusm.ca/se-rendre-lhopital-general-de-montreal'),
        Decimal('45.496828'),
        Decimal('-73.588782'),
    )
    mch = _create_site(
        institution,
        "Montreal Children's Hospital",
        "L'Hôpital de Montréal pour enfants",
        'MCH',
        PARKING_URLS,
        ('https://www.thechildren.com/getting-hospital', 'https://www.hopitalpourenfants.com/se-rendre-lhopital'),
        Decimal('45.473343'),
        Decimal('-73.600802'),
    )
    _create_site(
        institution,
        'Lachine Hospital',
        'Hôpital de Lachine',
        'LAC',
        PARKING_URLS,
        ('https://muhc.ca/how-get-lachine-hospital', 'https://cusm.ca/se-rendre-lhopital-de-lachine'),
        Decimal('45.44121'),
        Decimal('-73.676791'),
    )

    # patients
    marge = _create_patient(
        first_name='Marge',
        last_name='Simpson',
        date_of_birth=_create_date(36, 10, 1),
        sex=Patient.SexType.FEMALE,
        ramq='SIMM86600199',
        legacy_id=51,
        mrns=[
            (rvh, '9999996'),
        ],
    )

    homer = _create_patient(
        first_name='Homer',
        last_name='Simpson',
        date_of_birth=_create_date(39, 5, 12),
        sex=Patient.SexType.MALE,
        ramq='SIMH83051299',
        legacy_id=52,
        mrns=[
            (rvh, '9999997'),
            (mgh, '9999996'),
        ],
    )

    bart = _create_patient(
        first_name='Bart',
        last_name='Simpson',
        date_of_birth=_create_date(14, 2, 23),
        sex=Patient.SexType.MALE,
        ramq='SIMB13022399',
        legacy_id=53,
        mrns=[
            (mch, '9999996'),
        ],
    )

    lisa = _create_patient(
        first_name='Lisa',
        last_name='Simpson',
        date_of_birth=_create_date(8, 5, 9),
        sex=Patient.SexType.FEMALE,
        ramq='SIML14550999',
        legacy_id=54,
        mrns=[
            (mch, '9999993'),
        ],
    )

    mona = _create_patient(
        first_name='Mona',
        last_name='Simpson',
        date_of_birth=date(1940, 3, 15),
        sex=Patient.SexType.FEMALE,
        ramq='SIMM40531599',
        legacy_id=55,
        mrns=[
            (rvh, '9999993'),
        ],
        date_of_death=_relative_date(today, -2),
    )

    # caregivers
    user_marge = _create_caregiver(
        first_name=marge.first_name,
        last_name=marge.last_name,
        username='QXmz5ANVN3Qp9ktMlqm2tJ2YYBz2',
        email='marge@opalmedapps.ca',
        language='en',
        phone_number='+15551234567',
        legacy_id=1,
    )

    user_homer = _create_caregiver(
        first_name=homer.first_name,
        last_name=homer.last_name,
        username='PyKlcbRpMLVm8lVnuopFnFOHO4B3',
        email='homer@opalmedapps.ca',
        language='fr',
        phone_number='+15557654321',
        legacy_id=2,
        # homer is blocked: he lost access due to him being unstable
        is_active=False,
    )

    user_bart = _create_caregiver(
        first_name=bart.first_name,
        last_name=bart.last_name,
        username='SipDLZCcOyTYj7O3C8HnWLalb4G3',
        email='bart@opalmedapps.ca',
        language='fr',
        phone_number='+498999998123',
        legacy_id=3,
    )

    user_mona = _create_caregiver(
        first_name=mona.first_name,
        last_name=mona.last_name,
        username='61DXBRwLCmPxlaUoX6M1MP9DiEl1',
        email='mona@opalmedapps.ca',
        language='fr',
        phone_number='+15144758941',
        legacy_id=4,
        is_active=False,
    )

    # get relationship types
    type_self = RelationshipType.objects.self_type()
    type_parent = RelationshipType.objects.parent_guardian()
    type_caregiver = RelationshipType.objects.guardian_caregiver()
    type_mandatary = RelationshipType.objects.mandatary()

    # relationships
    # Marge --> Marge: Self
    _create_relationship(
        patient=marge,
        caregiver=user_marge,
        relationship_type=type_self,
        status=RelationshipStatus.CONFIRMED,
        request_date=_relative_date(today, -4),
        start_date=_relative_date(today, -6),
    )

    # Marge --> Homer: Mandatary
    _create_relationship(
        patient=homer,
        caregiver=user_marge,
        relationship_type=type_mandatary,
        status=RelationshipStatus.CONFIRMED,
        request_date=_relative_date(today, -1),
        start_date=_relative_date(today, -1),
    )

    # Homer --> Homer: Self
    _create_relationship(
        patient=homer,
        caregiver=user_homer,
        relationship_type=type_self,
        status=RelationshipStatus.REVOKED,
        request_date=_relative_date(today, -10),
        start_date=_relative_date(today, -12),
        end_date=_relative_date(today, -1),
        reason='Revoked due to legal court order.',
    )

    # Marge --> Bart: Guardian/Parent
    date_bart_fourteen = _relative_date(bart.date_of_birth, 14)
    _create_relationship(
        patient=bart,
        caregiver=user_marge,
        relationship_type=type_parent,
        status=RelationshipStatus.EXPIRED,
        request_date=_relative_date(today, -9),
        start_date=bart.date_of_birth,
        end_date=date_bart_fourteen,
    )

    # Marge --> Bart: Guardian-Caregiver
    _create_relationship(
        patient=bart,
        caregiver=user_marge,
        relationship_type=type_caregiver,
        status=RelationshipStatus.PENDING,
        request_date=date_bart_fourteen,
        start_date=date_bart_fourteen,
        end_date=_relative_date(bart.date_of_birth, 18),
    )

    # Marge --> Lisa: Guardian/Parent
    _create_relationship(
        patient=lisa,
        caregiver=user_marge,
        relationship_type=type_parent,
        status=RelationshipStatus.CONFIRMED,
        request_date=_relative_date(today, -1),
        start_date=_relative_date(today, -3),
        end_date=_relative_date(lisa.date_of_birth, 14),
    )

    # Bart --> Bart
    _create_relationship(
        patient=bart,
        caregiver=user_bart,
        relationship_type=type_self,
        status=RelationshipStatus.CONFIRMED,
        request_date=date_bart_fourteen,
        start_date=date_bart_fourteen,
    )

    # Marge --> Mona: Mandatary
    _create_relationship(
        patient=mona,
        caregiver=user_marge,
        relationship_type=type_mandatary,
        status=RelationshipStatus.EXPIRED,
        request_date=_relative_date(today, -5),
        start_date=_relative_date(today, -3),
        end_date=_relative_date(today, -2),
        reason='Patient deceased.',
    )

    # Mona --> Mona: Self
    _create_relationship(
        patient=mona,
        caregiver=user_mona,
        relationship_type=type_self,
        status=RelationshipStatus.EXPIRED,
        request_date=_relative_date(today, -5),
        start_date=_relative_date(today, -4),
        end_date=_relative_date(today, -2),
        reason='Patient deceased.',
    )
    # create the same security question and answers for the caregivers
    _create_security_answers(user_marge)
    _create_security_answers(user_homer)
    _create_security_answers(user_bart)
    _create_security_answers(user_mona)


def _create_institution() -> Institution:
    """
    Create, validate and save an institution instance with the given properties.

    The logo and terms of use are loaded from the file system under `files/` within the directory of this module.

    Returns:
        the newly created institution
    """
    with DIRECTORY_FILES.joinpath('logo.png').open('rb') as logo_file:
        logo = ContentFile(logo_file.read(), logo_file.name)

    with DIRECTORY_FILES.joinpath('terms_of_use_en.pdf').open('rb') as terms_file_en:
        terms_of_use_en = ContentFile(terms_file_en.read(), terms_file_en.name)

    with DIRECTORY_FILES.joinpath('terms_of_use_fr.pdf').open('rb') as terms_file_fr:
        terms_of_use_fr = ContentFile(terms_file_fr.read(), terms_file_fr.name)

    institution = Institution(
        name='McGill University Health Centre',
        name_fr='Centre universitaire de santé McGill',
        code='MUHC',
        support_email='opal@muhc.mcgill.ca',
        terms_of_use=terms_of_use_en,
        terms_of_use_fr=terms_of_use_fr,
        logo=logo,
        logo_fr=logo,
    )
    institution.full_clean()
    institution.save()

    return institution


def _create_site(
    institution: Institution,
    name: str,
    name_fr: str,
    code: str,
    parking_urls: tuple[str, str],
    direction_urls: tuple[str, str],
    latitude: Decimal,
    longitude: Decimal,
) -> Site:
    """
    Create, validate and save a site instance with the given properties.

    Args:
        institution: the institution instance the site belongs to
        name: the English name of the site
        name_fr: the French name of the site
        code: the code (acronym) of the institution
        parking_urls: a tuple of URLs to the English and French parking information
        direction_urls: a tuple of URLs to the English and French direction to the hospital information
        latitude: the latitude of the GPS location of the site
        longitude: the longitude of the GPS location of the site

    Returns:
        the newly created site
    """
    site = Site(
        institution=institution,
        name=name,
        name_fr=name_fr,
        code=code,
        parking_url=parking_urls[0],
        parking_url_fr=parking_urls[1],
        direction_url=direction_urls[0],
        direction_url_fr=direction_urls[1],
        latitude=latitude,
        longitude=longitude,
    )

    site.full_clean()
    site.save()

    return site


def _create_patient(
    first_name: str,
    last_name: str,
    date_of_birth: date,
    sex: Patient.SexType,
    ramq: str,
    legacy_id: int,
    mrns: list[tuple[Site, str]],
    date_of_death: Optional[date] = None,
) -> Patient:
    """
    Create, validate and save a patient instance with the given properties.

    Also creates related hospital patient instances for the given list of site and MRN tuples.

    Args:
        first_name: the patient's first name
        last_name: the patient's last name
        date_of_birth: the patient's date of birth
        sex: the patient's sex
        ramq: the patient's RAMQ number
        legacy_id: the ID (aka. SerNum) of the patient in the legacy DB
        mrns: a list of Site, MRN tuples for the MRNs the patient has at different sites
        date_of_death: an optional date of death if the patient is deceased

    Returns:
        the created patient instance
    """
    patient = Patient(
        first_name=first_name,
        last_name=last_name,
        date_of_birth=date_of_birth,
        sex=sex,
        ramq=ramq,
        legacy_id=legacy_id,
    )

    if date_of_death:
        patient.date_of_death = timezone.make_aware(datetime.combine(date_of_death, datetime.min.time()))

    patient.full_clean()
    patient.save()

    for mrn in mrns:
        hospital_patient = HospitalPatient(
            patient=patient,
            site=mrn[0],
            mrn=mrn[1],
        )

        hospital_patient.full_clean()
        hospital_patient.save()

    return patient


def _create_caregiver(
    first_name: str,
    last_name: str,
    username: str,
    email: str,
    language: str,
    phone_number: str,
    legacy_id: int,
    is_active: bool = True,
) -> CaregiverProfile:
    """
    Create, validate and save a `Caregiver` user and related `CaregiverProfile` with the given properties.

    The user will not have a password.

    Args:
        first_name: the caregiver's first name
        last_name: the caregiver's last name
        username: the caregiver's username (Firebase username)
        email: the caregiver's email address
        language: the caregiver's language (en for English, fr for French)
        phone_number: the caregiver's phone number
        legacy_id: the ID (aka. SerNum) of the caregiver in the legacy DB
        is_active: `True`, if the user account is active (registered), `False` otherwise

    Returns:
        the `CaregiverProfile` instance which allows you to get the user instance from it.
    """
    user = Caregiver(
        first_name=first_name,
        last_name=last_name,
        username=username,
        email=email,
        language=language,
        phone_number=phone_number,
        is_active=is_active,
    )

    # don't expect a password
    user.full_clean(exclude=('password',))
    user.save()

    profile = CaregiverProfile(
        user=user,
        legacy_id=legacy_id,
    )

    profile.full_clean()
    profile.save()

    return profile


def _create_relationship(
    patient: Patient,
    caregiver: CaregiverProfile,
    relationship_type: RelationshipType,
    status: RelationshipStatus,
    request_date: date,
    start_date: date,
    end_date: Optional[date] = None,
    reason: str = '',
) -> None:
    """
    Create, validate and save a relationship instance with the given properties.

    Args:
        patient: the patient instance
        caregiver: the caregiver profile instance
        relationship_type: the type of the relationship
        status: the status of the relationship
        request_date: the request date of the relationship
        start_date: the start date of the relationship
        end_date: the optional end date of the relationship, `None` if there is no end date
        reason: the optional reason for the relationship status
    """
    relationship = Relationship(
        patient=patient,
        caregiver=caregiver,
        type=relationship_type,
        status=status,
        request_date=request_date,
        start_date=start_date,
        end_date=end_date,
        reason=reason,
    )

    relationship.full_clean()
    relationship.save()


def _create_security_answer(caregiver: CaregiverProfile, question: str, answer: str) -> None:
    security_answer = SecurityAnswer.objects.create(user=caregiver, question=question, answer=answer)
    security_answer.full_clean()
    security_answer.save()


def _create_security_answers(caregiver: CaregiverProfile) -> None:
    language = caregiver.user.language

    question1 = (
        'What is the name of your first pet?'
        if language == 'en'
        else
        'Quel est le nom de votre premier animal de compagnie?'
    )
    question2 = (
        'What was the name of your favorite superhero as a child?'
        if language == 'en'
        else
        'Quel était le nom de votre super-héros préféré durant votre enfance?'
    )
    question3 = (
        'What was the color of your first car'
        if language == 'en'
        else
        'Quelle était la couleur de votre première voiture?'
    )
    _create_security_answer(
        caregiver,
        question1,
        '5ed4c7167f059c5b864fd775f527c5a88794f9f823fea73c6284756b31a08faf6f9f950473c5aa7cdb99c56bc7807517fe4c4a0bd67318bcaec508592dd6d917',  # noqa: E501
    )
    _create_security_answer(
        caregiver,
        question2,
        'f3b49c229cc474b3334dd4a3bbe827a866cbf6d6775cde7a5c42da24b4f15db8c0e564c4ff20754841c2baa9dafffc2caa02341010456157b1de9b927f24a1e6',  # noqa: E501
    )
    _create_security_answer(
        caregiver,
        question3,
        'a7dbabba9a0371fbdb92724a5ca66401e02069089b1f3a100374e61f934fe9e959215ae0327de2bc064a9dfc351c4d64ef89bd47e95be0198a1f466c3518cc1d',  # noqa: E501
    )


def _create_date(relative_years: int, month: int, day: int) -> date:
    """
    Create a date that is relative to today.

    The date will have the given month and day.
    The year will be the number of given years before today.

    Args:
        relative_years: the number of years to subtract
        month: the month to use for the date
        day: the day to use for the date

    Returns:
        the date with the given month and day and the year the given number of years before today
    """
    current_year = date.today().year

    return date(current_year, month, day) - relativedelta(years=relative_years)


def _relative_date(base_date: date, years: int) -> date:
    """
    Calculate a relative date based on the given date and the number of years.

    The number of years can be negative, i.e., the date will be before the reference data.

    Args:
        base_date: the date from which to calculate
        years: the number of years to add to the base date, use a negative number to subtract

    Returns:
        the relative date calculated via `base_date + years`
    """
    return base_date + relativedelta(years=years)
