"""Management command for inserting test data."""
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from pathlib import Path
from types import MappingProxyType
from typing import Any, Optional

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandParser
from django.db import transaction
from django.utils import timezone

from dateutil.relativedelta import relativedelta

from opal.caregivers.models import CaregiverProfile, SecurityAnswer
from opal.hospital_settings.models import Institution, Site
from opal.patients.models import HospitalPatient, Patient, Relationship, RelationshipStatus, RelationshipType
from opal.test_results.models import GeneralTest, Note, PathologyObservation, TestType
from opal.users.models import Caregiver

DIRECTORY_FILES = Path('opal/core/management/commands/files')
PARKING_URLS_MUHC = ('https://muhc.ca/patient-and-visitor-parking', 'https://cusm.ca/stationnement')
TRAVEL_URLS_CRE = (
    'https://live-cbhssjb.pantheonsite.io/cps/travelling',
    'https://live-cbhssjb.pantheonsite.io/fr/cps/voyager',
)


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
        'name': 'Opal Medical Institution',
        'name_fr': 'Établissement Médical Opal',
        'acronym_fr': 'ÉMO',
        'support_email': 'opal@muhc.mcgill.ca',
    },
    InstitutionOption.ohigph: {
        'name': 'OHIG Pediatric Hospital',
        'name_fr': 'Hôpital Pédiatrique OHIG',
        'acronym_fr': 'HPOHIG',
        'support_email': 'opal+chusj@muhc.mcgill.ca',
    },
})

SITE_DATA = MappingProxyType({
    InstitutionOption.omi: [
        (
            'Opal General Hospital 1 (RVH)',
            'Hôpital général Opal 1 (HRV)',
            'RVH',
            'HRV',
            PARKING_URLS_MUHC,
            ('https://muhc.ca/getting-glen-site', 'https://cusm.ca/se-rendre-au-site-glen'),
            Decimal('45.473435'),
            Decimal('-73.601611'),
            ('Decarie Boulevard', '1001', 'H4A3J1', 'Montréal', 'QC', '5149341934', ''),
        ),
        (
            'Opal General Hospital 2 (MGH)',
            'Hôpital général Opal 2 (HGM)',
            'MGH',
            'HGM',
            PARKING_URLS_MUHC,
            (
                'https://muhc.ca/how-get-montreal-general-hospital',
                'https://cusm.ca/se-rendre-lhopital-general-de-montreal',
            ),
            Decimal('45.496828'),
            Decimal('-73.588782'),
            ('Cedar Avenue', '1650', 'H3G1A4', 'Montréal', 'QC', '5149341934', ''),
        ),
        (
            'Opal Childrens Hospital',
            "L'Hôpital Opal pour enfants",
            'MCH',
            'HME',
            PARKING_URLS_MUHC,
            ('https://www.thechildren.com/getting-hospital', 'https://www.hopitalpourenfants.com/se-rendre-lhopital'),
            Decimal('45.473343'),
            Decimal('-73.600802'),
            ('Decarie Boulevard', '1001', 'H4A3J1', 'Montréal', 'QC', '5144124400', ''),
        ),
        (
            'Opal General Hospital 3 (LAC)',
            'Hôpital général Opal 3 (LAC)',
            'LAC',
            'LAC',
            PARKING_URLS_MUHC,
            ('https://muhc.ca/how-get-lachine-hospital', 'https://cusm.ca/se-rendre-lhopital-de-lachine'),
            Decimal('45.44121'),
            Decimal('-73.676791'),
            ('16e Avenue', '650', 'H8S3N5', 'Lachine', 'QC', '5149341934', ''),
        ),
        (
            'Opal General Hospital 4 (CRE)',
            'Hôpital général Opal 4 (CRE)',
            'CRE',
            'CRE',
            TRAVEL_URLS_CRE,
            TRAVEL_URLS_CRE,
            Decimal('45.51640'),
            Decimal('-73.55529'),
            ('Boulevard René-Lévesque', '1055', 'H2L4S5', 'Montréal', 'QC', '5148615955', ''),
        ),
    ],
    InstitutionOption.ohigph: [
        (
            'OHIG Pediatric Hospital',
            'Hôpital Pédiatrique OHIG',
            'CHUSJ',
            'CHUSJ',
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
        'Marge Simpson': [('RVH', '9999996')],
        'Homer Simpson': [
            ('RVH', '9999997'),
            ('MGH', '9999998'),
        ],
        'Bart Simpson': [('MCH', '9999996')],
        'Mona Simpson': [
            ('RVH', '9999993'),
            ('MCH', '5407383'),
        ],
        'Fred Flintstone': [('RVH', '9999998')],
        'Pebbles Flintstone': [('MCH', '9999999')],
        'Wednesday Addams': [('RVH', '9999991')],
    },
    InstitutionOption.ohigph: {
        'Bart Simpson': [('CHUSJ', '9999996')],
        'Lisa Simpson': [('CHUSJ', '9999993')],
    },
})


class Command(BaseCommand):
    """
    Command for inserting test data.

    Inserts an institution, sites, patients, caregivers and relationships between the patients and caregivers.
    """

    help = 'Insert data for testing purposes. Data includes patients, caregivers, relationships.'  # noqa: A003

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
    Patient.objects.all().delete()
    # also deletes security answers
    CaregiverProfile.objects.all().delete()
    Caregiver.objects.all().delete()
    # also deletes Sites
    Institution.objects.all().delete()
    Note.objects.all().delete()
    PathologyObservation.objects.all().delete()
    GeneralTest.objects.all().delete()


def _create_test_data(institution_option: InstitutionOption) -> None:  # noqa: C901
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
    today = date.today()

    # hospital settings
    institution = create_institution(institution_option)
    sites = create_sites(institution_option, institution)

    mrn_data: dict[str, list[tuple[Site, str]]] = {}  # noqa: WPS234

    for key, value in MRN_DATA[institution_option].items():
        new_value = [(sites[site], mrn) for site, mrn in value]
        mrn_data[key] = new_value

    is_pediatric = institution_option == InstitutionOption.ohigph

    # patients
    if is_pediatric:
        lisa = _create_patient(
            first_name='Lisa',
            last_name='Simpson',
            date_of_birth=_create_date(8, 5, 9),
            sex=Patient.SexType.FEMALE,
            ramq='SIML14550999',
            legacy_id=54,
            mrns=mrn_data['Lisa Simpson'],
        )
    else:
        marge = _create_patient(
            first_name='Marge',
            last_name='Simpson',
            date_of_birth=_create_date(36, 10, 1),
            sex=Patient.SexType.FEMALE,
            ramq='SIMM86600199',
            legacy_id=51,
            mrns=mrn_data['Marge Simpson'],
        )

        homer = _create_patient(
            first_name='Homer',
            last_name='Simpson',
            date_of_birth=_create_date(39, 5, 12),
            sex=Patient.SexType.MALE,
            ramq='SIMH83051299',
            legacy_id=52,
            mrns=mrn_data['Homer Simpson'],
        )

        mona = _create_patient(
            first_name='Mona',
            last_name='Simpson',
            date_of_birth=date(1940, 3, 15),
            sex=Patient.SexType.FEMALE,
            ramq='SIMM40531599',
            legacy_id=55,
            mrns=mrn_data['Mona Simpson'],
            date_of_death=_relative_date(today, -2),
        )

        fred = _create_patient(
            first_name='Fred',
            last_name='Flintstone',
            date_of_birth=date(1960, 8, 1),
            sex=Patient.SexType.MALE,
            ramq='FLIF60080199',
            legacy_id=56,
            mrns=mrn_data['Fred Flintstone'],
        )

        pebbles = _create_patient(
            first_name='Pebbles',
            last_name='Flintstone',
            date_of_birth=_create_date(9, 2, 1),
            sex=Patient.SexType.FEMALE,
            ramq='FLIP15022299',
            legacy_id=57,
            mrns=mrn_data['Pebbles Flintstone'],
        )
        wednesday = _create_patient(
            first_name='Wednesday',
            last_name='Addams',
            date_of_birth=date(2009, 2, 13),
            sex=Patient.SexType.FEMALE,
            ramq='ADAW09021399',
            legacy_id=58,
            mrns=mrn_data['Wednesday Addams'],
        )

    # Bart exists at both institutions
    bart = _create_patient(
        first_name='Bart',
        last_name='Simpson',
        date_of_birth=_create_date(14, 2, 23),
        sex=Patient.SexType.MALE,
        ramq='SIMB13022399',
        legacy_id=53,
        mrns=mrn_data['Bart Simpson'],
    )

    # caregivers
    user_marge = _create_caregiver(
        # hard-coded name since the patient Marge might not exist
        first_name='Marge',
        last_name='Simpson',
        username='QXmz5ANVN3Qp9ktMlqm2tJ2YYBz2',
        email='marge@opalmedapps.ca',
        language='en',
        phone_number='+15551234567',
        legacy_id=1,
    )

    user_bart = _create_caregiver(
        first_name=bart.first_name,
        last_name=bart.last_name,
        username='SipDLZCcOyTYj7O3C8HnWLalb4G3',
        email='bart@opalmedapps.ca',
        language='en',
        phone_number='+498999998123',
        legacy_id=3,
    )

    if not is_pediatric:
        user_homer = _create_caregiver(
            first_name=homer.first_name,
            last_name=homer.last_name,
            username='PyKlcbRpMLVm8lVnuopFnFOHO4B3',
            email='homer@opalmedapps.ca',
            language='en',
            phone_number='+15557654321',
            legacy_id=2,
            # homer is blocked: he lost access due to him being unstable
            is_active=False,
        )

        user_mona = _create_caregiver(
            first_name=mona.first_name,
            last_name=mona.last_name,
            username='61DXBRwLCmPxlaUoX6M1MP9DiEl1',
            email='mona@opalmedapps.ca',
            language='en',
            phone_number='+15144758941',
            legacy_id=4,
            is_active=False,
        )

        user_fred = _create_caregiver(
            first_name='Fred',
            last_name='Flintstone',
            username='ZYHAjhNy6hhr4tOW8nFaVEeKngt1',
            email='fred@opalmedapps.ca',
            language='en',
            phone_number='+15144758941',
            legacy_id=5,
        )

    # get relationship types
    type_self = RelationshipType.objects.self_type()
    type_parent = RelationshipType.objects.parent_guardian()
    type_caregiver = RelationshipType.objects.guardian_caregiver()
    type_mandatary = RelationshipType.objects.mandatary()

    # relationships
    date_bart_fourteen = _relative_date(bart.date_of_birth, 14)

    if is_pediatric:
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
    else:
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
            status=RelationshipStatus.CONFIRMED,
            request_date=_relative_date(today, -10),
            start_date=_relative_date(today, -12),
            end_date=_relative_date(today, -1),
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

        # Marge --> Bart: Guardian/Parent
        _create_relationship(
            patient=bart,
            caregiver=user_marge,
            relationship_type=type_parent,
            status=RelationshipStatus.EXPIRED,
            request_date=_relative_date(today, -9),
            start_date=bart.date_of_birth,
            end_date=date_bart_fourteen,
        )

        # Fred --> Fred: Self
        _create_relationship(
            patient=fred,
            caregiver=user_fred,
            relationship_type=type_self,
            status=RelationshipStatus.CONFIRMED,
            request_date=_relative_date(today, -2),
            start_date=_relative_date(today, -8),
        )

        # Fred --> Pebbles: Guardian/Parent
        _create_relationship(
            patient=pebbles,
            caregiver=user_fred,
            relationship_type=type_parent,
            status=RelationshipStatus.CONFIRMED,
            request_date=_relative_date(today, -1),
            start_date=_relative_date(today, -3),
            end_date=_relative_date(pebbles.date_of_birth, 14),
        )

    # The rest of the relationships exist at both institutions

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

    # Bart --> Bart
    _create_relationship(
        patient=bart,
        caregiver=user_bart,
        relationship_type=type_self,
        status=RelationshipStatus.CONFIRMED,
        request_date=date_bart_fourteen,
        start_date=date_bart_fourteen,
    )

    # create the same security question and answers for the caregivers
    if not is_pediatric:
        _create_security_answers(user_homer)
        _create_security_answers(user_fred)

    _create_security_answers(user_marge)
    _create_security_answers(user_bart)

    # Pathology reports for Marge, Bart, Homer, Fred, Pebbles, and Wednesday
    # Pathology reports are currently not intended to be rolled out at Sainte-Justine which is a pediatric hospital
    if not is_pediatric:
        # Marge has 2 pathology reports received 2 and 12 days ago respectively
        _create_pathology_result(
            patient=marge,
            site=sites['RVH'],
            collected_at=timezone.make_aware(
                datetime.now() - relativedelta(years=0, months=0, days=2),
            ),
            received_at=timezone.make_aware(
                datetime.now() - relativedelta(years=0, months=0, days=2),
            ),
            reported_at=timezone.make_aware(
                datetime.now() - relativedelta(years=0, months=0, days=2),
            ),
            legacy_document_id=7,
        )
        _create_pathology_result(
            patient=marge,
            site=sites['RVH'],
            collected_at=timezone.make_aware(
                datetime.now() - relativedelta(years=0, months=0, days=12),
            ),
            received_at=timezone.make_aware(
                datetime.now() - relativedelta(years=0, months=0, days=12),
            ),
            reported_at=timezone.make_aware(
                datetime.now() - relativedelta(years=0, months=0, days=12),
            ),
            legacy_document_id=8,
        )
        # Homer received his pathology 8 days ago
        _create_pathology_result(
            patient=homer,
            site=sites['MGH'],
            collected_at=timezone.make_aware(
                datetime.now() - relativedelta(years=0, months=0, days=8),
            ),
            received_at=timezone.make_aware(
                datetime.now() - relativedelta(years=0, months=0, days=8),
            ),
            reported_at=timezone.make_aware(
                datetime.now() - relativedelta(years=0, months=0, days=8),
            ),
            legacy_document_id=6,
        )
        # Fred received his pathology 4 days ago
        _create_pathology_result(
            patient=fred,
            site=sites['RVH'],
            collected_at=timezone.make_aware(
                datetime.now() - relativedelta(years=0, months=0, days=4),
            ),
            received_at=timezone.make_aware(
                datetime.now() - relativedelta(years=0, months=0, days=4),
            ),
            reported_at=timezone.make_aware(
                datetime.now() - relativedelta(years=0, months=0, days=4),
            ),
            legacy_document_id=12,
        )
        # Bart received his pathology 5 days ago
        _create_pathology_result(
            patient=bart,
            site=sites['MCH'],
            collected_at=timezone.make_aware(
                datetime.now() - relativedelta(years=0, months=0, days=5),
            ),
            received_at=timezone.make_aware(
                datetime.now() - relativedelta(years=0, months=0, days=5),
            ),
            reported_at=timezone.make_aware(
                datetime.now() - relativedelta(years=0, months=0, days=5),
            ),
            legacy_document_id=5,
        )
        # Pebbles received her pathology 4 days ago
        _create_pathology_result(
            patient=pebbles,
            site=sites['MCH'],
            collected_at=timezone.make_aware(
                datetime.now() - relativedelta(years=0, months=0, days=4),
            ),
            received_at=timezone.make_aware(
                datetime.now() - relativedelta(years=0, months=0, days=4),
            ),
            reported_at=timezone.make_aware(
                datetime.now() - relativedelta(years=0, months=0, days=4),
            ),
            legacy_document_id=13,
        )
        # Wednesday received her pathology 15 days ago
        _create_pathology_result(
            patient=wednesday,
            site=sites['RVH'],
            collected_at=timezone.make_aware(
                datetime.now() - relativedelta(years=0, months=0, days=15),
            ),
            received_at=timezone.make_aware(
                datetime.now() - relativedelta(years=0, months=0, days=15),
            ),
            reported_at=timezone.make_aware(
                datetime.now() - relativedelta(years=0, months=0, days=15),
            ),
            legacy_document_id=16,
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


def _create_site(
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
        'What was the color of your first car?'
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

    # is the current date before the birth date
    # if so, to have the correct age, we need to add an extra year
    before_birth_date = date.today() < date(current_year, month, day)
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


def _create_pathology_result(
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
