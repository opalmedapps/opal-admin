# SPDX-FileCopyrightText: Copyright (C) 2024 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Utility functions used by usage statistics app."""

import datetime as dt
from collections import UserDict
from pathlib import Path
from typing import Any

from django.db import models

import pandas as pd

from opal.legacy import models as legacy_models
from opal.patients.models import Relationship
from opal.usage_statistics.models import DailyUserPatientActivity

from . import queries

# Type aliases
type RowData = dict[str, Any]
type UsageStatisticsData = list[RowData]
type ReportData = dict[str, UsageStatisticsData]


class RelationshipMapping(UserDict[str, Any]):
    """Custom patient-user relationship mapping."""

    def __init__(
        self,
        relationships: models.QuerySet[Relationship, dict[str, Any]],
    ) -> None:
        """
        Build relationships dictionary for populating patients' application activities.

        The mapping contains the legacy patient IDs that map to a dictionary with patient ID and usernames.
        The username keys map to a dictionary with the relationship and user IDs.

        The created dictionary contains required values for populating `DailyUserPatientActivity` model.

        Args:
            relationships: patient-caregiver relationships queryset
        """
        relationships_dict = {}

        for rel in relationships:
            legacy_id = rel['patient__legacy_id']
            username = rel['caregiver__user__username']
            username_dict = {
                'relationship_id': rel['id'],
                'user_id': rel['caregiver__user__id'],
            }

            if legacy_id not in relationships_dict:
                relationships_dict[legacy_id] = {'patient_id': rel['patient__id']}

            relationships_dict[legacy_id][username] = username_dict

        super().__init__(relationships_dict)


def annotate_patient_activities(
    activities: models.QuerySet[legacy_models.LegacyPatientActivityLog, dict[str, Any]],
    relationships_dict: RelationshipMapping,
) -> list[DailyUserPatientActivity]:
    """
    Annotate patient's activity records with the fields that are required in `DailyUserPatientActivity` model.

    For each record add `user_relationship_to_patient_id`, `action_by_user_id`, `patient_id` fields.

    Args:
        activities: `LegacyPatientActivityLog` records per patient per day
        relationships_dict: mapping with patient IDs that map to a dictionary with patient ID and usernames

    Returns:
        list of `DailyUserPatientActivity` objects
    """
    patient_activities_list = []

    for activity in activities:
        username = activity.pop('username')
        patient_data = relationships_dict[activity.pop('target_patient_id')]
        activity['user_relationship_to_patient_id'] = patient_data[username]['relationship_id']
        activity['action_by_user_id'] = patient_data[username]['user_id']
        activity['patient_id'] = patient_data['patient_id']
        patient_activities_list.append(DailyUserPatientActivity(**activity))

    return patient_activities_list


def get_aggregated_patient_received_data(
    start_datetime_period: dt.datetime,
    end_datetime_period: dt.datetime,
) -> models.QuerySet[legacy_models.LegacyPatientControl, dict[str, Any]]:
    """
    Retrieve aggregated patients' received data statistics for a given time period.

    The statistics are fetched from the legacy `OpalDB` tables.

    NOTE: The legacy datetime fields are stored in the EST time zone format
    (e.g., zoneinfo.ZoneInfo(key=EST5EDT))), while managed Django models store datetimes in the
    UTC format. Both are time zone aware.

    Args:
        start_datetime_period: the beginning of the time period of app activities being extracted
        end_datetime_period: the end of the time period of app activities being extracted

    Returns:
        Annotated `LegacyPatient` records
    """
    patient_out_ref = models.OuterRef('patient')
    date_added_range = (start_datetime_period, end_datetime_period)
    zero_count = models.Value(0)

    annotation_subqueries = {
        # Subqueries for Appointments
        # The appointment statistics are typically for answering questions like:
        #   - How are active the patients in the appointments category?
        #   - How many patients had appointments in the last day, week, month, etc.?"
        'last_appointment_received': models.Subquery(
            # Retrieve the most recent appointment for every patient relatively to the requesting date range,
            # regardless of how old it might be (e.g., the appointment might be older than the start of the range).
            # Use a slice (e.g., [:1]) instead of get()/first()
            # since the OuterRef cannot be resolved until the queryset is used within a Subquery.
            # https://docs.djangoproject.com/en/5.0/ref/models/expressions/#limiting-the-subquery-to-a-single-row
            legacy_models.LegacyAppointment.objects
            .filter(
                patientsernum=patient_out_ref,
                scheduledstarttime__lt=end_datetime_period,
            )
            .order_by('-scheduledstarttime')
            .values('scheduledstarttime')[:1],
        ),
        'next_appointment': models.Subquery(
            # Retrieve the closest open/active appointment for every patient relatively to the requesting
            # date range, regardless of how far it might be.
            # E.g., the appointment might be later than the end of the range.
            legacy_models.LegacyAppointment.objects
            .filter(
                patientsernum=patient_out_ref,
                state='Active',
                status='Open',
                scheduledstarttime__gt=end_datetime_period,
            )
            .order_by('scheduledstarttime')
            .values('scheduledstarttime')[:1],
        ),
        'appointments_received': models.functions.Coalesce(
            # Use Coalesce to prevent an aggregate Count() from returning a None and return 0 instead.
            models.Subquery(
                # Aggregate how many appointments for every patient were received in the given date range.
                legacy_models.LegacyAppointment.objects
                .filter(
                    patientsernum=patient_out_ref,
                    date_added__range=date_added_range,
                )
                .values(
                    'patientsernum',
                )
                .annotate(
                    count=models.Count('appointmentsernum'),
                )
                .values('count'),
            ),
            zero_count,
        ),
        # Subqueries for Documents
        'last_document_received': models.Subquery(
            # Retrieve the latest received document for every patient, regardless of how old it might be.
            legacy_models.LegacyDocument.objects
            .filter(
                patientsernum=patient_out_ref,
                dateadded__lt=end_datetime_period,
            )
            .order_by('-dateadded')
            .values('dateadded')[:1],
        ),
        'documents_received': models.functions.Coalesce(
            # Use Coalesce to prevent an aggregate Count() from returning a None and return 0 instead.
            models.Subquery(
                # Aggregate how many documents for every patient were received in the given date range.
                legacy_models.LegacyDocument.objects
                .filter(
                    patientsernum=patient_out_ref,
                    dateadded__range=date_added_range,
                )
                .values(
                    'patientsernum',
                )
                .annotate(
                    count=models.Count('documentsernum'),
                )
                .values('count'),
            ),
            zero_count,
        ),
        # Subqueries for Educational Materials
        'last_educational_material_received': models.Subquery(
            # Retrieve the latest received educational material for every patient,
            # regardless of how old it might be.
            legacy_models.LegacyEducationalMaterial.objects
            .filter(
                patientsernum=patient_out_ref,
                date_added__lt=end_datetime_period,
            )
            .order_by('-date_added')
            .values('date_added')[:1],
        ),
        'educational_materials_received': models.functions.Coalesce(
            # Use Coalesce to prevent an aggregate Count() from returning a None and return 0 instead.
            models.Subquery(
                # Aggregate how many educational materials for every patient were received in the given date range.
                legacy_models.LegacyEducationalMaterial.objects
                .filter(
                    patientsernum=patient_out_ref,
                    date_added__range=date_added_range,
                )
                .values(
                    'patientsernum',
                )
                .annotate(
                    count=models.Count('educationalmaterialsernum'),
                )
                .values('count'),
            ),
            zero_count,
        ),
        # Subqueries for Questionnaires
        'last_questionnaire_received': models.Subquery(
            # Retrieve the latest received questionnaire for every patient, regardless of how old it might be.
            legacy_models.LegacyQuestionnaire.objects
            .filter(
                patientsernum=patient_out_ref,
                date_added__lt=end_datetime_period,
            )
            .order_by('-date_added')
            .values('date_added')[:1],
        ),
        'questionnaires_received': models.functions.Coalesce(
            # Use Coalesce to prevent an aggregate Count() from returning a None and return 0 instead.
            models.Subquery(
                # Aggregate how many questionnaires for every patient were received in the given date range.
                legacy_models.LegacyQuestionnaire.objects
                .filter(
                    patientsernum=patient_out_ref,
                    date_added__range=date_added_range,
                )
                .values(
                    'patientsernum',
                )
                .annotate(
                    count=models.Count('questionnairesernum'),
                )
                .values('count'),
            ),
            zero_count,
        ),
        # TODO: QSCCD-2209 - add a lab_groups_received count that shows how many "complete lab groups" were received.
        # Subqueries for Labs
        'last_lab_received': models.Subquery(
            # Retrieve the latest received lab result for every patient, regardless of how old it might be.
            legacy_models.LegacyPatientTestResult.objects
            .filter(
                patient_ser_num=patient_out_ref,
                date_added__lt=end_datetime_period,
            )
            .order_by('-date_added')
            .values('date_added')[:1],
        ),
        'labs_received': models.functions.Coalesce(
            # Use Coalesce to prevent an aggregate Count() from returning a None and return 0 instead.
            models.Subquery(
                # Aggregate how many lab results for every patient were received in the given date range.
                legacy_models.LegacyPatientTestResult.objects
                .filter(
                    patient_ser_num=patient_out_ref,
                    date_added__range=date_added_range,
                )
                .values(
                    'patient_ser_num',
                )
                .annotate(
                    count=models.Count('patient_test_result_ser_num'),
                )
                .values('count'),
            ),
            zero_count,
        ),
        # NOTE! The action_date indicates the date when the patients' data were received.
        # It is not the date when the activity statistics were populated.
        'action_date': models.Value(start_datetime_period.date()),
    }

    return legacy_models.LegacyPatientControl.objects.annotate(  # type: ignore[no-any-return]
        **annotation_subqueries,
    ).values(
        'patient',
        *annotation_subqueries,
    )


def export_data(
    data_set: list[dict[str, Any]] | dict[str, Any],
    file_path: Path,
) -> None:
    """
    Export the data into a csv/xlsx file to facilitate the use of the new usage stats queries.

    The function currently only support for csv and xlsx format, a value error will be raised for other cases.

    Args:
        data_set: the data set  to be exported
        file_path: the destination path of the export file

    Raises:
        ValueError: If the file_name format is not supported
    """
    # Generate dataframe from the queryset given
    if not data_set:
        raise ValueError('Invalid input, unable to export empty data')
    if isinstance(data_set, list):
        data_set_columns = list(data_set[0].keys())
    else:
        data_set_columns = list(data_set.keys())
        data_set = [data_set]
    dataframe = pd.DataFrame.from_records(data_set, columns=data_set_columns)
    dataframe = dataframe.map(
        lambda col: _convert_to_naive(col) if isinstance(col, pd.Timestamp) else col,
    )
    # Generate the file in the required path and format
    match file_path.suffix:
        case '.csv':
            dataframe.to_csv(file_path, index=False)
        case '.xlsx':
            dataframe.to_excel(file_path, index=False)
        case _:
            raise ValueError('Invalid file format, please use either csv or xlsx')


def get_summary_report(
    start_date: dt.date,
    end_date: dt.date,
    group_by: queries.GroupByComponent,
) -> ReportData:
    """
    Fetch summary usage statistics report.

    The statistics include summaries on grouped registration codes, caregivers, patients, and device identifiers.

    Args:
        start_date: the beginning of the time period of the summary usage statistics (inclusive).
        end_date: the end of the time period of the of the summary usage statistics (inclusive).
        group_by: the date component to group by.

    Returns:
        grouped summary usage statistics for a given time period.
    """
    return {
        'registration_summary': [queries.fetch_registration_summary(start_date, end_date)],
        # Note this returns the same columns as `registration_summary`, it just groups by a date component
        'grouped_registration_summary': queries.fetch_grouped_registration_summary(start_date, end_date, group_by),
        'caregivers_summary': [queries.fetch_caregivers_summary(start_date, end_date)],
        'fetch_patients_summary': [queries.fetch_patients_summary(start_date, end_date)],
        'devices_summary': [queries.fetch_devices_summary(start_date, end_date)],
    }


def get_received_data_report(
    start_date: dt.date,
    end_date: dt.date,
    group_by: queries.GroupByComponent,
) -> ReportData:
    """
    Fetch received data usage statistics report.

    The statistics include summaries on the received clinical data (e.g., appointments, labs, clinical notes,
    diagnosis), educational materials, questionnaires, and documents.

    Args:
        start_date: the beginning of the time period of the received data usage statistics (inclusive).
        end_date: the end of the time period of the of the received data usage statistics (inclusive).
        group_by: the date component to group by.

    Returns:
        grouped received data usage statistics for a given time period.
    """
    return {
        'received_clinical_data_summary': [queries.fetch_patients_received_clinical_data_summary(start_date, end_date)],
        'received_labs_summary': queries.fetch_received_labs_summary(start_date, end_date, group_by),
        'received_appointments_summary': queries.fetch_received_appointments_summary(start_date, end_date, group_by),
        'received_educational_materials_summary': queries.fetch_received_educational_materials_summary(
            start_date,
            end_date,
            group_by,
        ),
        'received_documents_summary': queries.fetch_received_documents_summary(start_date, end_date, group_by),
        'received_questionnaires_summary': queries.fetch_received_questionnaires_summary(
            start_date,
            end_date,
            group_by,
        ),
    }


def get_app_activity_report(
    start_date: dt.date,
    end_date: dt.date,
    group_by: queries.GroupByComponent,
) -> ReportData:
    """
    Fetch mobile application activity usage statistics report.

    The statistics include summaries on the logins, users' clicks, patients' clicks, latest logins.

    Args:
        start_date: the beginning of the time period of the application activity usage statistics (inclusive).
        end_date: the end of the time period of the application activity usage statistics (inclusive).
        group_by: the date component to group by.

    Returns:
        grouped application activity usage statistics for a given time period.
    """
    return {
        'logins_summary': queries.fetch_logins_summary(start_date, end_date, group_by),
        'users_clicks_summary': queries.fetch_users_clicks_summary(start_date, end_date, group_by),
        'user_patient_clicks_summary': queries.fetch_user_patient_clicks_summary(start_date, end_date, group_by),
        'users_latest_login_year_summary': [queries.fetch_users_latest_login_year_summary(start_date, end_date)],
    }


def _convert_to_naive(datetime: pd.Timestamp) -> pd.Timestamp:
    """
    Clean the time zone info of the input datetime data if it exists.

    Args:
        datetime: the datetime data

    Returns:
        the datetime value without time zone information
    """
    return datetime.tz_convert(None) if datetime.tzinfo is not None else datetime
