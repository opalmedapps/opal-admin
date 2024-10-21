from http import HTTPStatus
from typing import Any

import requests

from .models import ErrorResponse, Patient, PatientByHINRequest, PatientByMRNRequest


class NonOKResponseError(Exception):
    """Error when a non-OK status code is returned in a response."""

    def __init__(self, response: requests.Response) -> None:
        """
        Initialize the error for the given response.

        Args:
            response: the response with an unsupported status code
        """
        self.error = ErrorResponse.model_validate_json(response.content, strict=True)
        message = f'Non-OK status code returned: {self.error.status_code}: {self.error.message}'
        super().__init__(message)


def _retrieve(url: str, data: Any | None) -> requests.Response:
    response = requests.get(url, data=data, timeout=5)

    if response.status_code != HTTPStatus.OK:
        raise NonOKResponseError(response)

    return response


def find_patient_by_hin(health_insurance_number: str) -> Patient:
    data = PatientByHINRequest(health_insurance_number=health_insurance_number)
    response = _retrieve('http://localhost/getPatientByHIN', data=data.model_dump_json())

    return Patient.model_validate_json(response.content, strict=True)


def find_patient_by_mrn(mrn: str, site: str) -> Patient:
    data = PatientByMRNRequest(mrn=mrn, site=site)
    response = _retrieve('http://localhost/getPatientByMRN', data=data.model_dump_json())

    return Patient.model_validate_json(response.content, strict=True)
