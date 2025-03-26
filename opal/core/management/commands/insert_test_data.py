"""Management command for inserting test data."""
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any, Optional

from django.core.files import File
from django.core.management.base import BaseCommand
from django.db import transaction

from opal.caregivers.models import CaregiverProfile
from opal.hospital_settings.models import Institution, Site
from opal.patients.models import HospitalPatient, Patient, Relationship, RelationshipStatus, RelationshipType
from opal.users.models import Caregiver

DIRECTORY_FILES = 'opal/core/management/commands/files'
PARKING_URLS = ('https://muhc.ca/patient-and-visitor-parking', 'https://cusm.ca/stationnement')


class Command(BaseCommand):
    """
    Command for inserting test data.

    Inserts:
        *
    """

    help = 'Insert data for testing purposes. Data includes patients, caregivers, relationships.'  # noqa: A003

    @transaction.atomic
    def handle(self, *args: Any, **kwargs: Any) -> None:
        if any(
            [
                Institution.objects.all().exists(),
                Patient.objects.all().exists(),
                Relationship.objects.all().exists(),
            ]
        ):
            confirm = input(
                'Database already contains data.\n'
                + 'To continue, existing data has to be deleted.\n'
                + 'Are you sure you want to do this?\n'
                + '\n'
                + "Type 'yes' to continue, or 'no' to cancel: ",
            )

            # if confirm != 'yes':
            # print('Test data insertion cancelled.')
            # return

            # _delete_existing_data()

        _create_test_data()


def _delete_existing_data() -> None:
    Relationship.objects.delete()
    # TODO: does it also delete HospitalPatient instances?
    Patient.objects.delete()
    # also deletes CaregiverProfiles
    Caregiver.objects.delete()
    # also deletes Sites
    Institution.objects.delete()


def _create_test_data() -> None:
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
        # TODO: calculate birth year depending on current year to get to correct age
        date_of_birth=date.fromisoformat('1986-10-01'),
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
        date_of_birth=date.fromisoformat('1983-05-12'),
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
        date_of_birth=date.fromisoformat('2013-02-23'),
        sex=Patient.SexType.MALE,
        ramq='SIMB13022399',
        legacy_id=53,
        mrns=[
            (mch, '9999996'),
        ],
    )

    maggie = _create_patient(
        first_name='Maggie',
        last_name='Simpson',
        date_of_birth=date.fromisoformat('2022-01-14'),
        sex=Patient.SexType.FEMALE,
        ramq='SIMM22511499',
        legacy_id=54,
        mrns=[
            (mch, '9999994'),
        ],
    )

    # caregivers
    user_marge = _create_caregiver(
        first_name=marge.first_name,
        last_name=marge.last_name,
        username='marge_username_undefined',
        email='muhc.app.mobile@gmail.com',
        language='fr',
        phone_number='+15144758941',
        legacy_id=1,
    )

    user_homer = _create_caregiver(
        first_name=homer.first_name,
        last_name=homer.last_name,
        username='homer_username_undefined',
        email='homer@opaldevapps.dev',
        language='fr',
        phone_number='+14381234567',
        legacy_id=2,
    )

    # get relationship types
    type_self = RelationshipType.objects.self()
    type_parent = RelationshipType.objects.parent_guardian()

    # relationships
    # _create_relationship(
    #     patient=marge,
    #     caregiver=marge,
    #     relationship_type=type_self,
    #     request_date=
    # )


def _create_institution() -> Institution:
    with Path(DIRECTORY_FILES).joinpath('logo.png').open('rb') as logo_file:
        logo = File(logo_file, logo_file.name)

        with Path(DIRECTORY_FILES).joinpath('terms_of_use.pdf').open('rb') as terms_file:
            terms_of_use = File(terms_file, terms_file.name)

            institution = Institution(
                name='McGill University Health Centre',
                name_fr='Centre universitaire de santé McGill',
                code='MUHD',
                support_email='opal@muhc.mcgill.ca',
                terms_of_use=terms_of_use,
                terms_of_use_fr=terms_of_use,
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
) -> Patient:
    patient = Patient(
        first_name=first_name,
        last_name=last_name,
        date_of_birth=date_of_birth,
        sex=sex,
        ramq=ramq,
        legacy_id=legacy_id,
    )

    patient.full_clean()
    patient.save()

    for mrn in mrns:
        hospital_patient = HospitalPatient(
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
    phone_number: Optional[str],
    legacy_id: int,
) -> CaregiverProfile:
    user = Caregiver(
        first_name=first_name,
        last_name=last_name,
        username=username,
        email=email,
        language=language,
        phone_number=phone_number,
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
    end_date: Optional[date],
) -> None:
    relationship = Relationship(
        patient=patient,
        caregiver=caregiver,
        type=relationship_type,
        status=status,
        request_date=request_date,
        start_date=start_date,
        end_date=end_date,
    )

    relationship.full_clean()
    relationship.save()
