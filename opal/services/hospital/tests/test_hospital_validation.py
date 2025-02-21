# SPDX-FileCopyrightText: Copyright (C) 2022 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from types import MappingProxyType

from django.utils import timezone

from opal.services.hospital.hospital_data import SourceSystemReportExportData
from opal.services.hospital.hospital_validation import SourceSystemValidator

BASE64_ENCODED_REPORT = 'T1BBTCBURVNUIEdFTkVSQVRFRCBSRVBPUlQgUERG'
DOCUMENT_NUMBER = 'FMU-8624'
MRN = '9999996'
SITE_CODE = 'MUHC'

SOURCE_SYSTEM_PATIENT_DATA = MappingProxyType({
    'dateOfBirth': '1953-01-01',
    'firstName': 'SANDRA',
    'lastName': 'TESTMUSEMGHPROD',
    'sex': 'F',
    'alias': '',
    'ramq': 'TESS53510111',
    'ramqExpiration': '201801',
    'mrns': [
        {
            'site': 'MGH',
            'mrn': '9999993',
            'active': True,
        },
    ],
})

source_system_validator = SourceSystemValidator()


# is_report_export_request_valid

def test_is_report_export_request_valid_success() -> None:
    """Ensure `SourceSystemReportExportData` successfully validates."""
    report_data = SourceSystemReportExportData(
        mrn=MRN,
        site=SITE_CODE,
        base64_content=BASE64_ENCODED_REPORT,
        document_number=DOCUMENT_NUMBER,
        document_date=timezone.now(),
    )

    assert source_system_validator.is_report_export_request_valid(report_data)


def test_is_report_export_request_invalid_mrn() -> None:
    """Ensure `SourceSystemReportExportData` with invalid MRN are handled and does not result in an error."""
    report_data = SourceSystemReportExportData(
        mrn='',
        site=SITE_CODE,
        base64_content=BASE64_ENCODED_REPORT,
        document_number=DOCUMENT_NUMBER,
        document_date=timezone.now(),
    )

    assert source_system_validator.is_report_export_request_valid(report_data) is False


def test_is_report_export_request_invalid_site() -> None:
    """Ensure `SourceSystemReportExportData` with invalid site are handled and does not result in an error."""
    report_data = SourceSystemReportExportData(
        mrn=MRN,
        site='',
        base64_content=BASE64_ENCODED_REPORT,
        document_number=DOCUMENT_NUMBER,
        document_date=timezone.now(),
    )

    assert source_system_validator.is_report_export_request_valid(report_data) is False


def test_is_report_export_request_invalid_content() -> None:
    """Ensure `SourceSystemReportExportData` with invalid base64 content are handled and does not result in an error."""
    report_data = SourceSystemReportExportData(
        mrn=MRN,
        site=SITE_CODE,
        base64_content='INVALID CONTENT',
        document_number=DOCUMENT_NUMBER,
        document_date=timezone.now(),
    )

    assert source_system_validator.is_report_export_request_valid(report_data) is False


def test_is_report_export_request_invalid_doctype() -> None:
    """Ensure `SourceSystemReportExportData` with invalid document type are handled and does not result in an error."""
    report_data = SourceSystemReportExportData(
        mrn=MRN,
        site=SITE_CODE,
        base64_content=BASE64_ENCODED_REPORT,
        document_number='FU-INVALID DOCUMENT TYPE',
        document_date=timezone.now(),
    )

    assert source_system_validator.is_report_export_request_valid(report_data) is False


# is_report_export_response_valid

def test_is_report_export_response_valid_success() -> None:
    """Ensure report export response data successfully validates."""
    assert source_system_validator.is_report_export_response_valid({'status': 'success'}) is True
    assert source_system_validator.is_report_export_response_valid({'status': 'error'}) is True


def test_is_report_export_response_invalid() -> None:
    """Ensure that report export invalid response data are handled and do not result in an error."""
    assert source_system_validator.is_report_export_response_valid({'invalid': 'invalid'}) is False
    assert source_system_validator.is_report_export_response_valid({'invalid': 'success'}) is False
    assert source_system_validator.is_report_export_response_valid({'invalid': 'error'}) is False
    assert source_system_validator.is_report_export_response_valid({}) is False


def test_is_report_export_response_invalid_type() -> None:
    """Ensure that report export invalid response data type is handled and does not result in an error."""
    assert source_system_validator.is_report_export_response_valid({'status': {}}) is False
    assert source_system_validator.is_report_export_response_valid(None) is False
    assert source_system_validator.is_report_export_response_valid('test string') is False
    assert source_system_validator.is_report_export_response_valid(123) is False
    assert source_system_validator.is_report_export_response_valid({'status': {'success'}}) is False


# is_patient_response_valid

def test_is_patient_response_valid_success() -> None:
    """Ensure patient response valid success."""
    errors = source_system_validator.is_patient_response_valid({
        'status': 'success',
        'data': SOURCE_SYSTEM_PATIENT_DATA,
    })

    assert not errors


def test_patient_response_status_non_exists() -> None:
    """Ensure patient response data non-existent status return error message."""
    errors = source_system_validator.is_patient_response_valid({
        'data': SOURCE_SYSTEM_PATIENT_DATA,
    })

    assert errors == ['Patient response data does not have the attribute "status"']


def test_patient_response_status_unexpected() -> None:
    """Ensure a patient response with unexpected status returns an error message."""
    errors = source_system_validator.is_patient_response_valid({
        'status': 'other',
    })

    assert errors == ['New patient response data has an unexpected "status" value: other']


# check_patient_data

def test_check_patient_data_valid() -> None:
    """Ensure patient data valid."""
    errors = source_system_validator.check_patient_data(SOURCE_SYSTEM_PATIENT_DATA)

    assert not errors


def test_check_patient_date_of_birth_non_exists() -> None:
    """Ensure patient data invalid date_of_birth return error message."""
    patient_data = SOURCE_SYSTEM_PATIENT_DATA.copy()
    patient_data.pop('dateOfBirth')

    errors = source_system_validator.check_patient_data(patient_data)

    assert errors == ['Patient data does not have the attribute dateOfBirth']


def test_check_patient_date_of_birth_invalid() -> None:
    """Ensure patient data invalid date_of_birth return error message."""
    patient_data = SOURCE_SYSTEM_PATIENT_DATA.copy()
    patient_data['dateOfBirth'] = '1953/01/01'

    errors = source_system_validator.check_patient_data(patient_data)

    assert errors == ["dateOfBirth is invalid: Invalid isoformat string: '1953/01/01'"]


def test_check_patient_first_name_non_exists() -> None:
    """Ensure patient data invalid firstName return error message."""
    patient_data = SOURCE_SYSTEM_PATIENT_DATA.copy()
    patient_data.pop('firstName')

    errors = source_system_validator.check_patient_data(patient_data)

    assert errors == ['Patient data does not have the attribute firstName']


def test_check_patient_first_name_empty() -> None:
    """Ensure patient data invalid firstName return error message."""
    patient_data = SOURCE_SYSTEM_PATIENT_DATA.copy()
    patient_data['firstName'] = ''

    errors = source_system_validator.check_patient_data(patient_data)

    assert errors == ['Patient data firstName is empty']


def test_check_patient_last_name_non_exists() -> None:
    """Ensure patient data invalid lastName return error message."""
    patient_data = SOURCE_SYSTEM_PATIENT_DATA.copy()
    patient_data.pop('lastName')

    errors = source_system_validator.check_patient_data(patient_data)

    assert errors == ['Patient data does not have the attribute lastName']


def test_check_patient_last_name_empty() -> None:
    """Ensure patient data invalid lastName return error message."""
    patient_data = SOURCE_SYSTEM_PATIENT_DATA.copy()
    patient_data['lastName'] = ''

    errors = source_system_validator.check_patient_data(patient_data)

    assert errors == ['Patient data lastName is empty']


def test_check_patient_sex_non_exists() -> None:
    """Ensure patient data invalid lastName return error message."""
    patient_data = SOURCE_SYSTEM_PATIENT_DATA.copy()
    patient_data.pop('sex')

    errors = source_system_validator.check_patient_data(patient_data)

    assert errors == ['Patient data does not have the attribute sex']


def test_check_patient_sex_empty() -> None:
    """Ensure patient data invalid lastName return error message."""
    patient_data = SOURCE_SYSTEM_PATIENT_DATA.copy()
    patient_data['sex'] = ''

    errors = source_system_validator.check_patient_data(patient_data)

    assert errors == ['Patient data sex is empty']


def test_check_patient_alias_non_exists() -> None:
    """Ensure patient data invalid alias return error message."""
    patient_data = SOURCE_SYSTEM_PATIENT_DATA.copy()
    patient_data.pop('alias')

    errors = source_system_validator.check_patient_data(patient_data)

    assert errors == ['Patient data does not have the attribute alias']


def test_check_patient_ramq_non_exists() -> None:
    """Ensure patient data invalid ramq return error message."""
    patient_data = SOURCE_SYSTEM_PATIENT_DATA.copy()
    patient_data.pop('ramq')

    errors = source_system_validator.check_patient_data(patient_data)

    assert errors == ['Patient ramq is missing']


def test_check_patient_ramq_invalid() -> None:
    """Ensure patient data invalid ramq return error message."""
    patient_data = SOURCE_SYSTEM_PATIENT_DATA.copy()
    patient_data['ramq'] = 'ABC1111'

    errors = source_system_validator.check_patient_data(patient_data)

    assert errors == ['Patient ramq is invalid']


def test_check_patient_ramq_expiration_non_exists() -> None:
    """Ensure patient data invalid ramqExpiration return error message."""
    patient_data = SOURCE_SYSTEM_PATIENT_DATA.copy()
    patient_data.pop('ramqExpiration')

    errors = source_system_validator.check_patient_data(patient_data)

    assert errors == ['Patient data does not have the attribute ramqExpiration']


def test_check_patient_ramq_expiration_invalid() -> None:
    """Ensure patient data invalid ramqExpiration return error message."""
    patient_data = SOURCE_SYSTEM_PATIENT_DATA.copy()
    patient_data['ramqExpiration'] = '2018-01-31'

    errors = source_system_validator.check_patient_data(patient_data)

    assert errors == ["Patient data ramqExpiration is invalid: time data '2018-01-31' does not match format '%Y%m'"]


def test_check_patient_mrns_non_exists() -> None:
    """Ensure patient data invalid mrn site return error message."""
    patient_data = SOURCE_SYSTEM_PATIENT_DATA.copy()
    patient_data.pop('mrns')

    errors = source_system_validator.check_patient_data(patient_data)

    assert errors == ['Patient data does not have the attribute mrns']


def test_check_patient_mrns_empty() -> None:
    """Ensure patient data invalid mrn site return error message."""
    patient_data = SOURCE_SYSTEM_PATIENT_DATA.copy()
    patient_data['mrns'] = []

    errors = source_system_validator.check_patient_data(patient_data)

    assert errors == ['Patient data mrns is empty']


def test_check_patient_mrn_site_non_exists() -> None:
    """Ensure patient data invalid mrn site return error message."""
    patient_data = SOURCE_SYSTEM_PATIENT_DATA.copy()
    patient_data['mrns'] = [
        {
            'mrn': '9999993',
            'active': True,
        },
    ]

    errors = source_system_validator.check_patient_data(patient_data)

    assert errors == ['Patient MRN data does not have the attribute site']


def test_check_patient_mrn_site_empty() -> None:
    """Ensure patient data invalid mrn site return error message."""
    patient_data = SOURCE_SYSTEM_PATIENT_DATA.copy()
    patient_data['mrns'] = [
        {
            'site': '',
            'mrn': '9999993',
            'active': True,
        },
    ]

    errors = source_system_validator.check_patient_data(patient_data)

    assert errors == ['Patient MRN data site is empty']


def test_check_patient_mrn_mrn_non_exists() -> None:
    """Ensure patient data invalid mrn mrn return error message."""
    patient_data = SOURCE_SYSTEM_PATIENT_DATA.copy()
    patient_data['mrns'] = [
        {
            'site': 'MGH',
            'active': True,
        },
    ]

    errors = source_system_validator.check_patient_data(patient_data)

    assert errors == ['Patient MRN data does not have the attribute mrn']


def test_check_patient_mrn_mrn_empty() -> None:
    """Ensure patient data invalid mrn mrn return error message."""
    patient_data = SOURCE_SYSTEM_PATIENT_DATA.copy()
    patient_data['mrns'] = [
        {
            'site': 'MGH',
            'mrn': '',
            'active': True,
        },
    ]

    errors = source_system_validator.check_patient_data(patient_data)

    assert errors == ['Patient MRN data mrn is empty']


def test_check_patient_mrn_active_non_exists() -> None:
    """Ensure patient data invalid mrn active return error message."""
    patient_data = SOURCE_SYSTEM_PATIENT_DATA.copy()
    patient_data['mrns'] = [
        {
            'site': 'MGH',
            'mrn': '9999993',
        },
    ]

    errors = source_system_validator.check_patient_data(patient_data)

    assert errors == ['Patient MRN data does not have the attribute active']


def test_check_patient_mrn_active_invalid() -> None:
    """Ensure patient data invalid mrn active return error message."""
    patient_data = SOURCE_SYSTEM_PATIENT_DATA.copy()
    patient_data['mrns'] = [
        {
            'site': 'MGH',
            'mrn': '9999993',
            'active': '',
        },
    ]

    errors = source_system_validator.check_patient_data(patient_data)

    assert errors == ['Patient MRN data active is not bool']


def test_new_patient_response_no_status() -> None:
    """An error message is returned when the patient response has no status."""
    response = {
        'error': 'Message',
    }

    valid, errors = source_system_validator.is_new_patient_response_valid(response)
    assert not valid
    assert errors == ['Patient response data does not have the attribute "status"']


def test_new_patient_response_success() -> None:
    """The response is considered valid if the status is 'Success'."""
    response = {
        'status': 'success',
    }

    valid, errors = source_system_validator.is_new_patient_response_valid(response)
    assert valid
    assert not errors


def test_new_patient_response_error() -> None:
    """The response is considered invalid if the status is 'Error'."""
    response = {
        'status': 'error',
    }

    valid, errors = source_system_validator.is_new_patient_response_valid(response)
    assert not valid
    assert errors == ['Error response from the source system']


def test_new_patient_response_unexpected_status() -> None:
    """An error message is returned when the patient response contains an unexpected status value."""
    response = {
        'status': 'other',
    }

    valid, errors = source_system_validator.is_new_patient_response_valid(response)
    assert not valid
    assert errors == ['New patient response data has an unexpected "status" value: other']
