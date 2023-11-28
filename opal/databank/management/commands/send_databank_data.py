"""Command for sending data to the Databank."""
import json
from collections import defaultdict
from typing import Any, Optional
import re
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models.query import QuerySet

import requests
from requests.auth import HTTPBasicAuth

from opal.databank.models import DatabankConsent, DataModuleType
from opal.legacy.models import LegacyAppointment, LegacyDiagnosis, LegacyPatient, LegacyPatientTestResult
from opal.legacy_questionnaires.models import LegacyAnswerQuestionnaire


class Command(BaseCommand):
    """Command to send the data of consenting databank patients to the external databank."""

    help = "send consenting Patients' data to the databank"  # noqa: A003

    @transaction.atomic
    def handle(self, *args: Any, **kwargs: Any) -> None:
        """
        Handle sending patients de-identified data to the databank.

        Return 'None'.

        Args:
            args: non-keyword input arguments.
            kwargs: variable keyword input arguments.
        """
        consenting_patients_querysets = {
            DataModuleType.APPOINTMENTS: DatabankConsent.objects.filter(has_appointments=True),
            DataModuleType.DIAGNOSES: DatabankConsent.objects.filter(has_diagnoses=True),
            DataModuleType.DEMOGRAPHICS: DatabankConsent.objects.filter(has_demographics=True),
            DataModuleType.LABS: DatabankConsent.objects.filter(has_labs=True),
            DataModuleType.QUESTIONNAIRES: DatabankConsent.objects.filter(has_questionnaires=True),
        }

        for module, queryset in consenting_patients_querysets.items():
            patients_list = list(queryset.iterator())
            patients_count = len(patients_list)

            if patients_count > 0:
                self.stdout.write(
                    f'Number of {DataModuleType(module).label}-consenting patients is: {queryset.count()}',
                )

                # Retrieve patient data for each module type and send all at once
                combined_module_data: list = []
                for databank_patient in patients_list:
                    databank_data = self._retrieve_databank_data_for_patient(databank_patient, module)
                    if databank_data:
                        nested_databank_data = self._nest_and_serialize_queryset(
                            databank_patient.guid,
                            databank_data,
                            module,
                        )
                        combined_module_data.append(nested_databank_data)
                if combined_module_data:
                    aggregate_response = self._send_to_oie_and_handle_response({'patientList': combined_module_data})
                    if aggregate_response:
                        print('DEBUG: Got aggregate response')
                        self._parse_aggregate_databank_response(aggregate_response, combined_module_data)
            else:
                self.stderr.write(
                    f'No patients found consenting to {DataModuleType(module).label} data donation.',
                )

    def _retrieve_databank_data_for_patient(self, databank_patient: DatabankConsent, module: DataModuleType) -> Any:
        """Use model managers to retrieve databank data for a consenting patient.

        Args:
            databank_patient: Patient consenting for this databank module
            module: databank data module enum type

        Raises:
            ValueError: If an invalid DateModuleType value is provided or if a patient is missing the legacy id

        Returns:
            JSON string of the patient's databank information for this module
        """
        if not databank_patient.patient.legacy_id:
            raise ValueError('Legacy ID missing from Databank Patient.')
        match module:
            case DataModuleType.APPOINTMENTS:
                databank_data = LegacyAppointment.objects.get_databank_data_for_patient(
                    patient_ser_num=databank_patient.patient.legacy_id,
                    last_synchronized=databank_patient.last_synchronized,
                )
            case DataModuleType.DIAGNOSES:
                databank_data = LegacyDiagnosis.objects.get_databank_data_for_patient(
                    patient_ser_num=databank_patient.patient.legacy_id,
                    last_synchronized=databank_patient.last_synchronized,
                )
            case DataModuleType.DEMOGRAPHICS:
                databank_data = LegacyPatient.objects.get_databank_data_for_patient(
                    patient_ser_num=databank_patient.patient.legacy_id,
                    last_synchronized=databank_patient.last_synchronized,
                )
            case DataModuleType.LABS:
                databank_data = LegacyPatientTestResult.objects.get_databank_data_for_patient(
                    patient_ser_num=databank_patient.patient.legacy_id,
                    last_synchronized=databank_patient.last_synchronized,
                )
            case DataModuleType.QUESTIONNAIRES:
                databank_data = LegacyAnswerQuestionnaire.objects.get_databank_data_for_patient(
                    patient_ser_num=databank_patient.patient.legacy_id,
                    last_synchronized=databank_patient.last_synchronized,
                )
            case _:
                raise ValueError(f'{module} not a valid databank data type.')

        if databank_data:
            # Return the data for this patient
            self.stdout.write(
                f'{len(databank_data)} instances of {DataModuleType(module).label} found for {databank_patient.patient}',  # noqa: E501, WPS221
            )
            return databank_data
        else:
            self.stdout.write(
                f'No {DataModuleType(module).label} data found for {databank_patient.patient}',
            )

    def _nest_and_serialize_queryset(self, guid: str, queryset: QuerySet, nesting_key: str) -> dict:
        """Pull the GUID to the top element and nest the rest of the qs records into a single dict.

        Args:
            queryset: Databank queryset with one or many rows
            guid: GUID for this databank patient, used as the 'parent' element of the dict
            nesting_key: name of key for the nested data

        Returns:
            Nested dictionary list
        """
        data = list(queryset)

        # Extra nesting requirements for lab data to reduce data repetition among components of a single lab group
        if nesting_key == 'LABS':
            groups = defaultdict(list)
            for item in data:
                # Group by test_group_name, test_group_indicator, and collection date
                key = (
                    item.pop('test_group_name', None),
                    item.pop('test_group_indicator', None),
                    item.pop('specimen_collected_date', None),
                )
                groups[key].append(item)
            # Convert the defaultdict to the final format
            data = [
                {
                    'test_group_name': key[0],
                    'test_group_indicator': key[1],
                    'specimen_collected_date': key[2],
                    'components': value,
                }
                for key, value in groups.items()
            ]
        return {'GUID': guid, nesting_key: data}

    def _send_to_oie_and_handle_response(self, data: dict) -> Any:
        """Send databank dataset to the OIE and handle immediate OIE response.

        Args:
            data: Databank dictionary of one of the five module types.

        Returns:
            Any: json object containing response for each individual patient message, or empty if send failed
        """
        try:
            response = requests.post(
                url=f'{settings.OIE_HOST}/databank/post',
                auth=HTTPBasicAuth(settings.OIE_USER, settings.OIE_PASSWORD),
                data=json.dumps(data, default=str),
                headers={'Content-Type': 'application/json'},
                timeout=30,
            )
            # 403 Unauth: Possibly need to check reverse proxy allow list and endpoint pass-throughs
            # 400 data failed to send
        except requests.exceptions.RequestException as exc:
            # log OIE errors
            self.stderr.write(
                f'Databank sender OIE Error: {exc}',
            )
        if response.status_code == 200:
            # Data sent to OIE successfully, parse aggregate response from databank and update models
            return response.json()
        elif response.json()['status'] == 502:
            # Bad gateway, issue with connection to OIE
            self.stderr.write(
                f"Bad gateway error, check OIE instance to ensure channels are enabled: {response.json()['message']}",
            )
            return {}
        # Reverse proxy config error or resource not found
        self.stderr.write(
            f"Missing endpoint allowance for databank or other reverse proxy error: {response.json()['message']}",
        )
        return {}

    def _parse_aggregate_databank_response(self, aggregate_response: json, original_data_sent: list) -> None:
        """Parse the aggregated response message from the databank and update databank models.

        Args:
            aggregate_response: JSON object with a response code & message for each patient data
            original_data_sent: list of data originally sent to OIE
        """
        for identifier, response_object in aggregate_response.items():
            status_code, message = response_object
            patient_guid = identifier[5:]
            if status_code in {200, 201}:
                # Call auxiliary method to update the PatientDatabankConsent model
                synced_patient_data = next((item for item in original_data_sent if item['GUID'] == patient_guid), None)
                self._update_patient_databank_metadata(
                    DatabankConsent.objects.filter(guid=patient_guid).first(),
                    synced_patient_data,
                    message.strip('[]"'),
                )
            elif status_code == 405:
                # Bearer token was missing or invalid
                self.stderr.write('Databank unauthorized error, check OIE for error log and verify API token valid.')
            elif status_code == 400:
                # Extract just the error text from the message
                error_message = message.strip('[]"')
                self.stderr.write(f'Databank sender error for patient {patient_guid}: {error_message}')

    def _update_patient_databank_metadata(self, databank_patient: DatabankConsent, synced_data: Any, message: Optional[str] = None) -> None:
        """Update DatabankConsent last synchronization time, sent data ids."""
        print('DEBUG: ')
