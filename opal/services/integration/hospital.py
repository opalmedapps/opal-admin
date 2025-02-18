# SPDX-FileCopyrightText: Copyright (C) 2025 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Functions in this module provide the ability to communicate with an institution's integration engine."""

from http import HTTPStatus
from typing import Any

from django.conf import settings

import requests

from .schemas import ErrorResponseSchema, HospitalNumberSchema, PatientByHINSchema, PatientByMRNSchema, PatientSchema


class NonOKResponseError(Exception):
    """Error when a non-OK status code is returned in a response."""

    def __init__(self, response: requests.Response) -> None:
        """
        Initialize the error for the given response.

        Args:
            response: the response with an unsupported status code
        """
        self.error = ErrorResponseSchema.model_validate_json(response.content, strict=True)
        message = f'Non-OK status code returned: {self.error.status_code}: {self.error.message}'
        super().__init__(message)


def _retrieve(url: str, data: Any | None) -> requests.Response:
    response = requests.post(url, data=data, timeout=5)

    if response.status_code != HTTPStatus.OK:
        raise NonOKResponseError(response)

    return response


def find_patient_by_hin(health_insurance_number: str) -> PatientSchema:
    """
    Find a patient by their health insurance number.

    Raises [NonOKResponseError][opal.services.integration.hospital.NonOKResponseError] if the response is not OK.
    Raises [pydantic.ValidationError][] if the data in the response is not valid.

    Args:
        health_insurance_number: the health insurance number of the patient

    Returns:
        the patient
    """
    data = PatientByHINSchema(health_insurance_number=health_insurance_number)
    response = _retrieve(f'{settings.SOURCE_SYSTEM_HOST}/getPatientDemographicsByHIN', data=data.model_dump_json())

    return PatientSchema.model_validate_json(response.content, strict=True)


def find_patient_by_mrn(mrn: str, site: str) -> PatientSchema:
    """
    Find a patient by their hospital number (MRN and site code).

    Raises [NonOKResponseError][opal.services.integration.hospital.NonOKResponseError] if the response is not OK.
    Raises [pydantic.ValidationError][] if the data in the response is not valid.

    Args:
        mrn: the MRN of the patient
        site: the site code the MRN of the patient belongs to

    Returns:
        the patient
    """
    data = PatientByMRNSchema(mrn=mrn, site=site)
    response = _retrieve(f'{settings.SOURCE_SYSTEM_HOST}/getPatientDemographicsByMRN', data=data.model_dump_json())

    return PatientSchema.model_validate_json(response.content, strict=True)


def notify_new_patient(mrn: str, site: str) -> None:
    """
    Notify the integration engine that a patient is now an Opal patient.

    Raises [NonOKResponseError][opal.services.integration.hospital.NonOKResponseError] if the response is not OK.

    Args:
        mrn: the MRN of the patient
        site: the site code the MRN of the patient belongs to
    """
    data = HospitalNumberSchema(mrn=mrn, site=site)
    _retrieve(f'{settings.SOURCE_SYSTEM_HOST}/newOpalPatient', data=data.model_dump_json())

    # we know at this point that the request was successful
