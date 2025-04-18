# SPDX-FileCopyrightText: Copyright (C) 2023 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Command for sending data to the Databank."""

import json
from collections import defaultdict
from http import HTTPStatus
from typing import TYPE_CHECKING, Any

from django.conf import settings
from django.core.management.base import BaseCommand, CommandParser
from django.db.models import Model, QuerySet
from django.utils import timezone

import requests
from requests.auth import HTTPBasicAuth

from opal.databank.models import DatabankConsent, DataModuleType, SharedData
from opal.legacy.models import LegacyAppointment, LegacyDiagnosis, LegacyPatient, LegacyPatientTestResult
from opal.legacy_questionnaires.models import LegacyAnswerQuestionnaire

if TYPE_CHECKING:
    from datetime import datetime

type CombinedModuleData = list[dict[str, Any]]
type DatabankQuerySet = QuerySet[Model, dict[str, Any]] | CombinedModuleData


class Command(BaseCommand):
    """Command to send the data of consenting databank patients to the external databank."""

    help = "send consenting Patients' data to the databank"

    def __init__(self) -> None:
        """
        Prepare some class level fields to help with last_synchronized tracking.

        - called_at is the time when this command was called
        - patient_data_success_tracker will have an entry for each patient
          with the value being a dictionary of booleans for each DataModuleType

        We only update the databank_patient.last_synchronized if all data type booleans are true for that patient.
        This is required to know when we have to re-send failed data in the next cron run.
        """
        super().__init__()
        self.patient_data_success_tracker: dict[str, dict[DataModuleType, bool]] = {}
        self.called_at: datetime = timezone.now()

    def add_arguments(self, parser: CommandParser) -> None:
        """
        Add arguments to the command.

        Args:
            parser: the command parser to add arguments to
        """
        parser.add_argument(
            '--request-timeout',
            type=int,
            required=False,
            default=120,
            help='Specify maximum wait time per API call to the databank [seconds]. Default 120.',
        )

    def handle(self, *args: Any, **options: Any) -> None:
        """
        Handle sending patients de-identified data to the databank.

        Return 'None'.

        Args:
            args: non-keyword input arguments.
            options: additional keyword input arguments.
        """
        consenting_patients_querysets = {
            DataModuleType.DEMOGRAPHICS: DatabankConsent.objects.filter(has_demographics=True),
            DataModuleType.APPOINTMENTS: DatabankConsent.objects.filter(has_appointments=True),
            DataModuleType.DIAGNOSES: DatabankConsent.objects.filter(has_diagnoses=True),
            DataModuleType.LABS: DatabankConsent.objects.filter(has_labs=True),
            DataModuleType.QUESTIONNAIRES: DatabankConsent.objects.filter(has_questionnaires=True),
        }

        request_timeout: int = options.get('request_timeout', 120)
        self.stdout.write(
            f'Sending databank data with {request_timeout} seconds timeout for source system response.',
        )
        for module, queryset in consenting_patients_querysets.items():
            patients_list = list(queryset.iterator())
            patients_count = len(patients_list)

            if patients_count > 0:
                self.stdout.write(
                    f'Number of {DataModuleType(module).label}-consenting patients is: {queryset.count()}',
                )

                # Retrieve patient data for each module type and send all at once
                combined_module_data: CombinedModuleData = []
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
                    aggregate_response = self._request_and_handle_response(
                        {'patientList': combined_module_data},
                        request_timeout,
                    )
                    if aggregate_response:
                        self._parse_aggregate_databank_response(aggregate_response, combined_module_data)
            else:
                self.stdout.write(
                    f'No patients found consenting to {DataModuleType(module).label} data donation.',
                )
        # Finally, update last_synchronization time for all patients
        self._update_patients_last_synchronization()

    def _retrieve_databank_data_for_patient(
        self,
        databank_patient: DatabankConsent,
        module: DataModuleType,
    ) -> DatabankQuerySet | None:
        """
        Use model managers to retrieve databank data for a consenting patient.

        Args:
            databank_patient: Patient consenting for this databank module
            module: databank data module enum type

        Raises:
            ValueError: If an invalid DateModuleType value is provided or if a patient is missing the legacy id

        Returns:
            JSON string of the patient's databank information for this module
        """
        databank_data: DatabankQuerySet | None = None
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
                f'{len(databank_data)} instances of {DataModuleType(module).label} found for {databank_patient.patient}',
            )
        else:
            self.stdout.write(
                f'No {DataModuleType(module).label} data found for {databank_patient.patient}',
            )

        return databank_data

    def _nest_and_serialize_queryset(
        self,
        guid: str,
        queryset: DatabankQuerySet,
        nesting_key: str,
    ) -> dict[str, str | CombinedModuleData]:
        """
        Pull the GUID to the top element and nest the rest of the qs records into a single dict.

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
        # Extra nesting requirements for questionnaires to create question answer list under questionnaire identifiers
        elif nesting_key == 'QSTN':
            groups2 = defaultdict(list)
            for item2 in data:
                # Group by answer questionnaire id, date answered, questionnaire id and title
                key2 = (
                    item2.pop('answer_questionnaire_id', None),
                    item2.pop('creation_date', None),
                    item2.pop('questionnaire_id', None),
                    item2.pop('questionnaire_title', None),
                )
                groups2[key2].append(item2)
            # Convert the defaultdict to the final format
            data = [
                {
                    'answer_questionnaire_id': key2[0],
                    'creation_date': key2[1],
                    'questionnaire_id': key2[2],
                    'questionnaire_title': key2[3],
                    'question_answers': value2,
                }
                for key2, value2 in groups2.items()
            ]
        return {'GUID': guid, nesting_key: data}

    def _request_and_handle_response(
        self,
        data: dict[str, CombinedModuleData],
        request_timeout: int,
    ) -> dict[str, Any] | None:
        """
        Send databank dataset to the source system and handle immediate response from source system.

        This function should handle status and errors between Django and source system only.
        The `_parse_aggregate_databank_response` function handles the status
        and errors between source system and Databank.

        Args:
            data: Databank dictionary of one of the five module types.
            request_timeout: Maximum seconds to wait for response per api call to the source system

        Returns:
            Any: json object containing response for each individual patient message, or empty if send failed
        """
        try:
            response = requests.post(
                url=f'{settings.SOURCE_SYSTEM_HOST}/databank/post',
                auth=HTTPBasicAuth(settings.SOURCE_SYSTEM_USER, settings.SOURCE_SYSTEM_PASSWORD),
                data=json.dumps(data, default=str),
                headers={'Content-Type': 'application/json'},
                timeout=request_timeout,
            )
        except requests.exceptions.RequestException as exc:
            # Connection details for source system might be misconfigured
            self.stderr.write(
                f'Source system connection Error: {exc}',
            )
            return None

        if response and response.status_code == HTTPStatus.OK:
            # Data sent to source system successfully, parse aggregate response from databank and update models
            response_data: dict[str, Any] = response.json()
            return response_data

        # Specific error occurred between Django, Nginx, and/or source system communications
        self.stderr.write(
            f'{response.status_code} source system response error: ' + response.content.decode(),
        )

        return None

    def _parse_aggregate_databank_response(
        self,
        aggregate_response: dict[str, list[Any]],
        original_data_sent: CombinedModuleData,
    ) -> None:
        """
        Parse the aggregated response message from the databank and update databank models.

        Args:
            aggregate_response: JSON object with a response code & message for each patient data
            original_data_sent: list of data originally sent to source system
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

            # Initialize the patient_data_success tracker for this patient
            if patient_guid not in self.patient_data_success_tracker:
                self.patient_data_success_tracker[patient_guid] = dict.fromkeys(DataModuleType, True)

            # Handle response codes
            if status_code in {HTTPStatus.OK, HTTPStatus.CREATED}:
                # Grab the data for this specific patient using a generator expression and matching on the patient GUID
                synced_patient_data = next((item for item in original_data_sent if item['GUID'] == patient_guid), None)
                self._update_databank_patient_shared_data(
                    DatabankConsent.objects.get(guid=patient_guid),
                    synced_patient_data,
                    message.strip('[]"'),
                )
            else:
                self.patient_data_success_tracker[patient_guid][data_module] = False
                self.stderr.write(
                    f'{status_code} error for patient {patient_guid}: ' + message.strip('[]"'),
                )

    def _update_databank_patient_shared_data(
        self,
        databank_patient: DatabankConsent,
        synced_data: Any,
        message: str | None = None,
    ) -> None:
        """
        Create `SharedData` instances for a given patient.

        Args:
            databank_patient: Consent instance to be updated
            synced_data: The dataset which was sent to the databank
            message: Optional return message from the databank with additional details
        """
        if message:
            self.stdout.write(f'Databank confirmation of data received for {databank_patient}: {message}')
        # Extract data ids depending on module and save to SharedData instances
        if DataModuleType.DEMOGRAPHICS in synced_data:
            sent_patient_id = synced_data.get(DataModuleType.DEMOGRAPHICS)[0].get('patient_id')
            SharedData.objects.create(
                databank_consent=databank_patient,
                data_id=sent_patient_id,
                data_type=DataModuleType.DEMOGRAPHICS,
            )
        elif DataModuleType.LABS in synced_data:
            sent_test_result_ids = [
                component['test_result_id']
                for lab in synced_data.get(DataModuleType.LABS, [])
                for component in lab.get('components', [])
                if 'test_result_id' in component
            ]
            self._create_shared_data_instances(databank_patient, DataModuleType.LABS, sent_test_result_ids)
        elif DataModuleType.DIAGNOSES in synced_data:
            sent_diagnosis_ids = [
                diagnosis['diagnosis_id'] for diagnosis in synced_data.get(DataModuleType.DIAGNOSES, [])
            ]
            self._create_shared_data_instances(databank_patient, DataModuleType.DIAGNOSES, sent_diagnosis_ids)
        elif DataModuleType.QUESTIONNAIRES in synced_data:
            sent_questionnaire_answer_ids = [
                questionnaire_answer['answer_questionnaire_id']
                for questionnaire_answer in synced_data.get(DataModuleType.QUESTIONNAIRES, [])
            ]
            self._create_shared_data_instances(
                databank_patient,
                DataModuleType.QUESTIONNAIRES,
                sent_questionnaire_answer_ids,
            )
        elif DataModuleType.APPOINTMENTS in synced_data:
            sent_appointment_ids = [
                appointment['appointment_id'] for appointment in synced_data.get(DataModuleType.APPOINTMENTS, [])
            ]
            self._create_shared_data_instances(databank_patient, DataModuleType.APPOINTMENTS, sent_appointment_ids)

    def _create_shared_data_instances(
        self,
        databank_patient: DatabankConsent,
        data_module_type: DataModuleType,
        id_list: list[Any],
    ) -> None:
        """
        Bulk create SharedData instances given the module type and id list.

        Args:
            databank_patient: The consent instance whose data was successfully synced with LORIS
            data_module_type: The data type
            id_list: The list of specific ids of module data that was successfully synced
        """
        shared_data_instances = [
            SharedData(databank_consent=databank_patient, data_id=data_id, data_type=data_module_type)
            for data_id in id_list
        ]
        SharedData.objects.bulk_create(shared_data_instances)

    def _update_patients_last_synchronization(self) -> None:
        """Update the `databank_patient.last_synchronized` for all patients based on the success tracker."""
        for guid, module_successes in self.patient_data_success_tracker.items():
            consent_instance = DatabankConsent.objects.get(guid=guid)
            if all(module_successes.values()):
                consent_instance.last_synchronized = self.called_at
                consent_instance.save()
