# SPDX-FileCopyrightText: Copyright (C) 2023 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Module providing business logic for communication with ORMS."""

from typing import Any
from uuid import UUID

from ..general.service_error import ServiceErrorHandler
from .orms_communication import ORMSHTTPCommunicationManager
from .orms_validation import ORMSValidator


class ORMSService:
    """
    Service that provides an interface for interaction with the Opal Room Management System (ORMS).

    All the provided functions contain the following business logic:
        * validate the input data (parameters)
        * send an HTTP request to ORMS
        * validate the response data received from ORMS
        * return response data or an error in JSON format
    """

    def __init__(self) -> None:
        """Initialize ORMS helper services."""
        self.communication_manager = ORMSHTTPCommunicationManager()
        self.error_handler = ServiceErrorHandler()
        self.validator = ORMSValidator()

    def set_opal_patient(
        self,
        active_mrn_list: list[tuple[str, str]],
        patient_uuid: UUID,
    ) -> dict[str, Any]:
        """
        Mark a patient as an Opal patient in ORMS.

        Tries calling ORMS using each of the patient's MRNs until one succeeds.

        Args:
            active_mrn_list: a list of all active (site_code, mrn) tuples belonging to the patient
            patient_uuid: the patient's UUID created and saved in Django

        Returns:
            A wrapped success response from ORMS or an error in JSON format
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
                endpoint='/php/api/public/v2/patient/updateOpalStatus.php',
                payload={
                    'mrn': mrn,
                    'site': site_code,
                    'opalStatus': 1,  # 1 => registered/active patient; 0 => unregistered/inactive patient
                    'opalUUID': str(patient_uuid),
                },
            )

            success, errors = self.validator.is_patient_response_valid(response_data)
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
