"""Command for sending data to the Databank."""
import json
from collections import defaultdict
from typing import Any, Optional

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models.query import QuerySet
from django.utils import timezone

import requests
from requests.auth import HTTPBasicAuth

from opal.databank.models import DatabankConsent, DataModuleType, SharedData
from opal.legacy.models import LegacyAppointment, LegacyDiagnosis, LegacyPatient, LegacyPatientTestResult
from opal.legacy_questionnaires.models import LegacyAnswerQuestionnaire


class Command(BaseCommand):
    """Command to send the data of consenting databank patients to the external databank."""

    help = "send consenting Patients' data to the databank"  # noqa: A003

    def __init__(self):
        """Prepare some class level fields to help with last_syncrhonization tracking.

        command_called is the time when this command was called
        patient_data_success will have an entry for each patient with value as a dict of bools for each DataModuleType
        Only update the databank_patient.last_synchronized if all booleans are true for that patient.
        This is required to know when we have to re-send failed data in the next cron run.
        """
        super().__init__()
        self.patient_data_success_tracker = defaultdict(lambda: {module: True for module in DataModuleType.choices})
        self.command_called = timezone.now()

    @transaction.atomic
    def handle(self, *args: Any, **kwargs: Any) -> None:  # noqa: WPS231
        """
        Handle sending patients de-identified data to the databank.

        Return 'None'.

        Args:
            args: non-keyword input arguments.
            kwargs: variable keyword input arguments.
        """
        consenting_patients_querysets = {
            DataModuleType.DEMOGRAPHICS: DatabankConsent.objects.filter(has_demographics=True),
            DataModuleType.APPOINTMENTS: DatabankConsent.objects.filter(has_appointments=True),
            DataModuleType.DIAGNOSES: DatabankConsent.objects.filter(has_diagnoses=True),
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
                        self._parse_aggregate_databank_response(aggregate_response, combined_module_data)
            else:
                self.stdout.write(
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

        This function should handle status and errors between Django and OIE only.
        The `_parse_aggregate_databank_response` function handles the status and errors between OIE and Databank.

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
        except requests.exceptions.RequestException as exc:
            # log OIE errors
            self.stderr.write(
                f'Databank sender OIE Error: {exc}',
            )

        if response.status_code == 200:
            # Data sent to OIE successfully, parse aggregate response from databank and update models
            return response.json()
        # TODO: QSCCD-1097 handle all error codes

    def _parse_aggregate_databank_response(self, aggregate_response: json, original_data_sent: list) -> None:
        """Parse the aggregated response message from the databank and update databank models.

        Args:
            aggregate_response: JSON object with a response code & message for each patient data
            original_data_sent: list of data originally sent to OIE
        """
        for identifier, response_object in aggregate_response.items():
            status_code, message = response_object
            # Extract the data type and patient guid from the response identifier string
            module_prefix, patient_guid = identifier.split('_', 1)

            # Try to map the module_prefix to one of our known DataModuleTypes:
            try:
                data_module = DataModuleType(module_prefix.upper())
            except ValueError:
                self.stderr.write(f'Unrecognized module prefix in response: {module_prefix}')

            # Intialize the patient_data_success tracker for this patient
            if patient_guid not in self.patient_data_success_tracker:
                self.patient_data_success_tracker[patient_guid] = {module: True for module in DataModuleType.choices}

            # Handle response codes
            if status_code in {200, 201}:
                # Grab the data for this specific patient using a list comprehension and matching on the patient GUID
                synced_patient_data = next((item for item in original_data_sent if item['GUID'] == patient_guid), None)
                self._update_patient_databank_metadata(
                    DatabankConsent.objects.filter(guid=patient_guid).first(),
                    synced_patient_data,
                    message.strip('[]"'),
                )
            # TODO: QSCCD-1097 handle all error codes
            else:
                # Update the data success tracker to false for this patient & data type
                self.patient_data_success_tracker[patient_guid][data_module] = False

    def _update_patient_databank_metadata(
        self,
        databank_patient: DatabankConsent,
        synced_data: Any,
        message: Optional[str] = None,
    ) -> None:
        """Update DatabankConsent last synchronization time create sent data ids.

        Args:
            databank_patient: Consent instance to be updated
            synced_data: The dataset which was sent to the databank
            message: Optional return message from the databank with additional details
        """
        if message:
            self.stdout.write(f'Databank confirmation of data received for {databank_patient}: {message}')
        # Update databank_patient.last_synchronized if patient_data_success_tracker true for all modules for the patient
        all_successful = all(self.patient_data_success_tracker[databank_patient.guid].values())
        if all_successful:
            databank_patient.last_synchronized = self.command_called
            databank_patient.save()

        # Extract data ids depending on module and save to SharedData instances
        if DataModuleType.DEMOGRAPHICS in synced_data:
            sent_data_id = synced_data.get(DataModuleType.DEMOGRAPHICS)[0].get('patient_id')
            SharedData.objects.create(
                databank_consent=databank_patient,
                data_id=sent_data_id,
                data_type=DataModuleType.DEMOGRAPHICS,
            )
        elif DataModuleType.LABS in synced_data:
            sent_test_result_ids = [
                component['test_result_id']
                for lab in synced_data.get(DataModuleType.LABS, [])
                for component in lab.get('components', [])
                if 'test_result_id' in component
            ]
            shared_data_instances = [
                SharedData(databank_consent=databank_patient, data_id=test_result_id, data_type=DataModuleType.LABS)
                for test_result_id in sent_test_result_ids
            ]
            SharedData.objects.bulk_create(shared_data_instances)
