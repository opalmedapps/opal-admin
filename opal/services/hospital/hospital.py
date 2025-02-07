# SPDX-FileCopyrightText: Copyright (C) 2022 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Module providing business logic for the hospital's internal communication (e.g., Opal Integration Engine)."""
from datetime import datetime
from typing import Any

from ..general.service_error import ServiceErrorHandler
from .hospital_communication import SourceSystemHTTPCommunicationManager
from .hospital_data import SourceSystemMRNData, SourceSystemPatientData, SourceSystemReportExportData
from .hospital_validation import SourceSystemValidator


class SourceSystemService:
    """
    Service that provides an interface (a.k.a., Facade) for interaction with the Integration Engine.

    All the provided functions contain the following business logic:
        * validate the input data (a.k.a., parameters)
        * send an HTTP request to the Source system
        * validate the response data received from the Source system
        * return response data or an error in JSON format
    """

    def __init__(self) -> None:
        """Initialize source system helper services."""
        self.communication_manager = SourceSystemHTTPCommunicationManager()
        self.error_handler = ServiceErrorHandler()
        self.validator = SourceSystemValidator()

    def export_pdf_report(
        self,
        report_data: SourceSystemReportExportData,
    ) -> Any:
        """
        Send base64 encoded PDF report to the source system.

        Args:
            report_data (SourceSystemReportExportData): PDF report data needed to call Source System endpoint

        Returns:
            Any: JSON object response
        """
        # Return a JSON format error if `SourceSystemReportExportData` is not valid
        if not self.validator.is_report_export_request_valid(report_data):
            return self.error_handler.generate_error(
                {'message': 'Provided request data are invalid.'},
            )

        # TODO: Change docType to docNumber once the source system endpoint is updated
        payload = {
            'mrn': report_data.mrn,
            'site': report_data.site,
            'reportContent': report_data.base64_content,
            'docType': report_data.document_number,
            'documentDate': report_data.document_date.strftime('%Y-%m-%d %H:%M:%S'),
        }

        response_data = self.communication_manager.submit(
            endpoint='/report/post',
            payload=payload,
        )

        if self.validator.is_report_export_response_valid(response_data):
            # TODO: confirm return format
            return response_data

        return self.error_handler.generate_error(
            {
                'message': 'Source system response format is not valid.',
                'responseData': response_data,
            },
        )

    def find_patient_by_mrn(self, mrn: str, site: str) -> dict[str, Any]:
        """
        Search patient info by MRN code.

        Args:
            mrn: Medical Record Number (MRN) code (e.g., 9999993)
            site: site acronym (e.g., MGH)

        Returns:
            patient info or an error in JSON format
        """
        if not self.validator.is_patient_site_mrn_valid(mrn, site):
            return self.error_handler.generate_error(
                {'message': 'Provided MRN or site is invalid.'},
            )

        payload = {
            'mrn': mrn,
            'site': site,
            'visitInfo': False,
        }
        response_data = self.communication_manager.submit(
            endpoint='/Patient/get',
            payload=payload,
        )

        errors = self.validator.is_patient_response_valid(response_data)

        mrns = []
        if not errors:
            # assign value to patient data only when no errors found in response data
            patient_data = response_data['data']

            for mrn_dict in patient_data['mrns']:
                mrn_data = SourceSystemMRNData(
                    site=mrn_dict['site'],
                    mrn=mrn_dict['mrn'],
                    active=mrn_dict['active'],
                )
                mrns.append(mrn_data)

            return {
                'status': 'success',
                'data': SourceSystemPatientData(
                    date_of_birth=datetime.fromisoformat(
                        str(patient_data['dateOfBirth']),
                    ).date(),
                    first_name=str(patient_data['firstName']),
                    last_name=str(patient_data['lastName']),
                    sex=str(patient_data['sex']),
                    alias=str(patient_data['alias']),
                    deceased=patient_data['deceased'],
                    death_date_time=None if not patient_data['deathDateTime']
                    else datetime.fromisoformat(str(patient_data['deathDateTime'])),
                    ramq=str(patient_data['ramq']),
                    ramq_expiration=None if not patient_data['ramqExpiration']
                    else datetime.strptime(  # noqa: DTZ007
                        str(patient_data['ramqExpiration']),
                        '%Y%m',
                    ),
                    mrns=mrns,
                ),
            }

        return self.error_handler.generate_error(
            {
                'message': errors,
                'responseData': response_data,
            },
        )

    def find_patient_by_ramq(self, ramq: str) -> dict[str, Any]:
        """
        Search patient info by RAMQ code.

        Args:
            ramq (str): RAMQ code

        Returns:
            patient info or an error in JSON format
        """
        if not self.validator.is_patient_ramq_valid(ramq):
            return self.error_handler.generate_error(
                {'message': 'Provided RAMQ is invalid.'},
            )

        response_data = self.communication_manager.submit(
            endpoint='/Patient/get',
            payload={
                'medicareNumber': ramq,
                'visitInfo': False,
            },
        )

        errors = self.validator.is_patient_response_valid(response_data)

        mrns = []
        if not errors:
            # assign value to patient data only when no errors found in response data
            patient_data = response_data['data']

            for mrn_dict in patient_data['mrns']:
                mrn_data = SourceSystemMRNData(
                    site=mrn_dict['site'],
                    mrn=mrn_dict['mrn'],
                    active=mrn_dict['active'],
                )
                mrns.append(mrn_data)

            return {
                'status': 'success',
                'data': SourceSystemPatientData(
                    date_of_birth=datetime.fromisoformat(
                        str(patient_data['dateOfBirth']),
                    ).date(),
                    first_name=str(patient_data['firstName']),
                    last_name=str(patient_data['lastName']),
                    sex=str(patient_data['sex']),
                    alias=str(patient_data['alias']),
                    deceased=patient_data['deceased'],
                    death_date_time=None if not patient_data['deathDateTime']
                    else datetime.fromisoformat(str(patient_data['deathDateTime'])),
                    ramq=str(patient_data['ramq']),
                    ramq_expiration=None if not patient_data['ramqExpiration']
                    else datetime.strptime(  # noqa: DTZ007
                        str(patient_data['ramqExpiration']),
                        '%Y%m',
                    ),
                    mrns=mrns,
                ),
            }

        return self.error_handler.generate_error(
            {
                'message': errors,
                'responseData': response_data,
            },
        )

    def new_opal_patient(self, active_mrn_list: list[tuple[str, str]]) -> dict[str, Any]:
        """
        Notifies the source system of a new Opal patient.

        Tries calling the source system using each of the patient's MRNs until one succeeds.

        Args:
            active_mrn_list: a list of all active (site_code, mrn) tuples belonging to the patient

        Returns:
            A wrapped success response from the source system or an error in JSON format
        """
        errors, response_data = None, None
        if not active_mrn_list:
            return self.error_handler.generate_error(
                {
                    'message': 'A list of active (site, mrn) tuples should be provided to set_opal_patient',
                    'mrn_list': active_mrn_list,
                },
            )

        for site_code, mrn in active_mrn_list:
            response_data = self.communication_manager.submit(
                endpoint='/Patient/New',
                payload={
                    'mrn': mrn,
                    'site': site_code,
                },
            )

            success, errors = self.validator.is_new_patient_response_valid(response_data)
            if success:
                return {
                    'status': 'success',
                }

        # If none of the calls succeeded, return the last error
        return self.error_handler.generate_error(
            {
                'message': errors,
                'responseData': response_data,
            },
        )
