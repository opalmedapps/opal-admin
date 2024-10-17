import datetime
import textwrap
from pathlib import Path

import pytest
from pytest_django.fixtures import SettingsWrapper

from opal.services.reports.base import InstitutionData, PatientData, SiteData
from opal.services.reports.pathology import PathologyData, PathologyPDF, generate_pdf

observation_clinical_info = """Left breast mass at 3 o'clock (previously collagenous stroma,
 discordant with imaging).\nRebiopsy under ultrasound was done today."""
observation_specimens = "LEFT BREAST AT 3 O'CLOCK, BIOPSY:"
observation_descriptions = """The specimen is received in formalin in 1 container labelled
 with patient's name. It consists of fragments of core needle biopsy tissue measuring
 0.5 to 2.0 cm in length. The specimen is submitted in toto in cassettes A1 and A2.\n
Time to fixation: 0\nTotal time of fixation: 9h 5m"""
observation_diagnosis = """LEFT BREAST AT 3 O'CLOCK, BIOPSY\n - BENIGN BREAST TISSUE
 WITH DENSE COLLAGENOUS STROMA AND ADENOSIS.\n - CALCIFICATIONS PRESENT\nCODE 1
"""

PATHOLOGY_REPORT_DATA_WITH_PAGE_BREAK = PathologyData(
    test_number='AS-2021-62605',
    test_collected_at=datetime.datetime(2021, 11, 25, 9, 55),
    test_reported_at=datetime.datetime(2021, 11, 28, 11, 52),
    observation_clinical_info=[observation_clinical_info],
    observation_specimens=[observation_specimens],
    observation_descriptions=[
        observation_descriptions,
        observation_descriptions,
        observation_descriptions,
        observation_descriptions,
        observation_descriptions,
        observation_descriptions,
    ],
    observation_diagnosis=[observation_diagnosis],
    prepared_by='Atilla Omeroglu, MD',
    prepared_at=datetime.datetime(2021, 12, 29, 10, 30),
)

PATHOLOGY_REPORT_DATA_WITH_NO_PAGE_BREAK = PathologyData(
    test_number='AS-2021-62605',
    test_collected_at=datetime.datetime(2021, 11, 25, 9, 55),
    test_reported_at=datetime.datetime(2021, 11, 28, 11, 52),
    observation_clinical_info=['Clinical Information', 'Clinical Information'],
    observation_specimens=['Specimen', 'Specimen', 'Specimen', 'Specimen'],
    observation_descriptions=['Gross Description', 'Gross Description', 'Gross Description'],
    observation_diagnosis=['Diagnosis'],
    prepared_by='Atilla Omeroglu, MD',
    prepared_at=datetime.datetime(2021, 12, 29, 10, 30),
)
INSTITUTION_REPORT_DATA_WITH_NO_PAGE_BREAK = InstitutionData(
    institution_logo_path=Path('opal/tests/fixtures/test_logo.png'),
)
PATIENT_REPORT_DATA_WITH_NO_PAGE_BREAK = PatientData(
    patient_first_name='Bart',
    patient_last_name='Simpson',
    patient_date_of_birth=datetime.date(1999, 1, 1),
    patient_ramq='SIMM99999999',
    patient_sites_and_mrns=[
        {'mrn': '22222443', 'site_code': 'MGH'},
        {'mrn': '1111728', 'site_code': 'RVH'},
    ],
)
SITE_REPORT_DATA_WITH_NO_PAGE_BREAK = SiteData(
    site_name='Decarie Boulevard',
    site_building_address='1001',
    site_city='Montreal',
    site_province='QC',
    site_postal_code='H4A3J1',
    site_phone='5149341934',
)


def test_generate_pathology_report_success_with_no_page_break(
    tmp_path: Path,
    settings: SettingsWrapper,
) -> None:
    """Ensure generate_pathology_report() method successfully generates a pathology report."""
    settings.PATHOLOGY_REPORTS_PATH = tmp_path

    # Generate the pathology report
    pathology_report = generate_pdf(
        institution_data=INSTITUTION_REPORT_DATA_WITH_NO_PAGE_BREAK,
        patient_data=PATIENT_REPORT_DATA_WITH_NO_PAGE_BREAK,
        site_data=SITE_REPORT_DATA_WITH_NO_PAGE_BREAK,
        pathology_data=PATHOLOGY_REPORT_DATA_WITH_NO_PAGE_BREAK,
    )

    assert pathology_report.parent == settings.PATHOLOGY_REPORTS_PATH
    assert pathology_report.exists()
    assert pathology_report.is_file()


INSTITUTION_REPORT_DATA_WITH_PAGE_BREAK = InstitutionData(
    institution_logo_path=Path('opal/tests/fixtures/test_logo.png'),
)
SITE_REPORT_DATA_WITH_PAGE_BREAK = SiteData(
    site_name='Decarie Boulevard',
    site_building_address='1001',
    site_city='Montreal',
    site_province='QC',
    site_postal_code='H4A3J1',
    site_phone='5149341934',
)
PATIENT_REPORT_DATA_WITH_PAGE_BREAK = PatientData(
    patient_first_name='Bart',
    patient_last_name='Simpson',
    patient_date_of_birth=datetime.date(1999, 1, 1),
    patient_ramq='SIMM99999999',
    patient_sites_and_mrns=[
        {'mrn': '22222443', 'site_code': 'MGH'},
        {'mrn': '1111728', 'site_code': 'RVH'},
    ],
)


def test_generate_pathology_report_success_with_page_break(
    tmp_path: Path,
    settings: SettingsWrapper,
) -> None:
    """Ensure generate_pathology_report() method successfully generates a pathology report with a page break."""
    settings.PATHOLOGY_REPORTS_PATH = tmp_path

    # Generate the pathology report
    pathology_report = generate_pdf(
        institution_data=INSTITUTION_REPORT_DATA_WITH_PAGE_BREAK,
        patient_data=PATIENT_REPORT_DATA_WITH_PAGE_BREAK,
        site_data=SITE_REPORT_DATA_WITH_PAGE_BREAK,
        pathology_data=PATHOLOGY_REPORT_DATA_WITH_PAGE_BREAK,
    )

    assert pathology_report.parent == settings.PATHOLOGY_REPORTS_PATH
    assert pathology_report.exists()
    assert pathology_report.is_file()


test_patient_names_data: list[tuple[str, str]] = [
    ('Gertruda', 'Evaristo'),
    ('Jean', 'Phillipe The Third of Canterbury'),
    ('Jean-Phillipe-Burgundy-Long-First-Name', 'Jean-Phillipe-Burgundy-Long-Last-Name'),
    ('Timothy John', 'Berners-Lee'),
    ('Leonardo di ser', 'Piero da Vinci'),
]


@pytest.mark.parametrize(('first_name', 'last_name'), test_patient_names_data)
def test_long_patient_names_not_splitted(first_name: str, last_name: str) -> None:
    """Ensure long patient names are formatted and no words splitted."""
    pathology_data = PATHOLOGY_REPORT_DATA_WITH_NO_PAGE_BREAK

    institution_data = INSTITUTION_REPORT_DATA_WITH_NO_PAGE_BREAK

    site_data = SITE_REPORT_DATA_WITH_NO_PAGE_BREAK

    patient_data = PATIENT_REPORT_DATA_WITH_NO_PAGE_BREAK._replace(
        patient_first_name=first_name,
        patient_last_name=last_name,
    )
    pathology_pdf = PathologyPDF(institution_data, patient_data, site_data, pathology_data)

    patient_list = pathology_pdf._get_site_address_patient_info_box()

    patient_info = next(elem for elem in patient_list if elem.get('name') == 'patient_name')
    # Wrap the text with the maximum characters can be filled in each line.
    wrapper = textwrap.TextWrapper(
        width=int((185 - 110) / 2) - 1,
    )
    patient_name = f'{last_name}, {first_name}'.upper()
    expected_patient_name = wrapper.fill(text=f'Nom/Name: {patient_name}')

    assert patient_info.get('text') == expected_patient_name
