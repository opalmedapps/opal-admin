# SPDX-FileCopyrightText: Copyright (C) 2023 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Management command for inserting test data."""

import hashlib
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from pathlib import Path
from types import MappingProxyType
from typing import Any

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandParser
from django.db import transaction
from django.utils import timezone

from dateutil.relativedelta import relativedelta

from opal.caregivers.models import CaregiverProfile, SecurityAnswer
from opal.hospital_settings.models import Institution, Site
from opal.patients.models import (
    DataAccessType,
    HospitalPatient,
    Patient,
    Relationship,
    RelationshipStatus,
    RelationshipType,
    RoleType,
    SexType,
)
from opal.test_results.models import GeneralTest, Note, PathologyObservation, TestType
from opal.users.models import Caregiver

DIRECTORY_FILES = Path('opal/core/management/commands/files')


class InstitutionOption(Enum):
    """The institutions that test data can be created for."""

    omi = 'OMI'
    ohigph = 'OHIGPH'

    def __str__(self) -> str:
        """
        Return the value of the enum literal.

        Returns:
            the value of the enum literal
        """
        return self.value


INSTITUTION_DATA = MappingProxyType({
    InstitutionOption.omi: {
        'name': 'Opal Demo',
        'name_fr': 'Démo de Opal',
        'acronym_fr': 'DO1',
        'support_email': 'info@opalmedapps.ca',
    },
    InstitutionOption.ohigph: {
        'name': 'Opal Demo 2',
        'name_fr': 'Démo de Opal 2',
        'acronym_fr': 'DO2',
        'support_email': 'info@opalmedapps.ca',
    },
})

SITE_DATA = MappingProxyType({
    InstitutionOption.omi: [
        (
            'Opal Demo Hospital',
            "Hôpital démo d'Opal",
            'ODH',
            'HDO',
            ('https://www.opalmedapps.com/en/soutien', 'https://www.opalmedapps.com/soutien'),
            ('https://www.opalmedapps.com/en', 'https://www.opalmedapps.com/fr'),
            Decimal('45.473435'),
            Decimal('-73.601611'),
            ('Decarie Boulevard', '1001', 'H4A3J1', 'Montréal', 'QC', '5141234567', ''),
        ),
    ],
    InstitutionOption.ohigph: [
        (
            'Opal Demo Hospital 2',
            "Hôpital démo d'Opal 2",
            'ODH2',
            'HDO2',
            (
                'https://www.chusj.org/en/a-propos/coordonnees/Stationnement',
                'https://www.chusj.org/a-propos/coordonnees/Stationnement',
            ),
            (
                # there are two pages for "getting there" (car and public transport): favouring public transport
                'https://www.chusj.org/en/a-propos/coordonnees/Se-rendre-en-transport-public',
                'https://www.chusj.org/a-propos/coordonnees/Se-rendre-en-transport-public',
            ),
            Decimal('45.503426'),
            Decimal('-73.624549'),
            ('Chemin de la Côte-Sainte-Catherine', '3175', 'H3T1C5', 'Montréal', 'QC', '5143454931', ''),
        ),
    ],
})

MRN_DATA = MappingProxyType({
    InstitutionOption.omi: {
        'Laurie Opal': [('ODH', '1092300')],
        "Rory O'Brien": [('ODH', '9999989')],
        "Cara O'Brien": [('ODH', '8888885')],
        'John Smith': [('ODH', '9999994')],
        'Richard Smith': [('ODH', '8888882')],
        'Mike Brown': [('ODH', '8888881')],
        'Kathy Brown': [('ODH', '8888880')],
        'Valerie Solanas': [('ODH', '5555553')],
        'Martin Curley': [('ODH', '5555559')],
        'Pete Boyd': [('ODH', '5555554')],
    },
    InstitutionOption.ohigph: {
        'Lisa Simpson': [('ODH2', '9999993')],
    },
})


class Command(BaseCommand):
    """
    Command for inserting test data.

    Inserts an institution, sites, patients, caregivers and relationships between the patients and caregivers.
    """

    help = 'Insert data for testing purposes. Data includes patients, caregivers, relationships.'

    def add_arguments(self, parser: CommandParser) -> None:
        """
        Add arguments to the command.

        Args:
            parser: the command parser to add arguments to
        """
        parser.add_argument(
            'institution',
            type=InstitutionOption,
            choices=list(InstitutionOption),
            help='Choose the institution for which to insert test data',
        )
        parser.add_argument(
            '--force-delete',
            action='store_true',
            default=False,
            help='Force deleting existing test data without prior confirmation',
        )

    @transaction.atomic
    def handle(self, *args: Any, **options: Any) -> None:
        """
        Handle execution of the command.

        Prompts whether existing data shall be deleted if there is existing data.
        Creates test data if there is no existing data or the prompt was confirmed.

        Args:
            args: additional arguments
            options: additional keyword arguments
        """
        if any([
            Relationship.objects.all().exists(),
            Patient.objects.all().exists(),
            Caregiver.objects.all().exists(),
            Institution.objects.all().exists(),
            SecurityAnswer.objects.all().exists(),
        ]):
            force_delete: bool = options['force_delete']

            if not force_delete:
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

        institution_option: InstitutionOption = options['institution']
        _create_test_data(institution_option)
        self.stdout.write(self.style.SUCCESS('Test data successfully created'))


def _delete_existing_data() -> None:
    """Delete all the existing test data."""
    Relationship.objects.all().delete()
    # delete any custom relationship types
    RelationshipType.objects.filter(role_type=RoleType.CAREGIVER).delete()
    Patient.objects.all().delete()
    # also deletes security answers
    CaregiverProfile.objects.all().delete()
    Caregiver.objects.all().delete()
    # also deletes Sites
    Institution.objects.all().delete()
    Note.objects.all().delete()
    PathologyObservation.objects.all().delete()
    GeneralTest.objects.all().delete()


def _create_test_data(institution_option: InstitutionOption) -> None:  # noqa: PLR0914, PLR0915
    """
    Create all test data.

    Takes care of:
        * institution
        * sites
        * patients
        * caregivers
        * relationships between the patients and caregivers
        * pathology reports matching test data setup in legacy db


    Args:
        institution_option: the chosen institution for which the test data should be inserted
    """
    today = timezone.now()

    # hospital settings
    institution = create_institution(institution_option)
    sites = create_sites(institution_option, institution)

    # create Family & Friends relationship type
    type_family = RelationshipType.objects.create(
        name='Family & Friends',
        name_fr='Famille et amis',
        description='Family & Friends',
        description_fr='Famille et amis',
        start_age=14,
        end_age=120,
        form_required=False,
    )

    mrn_data: dict[str, list[tuple[Site, str]]] = {}

    for key, value in MRN_DATA[institution_option].items():
        new_value = [(sites[site], mrn) for site, mrn in value]
        mrn_data[key] = new_value

    is_pediatric = institution_option == InstitutionOption.ohigph

    # patients
    if is_pediatric:
        _create_patient(
            first_name='Lisa',
            last_name='Simpson',
            date_of_birth=_create_date(8, 5, 9),
            sex=SexType.FEMALE,
            ramq='SIML14550999',
            legacy_id=54,
            mrns=mrn_data['Lisa Simpson'],
        )
    else:
        laurie = _create_patient(
            first_name='Laurie',
            last_name='Opal',
            date_of_birth=date(1958, 12, 13),
            sex=SexType.FEMALE,
            ramq='OPAL58621325',
            legacy_id=92,
            mrns=mrn_data['Laurie Opal'],
        )
        rory = _create_patient(
            first_name='Rory',
            last_name="O'Brien",
            date_of_birth=date(1972, 6, 11),
            sex=SexType.OTHER,
            ramq='OBRR72061199',
            legacy_id=59,
            mrns=mrn_data["Rory O'Brien"],
        )
        cara = _create_patient(
            first_name='Cara',
            last_name="O'Brien",
            date_of_birth=date(1974, 11, 25),
            sex=SexType.FEMALE,
            ramq='OBRC11257499',
            legacy_id=96,
            mrns=mrn_data["Cara O'Brien"],
        )
        john = _create_patient(
            first_name='John',
            last_name='Smith',
            date_of_birth=date(1985, 1, 1),
            sex=SexType.MALE,
            ramq='',
            legacy_id=93,
            mrns=mrn_data['John Smith'],
        )
        richard = _create_patient(
            first_name='Richard',
            last_name='Smith',
            date_of_birth=date(1946, 5, 5),
            sex=SexType.MALE,
            ramq='SMIR05054616',
            legacy_id=94,
            mrns=mrn_data['Richard Smith'],
        )
        mike = _create_patient(
            first_name='Mike',
            last_name='Brown',
            date_of_birth=date(1972, 6, 11),
            sex=SexType.MALE,
            ramq='BROM72061199',
            legacy_id=103,
            mrns=mrn_data['Mike Brown'],
        )
        kathy = _create_patient(
            first_name='Kathy',
            last_name='Brown',
            date_of_birth=date(1974, 11, 25),
            sex=SexType.FEMALE,
            ramq='BROK11257499',
            legacy_id=102,
            mrns=mrn_data['Kathy Brown'],
        )
        valerie = _create_patient(
            first_name='Valerie',
            last_name='Solanas',
            date_of_birth=date(1979, 6, 21),
            sex=SexType.MALE,
            ramq='SOLV06217999',
            legacy_id=99,
            mrns=mrn_data['Valerie Solanas'],
        )
        pete = _create_patient(
            first_name='Pete',
            last_name='Boyd',
            date_of_birth=date(1971, 6, 11),
            sex=SexType.MALE,
            ramq='BOYP06117199',
            legacy_id=100,
            mrns=mrn_data['Pete Boyd'],
        )
        martin = _create_patient(
            first_name='Martin',
            last_name='Curley',
            date_of_birth=date(1965, 4, 23),
            sex=SexType.MALE,
            ramq='CURM04236599',
            legacy_id=101,
            mrns=mrn_data['Martin Curley'],
        )

    # caregivers

    if not is_pediatric:
        user_laurie = _create_caregiver(
            first_name='Laurie',
            last_name='Opal',
            username='a51fba18-3810-4808-9238-4d0e487785c8',
            email='laurie@opalmedapps.ca',
            language='en',
            phone_number='',
            legacy_id=6,
        )
        user_rory = _create_caregiver(
            first_name='Rory',
            last_name="O'Brien",
            username='mouj1pqpXrYCl994oSm5wtJT3In2',
            email='rory@opalmedapps.ca',
            language='en',
            phone_number='+15145554321',
            legacy_id=7,
        )
        user_cara = _create_caregiver(
            first_name=cara.first_name,
            last_name=cara.last_name,
            username='dR2Cb1Yf0vQb4ywvMoAXw1SxbY93',
            email='cara@opalmedapps.ca',
            language='en',
            phone_number='',
            legacy_id=999,  # TODO
        )
        user_john = _create_caregiver(
            first_name=john.first_name,
            last_name=john.last_name,
            username='hIMnEXkedPMxYnXeqNXzphklu4V2',
            email='john@opalmedapps.ca',
            language='en',
            phone_number='',
            legacy_id=8,
        )
        user_richard = _create_caregiver(
            first_name=richard.first_name,
            last_name=richard.last_name,
            username='2WhxeTpYF8aHlfSQX8oGeq4LFhw2',
            email='richard@opalmedapps.ca',
            language='en',
            phone_number='',
            legacy_id=998,  # TODO
        )
        user_mike = _create_caregiver(
            first_name=mike.first_name,
            last_name=mike.last_name,
            username='hSJdAae7xWNwnemd2YypQSVfoOb2',
            email='mike@opalmedapps.ca',
            language='en',
            phone_number='',
            legacy_id=997,  # TODO
        )
        user_kathy = _create_caregiver(
            first_name=kathy.first_name,
            last_name=kathy.last_name,
            username='OPWj4Cj5iRfgva4b3HGtVGjvuk13',
            email='kathy@opalmedapps.ca',
            language='en',
            phone_number='',
            legacy_id=996,  # TODO
        )
        user_valerie = _create_caregiver(
            first_name=valerie.first_name,
            last_name=valerie.last_name,
            username='dcBSK5qdoiOM2L9cEdShkqOadkG3',
            email='valerie@opalmedapps.ca',
            language='en',
            phone_number='',
            legacy_id=995,  # TODO
        )
        user_pete = _create_caregiver(
            first_name=pete.first_name,
            last_name=pete.last_name,
            username='9kmS7qYQX8arnFFs4ZYJk1tqLFw1',
            email='pete@opalmedapps.ca',
            language='en',
            phone_number='',
            legacy_id=994,  # TODO
        )
        user_martin = _create_caregiver(
            first_name=martin.first_name,
            last_name=martin.last_name,
            username='2grqcCoyPlVucfAPD4NM1SuCk3i1',
            email='martin@opalmedapps.ca',
            language='en',
            phone_number='',
            legacy_id=993,  # TODO
        )

    # get relationship types
    type_self = RelationshipType.objects.self_type()

    # relationships

    if not is_pediatric:
        # Laurie --> Laurie: Self
        _create_relationship(
            patient=laurie,
            caregiver=user_laurie,
            relationship_type=type_self,
            status=RelationshipStatus.CONFIRMED,
            request_date=_relative_date(today, -14),
            start_date=_relative_date(today, -14),
        )

        # Rory --> Rory: Self
        _create_relationship(
            patient=rory,
            caregiver=user_rory,
            relationship_type=type_self,
            status=RelationshipStatus.CONFIRMED,
            request_date=_relative_date(today, -14),
            start_date=_relative_date(today, -14),
        )

        # Cara --> Cara: Self
        _create_relationship(
            patient=cara,
            caregiver=user_cara,
            relationship_type=type_self,
            status=RelationshipStatus.CONFIRMED,
            request_date=_relative_date(today, -14),  # TBC
            start_date=_relative_date(today, -14),  # TBC
        )

        # Rory --> Cara: Family & Friends
        _create_relationship(
            patient=cara,
            caregiver=user_rory,
            relationship_type=type_family,
            status=RelationshipStatus.CONFIRMED,
            request_date=_relative_date(today, -14),  # TBC
            start_date=_relative_date(today, -14),  # TBC
        )

        # John --> John: Self
        _create_relationship(
            patient=john,
            caregiver=user_john,
            relationship_type=type_self,
            status=RelationshipStatus.CONFIRMED,
            request_date=_relative_date(today, -14),
            start_date=_relative_date(today, -14),
        )

        # Richard --> Richard: Self
        _create_relationship(
            patient=richard,
            caregiver=user_richard,
            relationship_type=type_self,
            status=RelationshipStatus.CONFIRMED,
            request_date=_relative_date(today, -14),  # TBC
            start_date=_relative_date(today, -14),  # TBC
        )

        # John --> Richard: Family & Friends
        _create_relationship(
            patient=richard,
            caregiver=user_john,
            relationship_type=type_family,
            status=RelationshipStatus.CONFIRMED,
            request_date=_relative_date(today, -14),  # TBC
            start_date=_relative_date(today, -14),  # TBC
        )

        # Mike --> Mike: Self
        _create_relationship(
            patient=mike,
            caregiver=user_mike,
            relationship_type=type_self,
            status=RelationshipStatus.CONFIRMED,
            request_date=_relative_date(today, -14),  # TBC
            start_date=_relative_date(today, -14),  # TBC
        )

        # Kathy --> Kathy: Self
        _create_relationship(
            patient=kathy,
            caregiver=user_kathy,
            relationship_type=type_self,
            status=RelationshipStatus.CONFIRMED,
            request_date=_relative_date(today, -14),  # TBC
            start_date=_relative_date(today, -14),  # TBC
        )

        # Mike --> Kathy: Family & Friends
        _create_relationship(
            patient=kathy,
            caregiver=user_mike,
            relationship_type=type_family,
            status=RelationshipStatus.CONFIRMED,
            request_date=_relative_date(today, -14),  # TBC
            start_date=_relative_date(today, -14),  # TBC
        )

        # Valerie --> Valerie: Self
        _create_relationship(
            patient=valerie,
            caregiver=user_valerie,
            relationship_type=type_self,
            status=RelationshipStatus.CONFIRMED,
            request_date=_relative_date(today, -14),  # TBC
            start_date=_relative_date(today, -14),  # TBC
        )

        # Pete --> Pete: Self
        _create_relationship(
            patient=pete,
            caregiver=user_pete,
            relationship_type=type_self,
            status=RelationshipStatus.CONFIRMED,
            request_date=_relative_date(today, -14),  # TBC
            start_date=_relative_date(today, -14),  # TBC
        )

        # Martin --> Martin: Self
        _create_relationship(
            patient=martin,
            caregiver=user_martin,
            relationship_type=type_self,
            status=RelationshipStatus.CONFIRMED,
            request_date=_relative_date(today, -14),  # TBC
            start_date=_relative_date(today, -14),  # TBC
        )

    # The rest of the relationships exist at both institutions
    # To be added if necessary

    # create the same security question and answers for the caregivers
    if not is_pediatric:
        _create_security_answers(user_laurie)
        _create_security_answers(user_rory)
        _create_security_answers(user_cara)
        _create_security_answers(user_john)
        _create_security_answers(user_richard)
        _create_security_answers(user_mike)
        _create_security_answers(user_kathy)
        _create_security_answers(user_valerie)
        _create_security_answers(user_pete)
        _create_security_answers(user_martin)

    # Pathology reports for patients
    # Pathology reports are currently not intended to be rolled out at Sainte-Justine which is a pediatric hospital
    if not is_pediatric:
        # Create a fake pathology for laurie as well to complete her dataset
        # Laurie received her pathology 15 days ago
        _create_pathology_result(
            patient=laurie,
            site=sites['ODH'],
            collected_at=timezone.now() - relativedelta(years=6, months=0, days=15),
            received_at=timezone.now() - relativedelta(years=6, months=0, days=15),
            reported_at=timezone.now() - relativedelta(years=6, months=0, days=15),
            legacy_document_id=31,
        )


def create_institution(institution_option: InstitutionOption) -> Institution:
    """
    Create, validate and save an institution instance with the given properties.

    The logo and terms of use are loaded from the file system under `files/` within the directory of this module.

    Args:
        institution_option: the chosen institution for which the test data should be inserted

    Returns:
        the newly created institution
    """
    institution_directory = DIRECTORY_FILES.joinpath(institution_option.name)
    data = INSTITUTION_DATA[institution_option]

    logo_path = institution_directory.joinpath('logo.png')
    with logo_path.open('rb') as logo_file:
        logo = ContentFile(logo_file.read(), logo_path.name)

    terms_path_en = institution_directory.joinpath('terms_of_use_en.pdf')
    with terms_path_en.open('rb') as terms_file_en:
        terms_of_use_en = ContentFile(terms_file_en.read(), terms_path_en.name)

    terms_path_fr = institution_directory.joinpath('terms_of_use_fr.pdf')
    with terms_path_fr.open('rb') as terms_file_fr:
        terms_of_use_fr = ContentFile(terms_file_fr.read(), terms_path_fr.name)

    institution = Institution(
        name=data['name'],
        name_fr=data['name_fr'],
        acronym_fr=data['acronym_fr'],
        acronym=institution_option.value,
        support_email=data['support_email'],
        terms_of_use=terms_of_use_en,
        terms_of_use_fr=terms_of_use_fr,
        logo=logo,
        logo_fr=logo,
    )
    institution.full_clean()
    institution.save()

    return institution


def create_sites(institution_option: InstitutionOption, institution: Institution) -> dict[str, Site]:
    """
    Create sites according to the definition of the `SITE_DATA` constant for the chosen institution.

    Args:
        institution_option: the institution for which to create sites for
        institution: the institution instance

    Returns:
        a mapping from site acronym to `Site` instance
    """
    result: dict[str, Site] = {}

    for site_data in SITE_DATA[institution_option]:
        site = _create_site(institution, *site_data)
        result[site_data[2]] = site

    return result


def _create_site(  # noqa: PLR0913, PLR0917
    institution: Institution,
    name: str,
    name_fr: str,
    acronym: str,
    acronym_fr: str,
    parking_urls: tuple[str, str],
    direction_urls: tuple[str, str],
    latitude: Decimal,
    longitude: Decimal,
    address: tuple[str, str, str, str, str, str, str],
) -> Site:
    """
    Create, validate and save a site instance with the given properties.

    Args:
        institution: the institution instance the site belongs to
        name: the English name of the site
        name_fr: the French name of the site
        acronym: the acronym of the institution
        acronym_fr: the French acronym of the institution
        parking_urls: a tuple of URLs to the English and French parking information
        direction_urls: a tuple of URLs to the English and French direction to the hospital information
        latitude: the latitude of the GPS location of the site
        longitude: the longitude of the GPS location of the site
        address: a tuple of the address information of the site

    Returns:
        the newly created site
    """
    site = Site(
        institution=institution,
        name=name,
        name_fr=name_fr,
        acronym=acronym,
        acronym_fr=acronym_fr,
        parking_url=parking_urls[0],
        parking_url_fr=parking_urls[1],
        direction_url=direction_urls[0],
        direction_url_fr=direction_urls[1],
        latitude=latitude,
        longitude=longitude,
        street_name=address[0],
        street_number=address[1],
        postal_code=address[2],
        city=address[3],
        province_code=address[4],
        contact_telephone=address[5],
        contact_fax=address[6],
    )

    site.full_clean()
    site.save()

    return site


def _create_patient(  # noqa: PLR0913, PLR0917
    first_name: str,
    last_name: str,
    date_of_birth: date,
    sex: SexType,
    ramq: str,
    legacy_id: int,
    mrns: list[tuple[Site, str]],
    date_of_death: date | None = None,
    data_access: DataAccessType = DataAccessType.ALL,
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
        data_access: the data access level the patient has

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
        data_access=data_access,
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


def _create_caregiver(  # noqa: PLR0913, PLR0917
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

    # User passwords aren't currently saved in Django
    user.set_unusable_password()
    user.full_clean()
    user.save()

    profile = CaregiverProfile(
        user=user,
        legacy_id=legacy_id,
    )

    profile.full_clean()
    profile.save()

    return profile


def _create_relationship(  # noqa: PLR0913, PLR0917
    patient: Patient,
    caregiver: CaregiverProfile,
    relationship_type: RelationshipType,
    status: RelationshipStatus,
    request_date: date,
    start_date: date,
    end_date: date | None = None,
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
        else 'Quel est le nom de votre premier animal de compagnie?'
    )
    question2 = (
        'What was the name of your favorite superhero as a child?'
        if language == 'en'
        else 'Quel était le nom de votre super-héros préféré durant votre enfance?'
    )
    question3 = (
        'What was the color of your first car?'
        if language == 'en'
        else 'Quelle était la couleur de votre première voiture?'
    )
    _create_security_answer(
        caregiver,
        question1,
        hashlib.sha512(b'meg').hexdigest(),
    )
    _create_security_answer(
        caregiver,
        question2,
        hashlib.sha512(b'superman').hexdigest(),
    )
    _create_security_answer(
        caregiver,
        question3,
        hashlib.sha512(b'red').hexdigest(),
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
    current_year = timezone.now().year

    # is the current date before the birth date
    # if so, to have the correct age, we need to add an extra year
    before_birth_date = timezone.now().date() < date(current_year, month, day)
    relative_years += before_birth_date

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


def _create_pathology_result(  # noqa: PLR0913, PLR0917
    patient: Patient,
    site: Site,
    collected_at: datetime,
    received_at: datetime,
    reported_at: datetime,
    legacy_document_id: int,
) -> None:
    """
    Generate a Test Result instance for a patient and site.

    Args:
        patient: subject patient described in the pathology report
        site: facility where the sample was collected and pathology report was generated
        collected_at: datetime of biopsy
        received_at: datetime of sample received by pathologist
        reported_at: datetime of report
        legacy_document_id: OpalDB.Document entry serial number
    """
    general_test = GeneralTest(
        patient=patient,
        type=TestType.PATHOLOGY,
        sending_facility=site.acronym,
        receiving_facility=site.acronym,
        collected_at=collected_at,
        received_at=received_at,
        reported_at=reported_at,
        message_type='ORU',
        message_event='R01',
        test_group_code='RQSTPTISS',
        test_group_code_description='Request Pathology Tissue',
        legacy_document_id=legacy_document_id,
    )

    general_test.full_clean()
    general_test.save()

    specimen_observation = PathologyObservation(
        general_test=general_test,
        identifier_code='SPSPECI',
        identifier_text='SPECIMEN',
        value='Aliquam tincidunt mauris eu risus.',
        observed_at=collected_at,
    )
    specimen_observation.full_clean()
    specimen_observation.save()

    note = Note(
        general_test=general_test,
        note_source='Signature Line',
        note_text='Morbi in sem quis dui placerat ornare.',
    )

    note.full_clean()
    note.save()
