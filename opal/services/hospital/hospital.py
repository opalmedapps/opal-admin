"""Module providing business logic for the hospital's internal communication (e.g., Opal Integration Engine)."""
from datetime import datetime
from typing import Any

from .hospital_communication import OIEHTTPCommunicationManager
from .hospital_data import OIEMRNData, OIEPatientData, OIEReportExportData
from .hospital_error import OIEErrorHandler
from .hospital_validation import OIEValidator


class OIEService:
    """Service that provides an interface (a.k.a., Facade) for interaction with the Opal Integration Engine (OIE).

    All the provided functions contain the following business logic:
        * validate the input data (a.k.a., parameters)
        * send an HTTP request to the OIE
        * validate the response data received from the OIE
        * return response data or an error in JSON format
    """

    def __init__(self) -> None:
        """Initialize OIE helper services."""
        self.communication_manager = OIEHTTPCommunicationManager()
        self.error_handler = OIEErrorHandler()
        self.validator = OIEValidator()

    def export_pdf_report(
        self,
        report_data: OIEReportExportData,
    ) -> Any:
        """Send base64 encoded PDF report to the OIE.

        Args:
            report_data (OIEReportExportData): PDF report data needed to call OIE endpoint

        Returns:
            Any: JSON object response
        """
        # Return a JSON format error if `OIEReportExportData` is not valid
        if not self.validator.is_report_export_request_valid(report_data):
            return self.error_handler.generate_error(
                {'message': 'Provided request data are invalid.'},
            )

        # TODO: Change docType to docNumber once the OIE's endpoint is updated
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
                'message': 'OIE response format is not valid.',
                'responseData': response_data,
            },
        )

    def find_patient_by_mrn(self, mrn: str, site: str) -> Any:  # noqa: WPS210
        """Search patient info by MRN code.

        Args:
            mrn: Medical Record Number (MRN) code (e.g., 9999993)
            site: site code (e.g., MGH)

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

        patient_data = response_data['data']
        mrns = []
        if not errors:
            for mrn_dict in patient_data['mrns']:
                mrns.append(OIEMRNData(
                    site=mrn_dict['site'],
                    mrn=mrn_dict['mrn'],
                    active=mrn_dict['active'],
                ))

            return {
                'status': 'success',
                'data': OIEPatientData(
                    date_of_birth=datetime.strptime(
                        str(patient_data['dateOfBirth']),
                        '%Y-%m-%d %H:%M:%S',
                    ).date(),
                    first_name=str(patient_data['firstName']),
                    last_name=str(patient_data['lastName']),
                    sex=str(patient_data['sex']),
                    alias=str(patient_data['alias']),
                    deceased=patient_data['deceased'],
                    death_date_time=None if patient_data['deathDateTime'] == ''
                    else datetime.strptime(
                        str(patient_data['deathDateTime']),
                        '%Y-%m-%d %H:%M:%S',
                    ),
                    ramq=str(patient_data['ramq']),
                    ramq_expiration=None if patient_data['ramqExpiration'] == ''
                    else datetime.strptime(
                        str(patient_data['ramqExpiration']),
                        '%Y-%m-%d %H:%M:%S',
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

    def find_patient_by_ramq(self, ramq: str) -> Any:  # noqa: WPS210
        """Search patient info by RAMQ code.

        Args:
            ramq (str): RAMQ code

        Returns:
            patient info or an error in JSON format
        """
        if not self.validator.is_patient_ramq_valid(ramq):
            return self.error_handler.generate_error(
                {'message': 'Provided RAMQ is invalid.'},
            )

        payload = {
            'medicareNumber': ramq,
            'visitInfo': False,
        }
        response_data = self.communication_manager.submit(
            endpoint='/Patient/get',
            payload=payload,
        )

        errors = self.validator.is_patient_response_valid(response_data)

        patient_data = response_data['data']
        mrns = []
        if not errors:
            for mrn_dict in patient_data['mrns']:
                mrns.append(OIEMRNData(
                    site=mrn_dict['site'],
                    mrn=mrn_dict['mrn'],
                    active=mrn_dict['active'],
                ))

            return {
                'status': 'success',
                'data': OIEPatientData(
                    date_of_birth=datetime.strptime(
                        str(patient_data['dateOfBirth']),
                        '%Y-%m-%d %H:%M:%S',
                    ).date(),
                    first_name=str(patient_data['firstName']),
                    last_name=str(patient_data['lastName']),
                    sex=str(patient_data['sex']),
                    alias=str(patient_data['alias']),
                    deceased=patient_data['deceased'],
                    death_date_time=None if patient_data['deathDateTime'] == ''
                    else datetime.strptime(
                        str(patient_data['deathDateTime']),
                        '%Y-%m-%d %H:%M:%S',
                    ),
                    ramq=str(patient_data['ramq']),
                    ramq_expiration=None if patient_data['ramqExpiration'] == ''
                    else datetime.strptime(
                        str(patient_data['ramqExpiration']),
                        '%Y-%m-%d %H:%M:%S',
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
