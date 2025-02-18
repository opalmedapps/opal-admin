# SPDX-FileCopyrightText: Copyright (C) 2022 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Module providing validation rules for the data being sent/received to/from the source system."""
import datetime
import re
from typing import Any

from django.core.exceptions import ValidationError

from opal.core.validators import validate_ramq
from opal.utils import base64_utils

from .hospital_data import SourceSystemReportExportData

# TODO: translate error messages add _(message) that will be shown to the user.


class SourceSystemValidator:
    """Source system helper service that validates source system request and response data."""

    def is_report_export_request_valid(
        self,
        report_data: SourceSystemReportExportData,
    ) -> bool:
        """
        Check if the source system report export data is valid.

        Args:
            report_data (SourceSystemReportExportData): Source system report export data needed to
                                                        call source system endpoint

        Returns:
            bool: boolean value showing if source system report export data is valid
        """
        # TODO: Add more validation/checks for the MRN and Site fields once the requirements are clarified
        # TODO: Confirm the regex pattern for the document number
        reg_exp = re.compile(r'(^FU-[a-zA-Z0-9]+$)|(^FMU-[a-zA-Z0-9]+$)|(^MU-[a-zA-Z0-9]+$)')
        return (  # check if MRN is not empty
            bool(report_data.mrn.strip())
            # check if site is not empty
            and bool(report_data.site.strip())
            # check if report content is base64
            and base64_utils.is_base64(report_data.base64_content)
            # check if document type format is valid
            and bool(reg_exp.match(report_data.document_number))
        )

    def is_report_export_response_valid(
        self,
        response_data: Any,
    ) -> bool:
        """
        Check if the source system report export response data is valid.

        Args:
            response_data (Any): Source system report export response data received from the source system

        Returns:
            bool: boolean value showing if source system report export data is valid
        """
        try:
            status = response_data['status']
        except (TypeError, KeyError):
            return False

        # TODO: confirm validation rules (e.g., status in {'success', 'error'})
        return isinstance(status, str)

    def is_patient_site_mrn_valid(self, mrn: str, site: str) -> bool:
        """
        Check if the mrn and site are not empty.

        Args:
            mrn: Medical Record Number (MRN) code (e.g., 9999993)
            site: site code (e.g., MGH)

        Returns:
            bool: boolean value showing if the mrn and site are not empty
        """
        return bool(mrn.strip()) and bool(site.strip())

    def is_patient_ramq_valid(self, ramq: str) -> bool:
        """
        Check if the RAMQ value is valid.

        Args:
            ramq (str): RAMQ code

        Returns:
            bool: boolean value showing if RAMQ value is empty
        """
        reg_exp = re.compile(r'^[A-Z]{4}\d{8}$')
        return bool(reg_exp.match(ramq))

    def is_patient_response_valid(
        self,
        response_data: Any,
    ) -> list[str]:
        """
        Check if the source system patient response data is valid.

        Args:
            response_data (Any): Source system patient response data received from the source system

        Returns:
            return errors list
        """
        errors = []
        status = response_data.get('status')
        patient_data = response_data.get('data')

        if status is None:
            errors.append('Patient response data does not have the attribute "status"')
        elif not errors and patient_data and status == 'success':
            errors += self.check_patient_data(patient_data)
        elif status == 'error':
            if patient_data and 'exception' in patient_data:
                errors.append('connection_error')
            message: str = response_data.get('message')

            if message:
                # TODO: improve
                friendly_message = message.replace('Patient not found', 'not_found')
                friendly_message = friendly_message.replace(
                    'Not Opal test patient',
                    'no_test_patient',
                )
                errors.append(friendly_message)
        else:
            errors.append(f'New patient response data has an unexpected "status" value: {status}')

        return errors

    def is_new_patient_response_valid(
        self,
        response_data: Any,
    ) -> tuple[bool, list[str]]:
        """
        Check if the source system's new patient response data is valid.

        Args:
            response_data: Source system new patient response data

        Returns:
            A boolean indicating validity (true if valid, false otherwise) and an errors list
        """
        errors = []
        status = response_data.get('status')
        success = status == 'success'

        if status is None:
            errors.append('Patient response data does not have the attribute "status"')
        elif status == 'error':
            errors.append('Error response from the source system')
        elif not success:
            errors.append(f'New patient response data has an unexpected "status" value: {status}')

        return success, errors

    def check_patient_data(self, patient_data: Any) -> list[str]:  # noqa: C901, PLR0912, PLR0915
        """
        Check if the patient data is valid.

        Args:
            patient_data (Any): Source system patient data

        Returns:
            return errors list
        """
        errors = []
        # check dateOfBirth
        date_of_birth = None
        try:
            date_of_birth = patient_data['dateOfBirth']
        except (KeyError):
            errors.append('Patient data does not have the attribute dateOfBirth')

        if date_of_birth:
            try:
                datetime.datetime.fromisoformat(date_of_birth).date()
            except ValueError as exc:
                errors.append(f'dateOfBirth is invalid: {exc}')

        # check firstName
        first_name = None
        try:
            first_name = patient_data['firstName']
        except (KeyError):
            errors.append('Patient data does not have the attribute firstName')
        if first_name is not None and not first_name:
            errors.append('Patient data firstName is empty')

        # check lastName
        last_name = None
        try:
            last_name = patient_data['lastName']
        except (KeyError):
            errors.append('Patient data does not have the attribute lastName')
        if last_name is not None and not last_name:
            errors.append('Patient data lastName is empty')

        # check sex
        sex = None
        try:
            sex = patient_data['sex']
        except (KeyError):
            errors.append('Patient data does not have the attribute sex')
        if sex is not None and not sex:
            errors.append('Patient data sex is empty')

        # check alias
        if 'alias' not in patient_data:
            errors.append('Patient data does not have the attribute alias')

        # check ramq
        ramq = None
        try:
            ramq = patient_data['ramq']
        except (KeyError):
            errors.append('Patient ramq is missing')
        if ramq:
            try:
                validate_ramq(ramq)
            except ValidationError:
                errors.append('Patient ramq is invalid')

        # check ramqExpiration
        ramq_expiration = None
        try:
            ramq_expiration = patient_data['ramqExpiration']
        except (KeyError):
            errors.append('Patient data does not have the attribute ramqExpiration')
        if ramq_expiration:
            try:
                datetime.datetime.strptime(ramq_expiration, '%Y%m')  # noqa: DTZ007
            except ValueError as exc:
                errors.append(f'Patient data ramqExpiration is invalid: {exc}')

        # check mrns
        mrns = None
        try:
            mrns = patient_data['mrns']
        except (KeyError):
            errors.append('Patient data does not have the attribute mrns')
        if mrns:
            for mrn in mrns:
                errors += self._check_mrn_data(mrn)
        elif mrns is not None and not mrns:
            errors.append('Patient data mrns is empty')

        return errors

    def _check_mrn_data(self, mrn_data: Any) -> list[str]:
        """
        Check if the patient MRN data is valid.

        Args:
            mrn_data (Any): Source system patient MRN data

        Returns:
            return errors list
        """
        errors = []
        # check site
        site = None
        try:
            site = mrn_data['site']
        except (KeyError):
            errors.append('Patient MRN data does not have the attribute site')
        if site is not None and not site:
            errors.append('Patient MRN data site is empty')

        # check mrn
        mrn = None
        try:
            mrn = mrn_data['mrn']
        except (KeyError):
            errors.append('Patient MRN data does not have the attribute mrn')
        if mrn is not None and not mrn:
            errors.append('Patient MRN data mrn is empty')

        # check active
        active = None
        try:
            active = mrn_data['active']
        except (KeyError):
            errors.append('Patient MRN data does not have the attribute active')
        if active is not None and not isinstance(active, bool):
            errors.append('Patient MRN data active is not bool')

        return errors
