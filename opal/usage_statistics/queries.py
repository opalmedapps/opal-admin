# SPDX-FileCopyrightText: Copyright (C) 2024 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Statistics queries used by usage statistics app."""

import datetime as dt
from collections import Counter
from typing import Any

from django.conf import settings
from django.db import models
from django.db.models.functions import Cast, ExtractYear, Trunc, TruncDay, TruncMonth, TruncYear

from opal.caregivers import models as caregivers_models
from opal.legacy import models as legacy_models
from opal.patients import models as patients_models
from opal.users import models as users_models

from .common import GroupByComponent
from .models import DailyPatientDataReceived, DailyUserAppActivity, DailyUserPatientActivity

# GROUP REPORTING


def fetch_registration_summary(
    start_date: dt.date,
    end_date: dt.date,
) -> dict[str, Any]:
    """
    Fetch registration summary from `RegistrationCode` model.

    Args:
        start_date: the beginning of the time period of the registration summary (inclusive)
        end_date: the end of the time period of the registration summary (inclusive)

    Returns:
        registration summary for a given time period
    """
    return caregivers_models.RegistrationCode.objects.filter(
        created_at__date__gte=start_date,
        created_at__date__lte=end_date,
    ).aggregate(
        uncompleted_registration=models.Count(
            'id',
            filter=~models.Q(status=caregivers_models.RegistrationCodeStatus.REGISTERED),
        ),
        completed_registration=models.Count(
            'id',
            filter=models.Q(status=caregivers_models.RegistrationCodeStatus.REGISTERED),
        ),
        total_registration_codes=models.F('uncompleted_registration') + models.F('completed_registration'),
    )


def fetch_grouped_registration_summary(
    start_date: dt.date,
    end_date: dt.date,
    group_by: GroupByComponent = GroupByComponent.DAY,
) -> list[dict[str, Any]]:
    """
    Fetch grouped registration summary from `RegistrationCode` model.

    Args:
        start_date: the beginning of the time period of the registration summary (inclusive)
        end_date: the end of the time period of the registration summary (inclusive)
        group_by: the date component to group by

    Returns:
        grouped registration summary for given time period and grouping component
    """
    queryset = caregivers_models.RegistrationCode.objects.filter(
        created_at__date__gte=start_date,
        created_at__date__lte=end_date,
    )

    queryset = _annotate_queryset_with_grouping_field(queryset, 'created_at', group_by)
    group_field = group_by.name.lower()

    return list(
        queryset.values(
            group_field,
        )
        .annotate(
            uncompleted_registration=models.Count(
                'id',
                filter=~models.Q(status=caregivers_models.RegistrationCodeStatus.REGISTERED),
            ),
            completed_registration=models.Count(
                'id',
                filter=models.Q(status=caregivers_models.RegistrationCodeStatus.REGISTERED),
            ),
            total_registration_codes=models.F('uncompleted_registration') + models.F('completed_registration'),
        )
        .order_by(f'-{group_field}'),
    )


def fetch_caregivers_summary(
    start_date: dt.date,
    end_date: dt.date,
) -> dict[str, Any]:
    """
    Fetch grouped caregivers summary from `Caregiver` model.

    Args:
        start_date: the beginning of the time period of the caregivers summary (inclusive)
        end_date: the end of the time period of the caregivers summary (inclusive)

    Returns:
        caregivers summary for a given time period
    """
    lang_codes = [lang[0] for lang in settings.LANGUAGES]
    lang_dict = {lang: models.Count('id', filter=models.Q(language=lang)) for lang in lang_codes}

    return users_models.Caregiver.objects.filter(
        date_joined__date__gte=start_date,
        date_joined__date__lte=end_date,
    ).aggregate(
        caregivers_total=models.Count('id'),
        caregivers_registered=models.Count('id', filter=models.Q(is_active=True)),
        caregivers_unregistered=models.Count('id', filter=models.Q(is_active=False)),
        never_logged_in_after_registration=models.Count('id', filter=models.Q(is_active=True, last_login=None)),
        **lang_dict,
    )


def fetch_patients_summary(
    start_date: dt.date,
    end_date: dt.date,
) -> dict[str, Any]:
    """
    Fetch grouped patients summary from `Patient` model.

    Args:
        start_date: the beginning of the time period of the patients summary (inclusive)
        end_date: the end of the time period of the patients summary (inclusive)

    Returns:
        patients summary for a given time period
    """
    access_types = [access_type[0] for access_type in patients_models.DataAccessType.choices]
    access_dict = {}
    for access_type in access_types:
        key_name = f'access_{access_type.lower()}'
        access_dict[key_name] = models.Count('id', filter=models.Q(data_access=access_type))

    return patients_models.Patient.objects.filter(
        created_at__date__gte=start_date,
        created_at__date__lte=end_date,
    ).aggregate(
        total=models.Count('id'),
        deceased=models.Count('id', filter=models.Q(date_of_death__isnull=False)),
        male=models.Count('id', filter=models.Q(sex=patients_models.SexType.MALE)),
        female=models.Count('id', filter=models.Q(sex=patients_models.SexType.FEMALE)),
        sex_other=models.Count('id', filter=models.Q(sex=patients_models.SexType.OTHER)),
        sex_unknown=models.Count('id', filter=models.Q(sex=patients_models.SexType.UNKNOWN)),
        **access_dict,
    )


# TODO: QSCCD-2168
# Use Django's `Device` model instead of `LegacyPatientDeviceIdentifier` once QSCCD-628 and QSCCD-630 are finished.
def fetch_devices_summary(
    start_date: dt.date,
    end_date: dt.date,
) -> dict[str, Any]:
    """
    Fetch grouped device identifiers summary from `LegacyPatientDeviceIdentifier` model.

    Args:
        start_date: the beginning of the time period of the device identifiers summary (inclusive)
        end_date: the end of the time period of the device identifiers summary (inclusive)

    Returns:
        device identifiers summary for a given time period
    """
    return legacy_models.LegacyPatientDeviceIdentifier.objects.filter(
        last_updated__date__gte=start_date,
        last_updated__date__lte=end_date,
    ).aggregate(
        device_total=models.Count('patient_device_identifier_ser_num'),
        device_ios=models.Count(
            'patient_device_identifier_ser_num',
            filter=models.Q(device_type=0),
        ),
        device_android=models.Count(
            'patient_device_identifier_ser_num',
            filter=models.Q(device_type=1),
        ),
        device_browser=models.Count(
            'patient_device_identifier_ser_num',
            filter=models.Q(device_type=3),
        ),
    )


def fetch_patients_received_clinical_data_summary(
    start_date: dt.date,
    end_date: dt.date,
) -> dict[str, Any]:
    """
    Fetch grouped patients received data summary from the `DailyPatientDataReceived` model.

    The summary includes only clinical data (e.g., appointments, labs, clinical notes, diagnosis).

    Args:
        start_date: the beginning of the time period of the patients received data summary (inclusive)
        end_date: the end of the time period of the patients received data summary (inclusive)

    Returns:
        patients received data summary for a given time period
    """
    aggregated_patients_received_data = {
        'no_appointments_labs_notes': models.Count(
            'id',
            filter=models.Q(
                last_appointment_received=None,
                last_lab_received=None,
                last_document_received=None,
            ),
        ),
        'has_appointments_only': models.Count(
            'id',
            filter=models.Q(
                last_appointment_received__isnull=False,
                last_lab_received=None,
                last_document_received=None,
            ),
        ),
        'has_labs_only': models.Count(
            'id',
            filter=models.Q(
                last_appointment_received=None,
                last_lab_received__isnull=False,
                last_document_received=None,
            ),
        ),
        'has_clinical_notes_only': models.Count(
            'id',
            filter=models.Q(
                last_appointment_received=None,
                last_lab_received=None,
                last_document_received__isnull=False,
            ),
        ),
        'receiving_new_data_total': models.Count(
            'id',
            filter=models.Q(
                models.Q(last_appointment_received__isnull=False)
                | models.Q(last_lab_received__isnull=False)
                | models.Q(last_document_received__isnull=False),
            ),
        ),
    }

    return DailyPatientDataReceived.objects.filter(
        action_date__gte=start_date,
        action_date__lte=end_date,
    ).aggregate(
        **aggregated_patients_received_data,
    )


def fetch_logins_summary(
    start_date: dt.date,
    end_date: dt.date,
    group_by: GroupByComponent = GroupByComponent.DAY,
) -> list[dict[str, Any]]:
    """
    Fetch grouped logins summary from `DailyUserAppActivity` model.

    Args:
        start_date: the beginning of the time period of the logins summary (inclusive)
        end_date: the end of the time period of the logins summary (inclusive)
        group_by: the date component to group by. By default it is grouped by day.

    Returns:
        grouped logins summary for a given time period
    """
    queryset = DailyUserAppActivity.objects.filter(
        action_date__gte=start_date,
        action_date__lte=end_date,
    )

    queryset = _annotate_queryset_with_grouping_field(queryset, 'action_date', group_by)
    group_field = group_by.name.lower()

    return list(
        queryset.values(
            group_field,
        )
        .annotate(
            total_logins=models.Sum('count_logins'),
            unique_user_logins=models.Count('action_by_user', distinct=True),
            avg_logins_per_user=models.F('total_logins') / models.F('unique_user_logins'),
        )
        .order_by(f'-{group_field}'),
    )


def fetch_users_clicks_summary(
    start_date: dt.date,
    end_date: dt.date,
    group_by: GroupByComponent = GroupByComponent.DAY,
) -> list[dict[str, Any]]:
    """
    Fetch grouped users' clicks from `DailyUserAppActivity` model.

    Args:
        start_date: the beginning of the time period of the users' clicks summary (inclusive)
        end_date: the end of the time period of the users' clicks summary (inclusive)
        group_by: the date component to group by. By default it is grouped by day.

    Returns:
        grouped users' clicks summary for a given time period
    """
    queryset = DailyUserAppActivity.objects.filter(
        action_date__gte=start_date,
        action_date__lte=end_date,
    )

    queryset = _annotate_queryset_with_grouping_field(queryset, 'action_date', group_by)
    group_field = group_by.name.lower()

    # TODO: QSCCD-2173 - add count of the announcement clicks
    return list(
        queryset.values(
            group_field,
        )
        .annotate(
            login_count=models.Sum('count_logins'),
            feedback_count=models.Sum('count_feedback'),
            update_security_answers_count=models.Sum('count_update_security_answers'),
            update_passwords_count=models.Sum('count_update_passwords'),
        )
        .order_by(f'-{group_field}'),
    )


def fetch_user_patient_clicks_summary(
    start_date: dt.date,
    end_date: dt.date,
    group_by: GroupByComponent = GroupByComponent.DAY,
) -> list[dict[str, Any]]:
    """
    Fetch grouped user's clicks on behalf of a patient from `DailyUserPatientActivity` model.

    Args:
        start_date: the beginning of the time period of the patients' clicks summary (inclusive)
        end_date: the end of the time period of the patients' clicks summary (inclusive)
        group_by: the date component to group by. By default it is grouped by day.

    Returns:
        grouped patients' clicks summary for a given time period
    """
    queryset = DailyUserPatientActivity.objects.filter(
        action_date__gte=start_date,
        action_date__lte=end_date,
    )

    queryset = _annotate_queryset_with_grouping_field(queryset, 'action_date', group_by)
    group_field = group_by.name.lower()

    return list(
        queryset.values(
            group_field,
        )
        .annotate(
            checkins_count=models.Sum('count_checkins'),
            documents_count=models.Sum('count_documents'),
            educational_materials_count=models.Sum('count_educational_materials'),
            completed_questionnaires_count=models.Sum('count_questionnaires_complete'),
            labs_count=models.Sum('count_labs'),
        )
        .order_by(f'-{group_field}'),
    )


def fetch_received_labs_summary(
    start_date: dt.date,
    end_date: dt.date,
    group_by: GroupByComponent = GroupByComponent.DAY,
) -> list[dict[str, Any]]:
    """
    Fetch received lab results statistics from the `DailyPatientDataReceived` model.

    The results can be grouped by date (by default), by month, by year.

    Args:
        start_date: the beginning of the time period of the received lab results summary (inclusive)
        end_date: the end of the time period of the received lab results summary (inclusive)
        group_by: the date component to group by. By default it is grouped by day.

    Returns:
        grouped received lab results summary for a given time period
    """
    return _fetch_received_medical_records_summary(
        start_date=start_date,
        end_date=end_date,
        filters={
            'labs_received__gt': models.Value(0),
        },
        annotated_summary_fields={
            'total_received_labs': models.Sum('labs_received'),
            'total_unique_patients': models.Count('patient', distinct=True),
            'avg_received_labs_per_patient': models.F('total_received_labs') / models.F('total_unique_patients'),
        },
        group_by=group_by,
    )


def fetch_received_appointments_summary(
    start_date: dt.date,
    end_date: dt.date,
    group_by: GroupByComponent = GroupByComponent.DAY,
) -> list[dict[str, Any]]:
    """
    Fetch received appointments summary from the `DailyPatientDataReceived` model.

    The results can be grouped by day (by default), by month, by year.

    Args:
        start_date: the beginning of the time period of the received appointments summary (inclusive)
        end_date: the end of the time period of the received appointments summary (inclusive)
        group_by: the date component to group by. By default it is grouped by day.

    Returns:
        grouped received appointments summary for a given time period
    """
    return _fetch_received_medical_records_summary(
        start_date=start_date,
        end_date=end_date,
        filters={'appointments_received__gt': models.Value(0)},
        annotated_summary_fields={
            'total_received_appointments': models.Sum('appointments_received'),
            'total_unique_patients': models.Count('patient', distinct=True),
            'avg_received_appointments_per_patient': models.F('total_received_appointments')
            / models.F('total_unique_patients'),
        },
        group_by=group_by,
    )


# TODO: QSCCD-2173 - implement fetch_received_diagnoses_summary() function once diagnoses_received field is added.


def fetch_received_educational_materials_summary(
    start_date: dt.date,
    end_date: dt.date,
    group_by: GroupByComponent = GroupByComponent.DAY,
) -> list[dict[str, Any]]:
    """
    Fetch received educational materials summary from the `DailyPatientDataReceived` model.

    The results can be grouped by day (by default), by month, by year.

    Args:
        start_date: the beginning of the time period of the received educational materials summary (inclusive)
        end_date: the end of the time period of the received educational materials summary (inclusive)
        group_by: the date component to group by. By default it is grouped by day.

    Returns:
        grouped received educational materials summary for a given time period
    """
    return _fetch_received_medical_records_summary(
        start_date=start_date,
        end_date=end_date,
        filters={'educational_materials_received__gt': models.Value(0)},
        annotated_summary_fields={
            'total_received_edu_materials': models.Sum('educational_materials_received'),
            'total_unique_patients': models.Count('patient', distinct=True),
            'avg_received_edu_materials_per_patient': models.F('total_received_edu_materials')
            / models.F('total_unique_patients'),
        },
        group_by=group_by,
    )


def fetch_received_documents_summary(
    start_date: dt.date,
    end_date: dt.date,
    group_by: GroupByComponent = GroupByComponent.DAY,
) -> list[dict[str, Any]]:
    """
    Fetch received documents summary from the `DailyPatientDataReceived` model.

    The results can be grouped by day (by default), by month, by year.

    Args:
        start_date: the beginning of the time period of the received documents summary (inclusive)
        end_date: the end of the time period of the received documents summary (inclusive)
        group_by: the date component to group by. By default it is grouped by day.

    Returns:
        grouped received documents summary for a given time period
    """
    return _fetch_received_medical_records_summary(
        start_date=start_date,
        end_date=end_date,
        filters={'documents_received__gt': models.Value(0)},
        annotated_summary_fields={
            'total_received_documents': models.Sum('documents_received'),
            'total_unique_patients': models.Count('patient', distinct=True),
            'avg_received_documents_per_patient': models.F('total_received_documents')
            / models.F('total_unique_patients'),
        },
        group_by=group_by,
    )


def fetch_received_questionnaires_summary(
    start_date: dt.date,
    end_date: dt.date,
    group_by: GroupByComponent = GroupByComponent.DAY,
) -> list[dict[str, Any]]:
    """
    Fetch received questionnaires summary from the `DailyPatientDataReceived` model.

    The results can be grouped by day (by default), by month, by year.

    Args:
        start_date: the beginning of the time period of the received questionnaires summary (inclusive)
        end_date: the end of the time period of the received questionnaires summary (inclusive)
        group_by: the date component to group by. By default it is grouped by day.

    Returns:
        grouped received questionnaires summary for a given time period
    """
    return _fetch_received_medical_records_summary(
        start_date=start_date,
        end_date=end_date,
        filters={'questionnaires_received__gt': models.Value(0)},
        annotated_summary_fields={
            'total_received_questionnaires': models.Sum('questionnaires_received'),
            'total_unique_patients': models.Count('patient', distinct=True),
            'avg_received_questionnaires_per_patient': models.F('total_received_questionnaires')
            / models.F('total_unique_patients'),
        },
        group_by=group_by,
    )


def fetch_users_latest_login_year_summary(
    start_date: dt.date,
    end_date: dt.date,
) -> dict[str, int]:
    """
    Fetch users' latest login statistics grouped by year.

    The goal of the query is to find in a given date range how many users stopped using the app in each year.

    Args:
        start_date: the beginning of the time period of the users' latest logins summary (inclusive)
        end_date: the end of the time period of the users' latest logins summary (inclusive)

    Returns:
        latest login statistics grouped by year for a given time period.
    """
    latest_logins = (
        DailyUserAppActivity.objects.filter(
            action_date__gte=start_date,
            action_date__lte=end_date,
        )
        .values(
            'action_by_user',
        )
        .annotate(
            year=ExtractYear(models.Max('last_login', tzinfo=dt.UTC)),
        )
    )

    latest_logins_by_year = Counter(str(item['year']) for item in latest_logins)
    return dict(latest_logins_by_year)


# INDIVIDUAL REPORTS
def fetch_labs_summary_per_patient(
    start_date: dt.date,
    end_date: dt.date,
) -> list[dict[str, Any]]:
    """
    Fetch the individual received lab results statistics from the `DailyPatientDataReceived` model.

    The statistics show the number of lab results received per patient and the frequency
    with which patients receive lab results for a given date range.

    Args:
        start_date: the starting date of the time period for lab statistics (inclusive).
        end_date: the ending date of the time period for lab statistics (inclusive).

    Returns:
        individual lab results statistics (per patient).
    """
    # TODO: update the query using `lab_groups_received` statistic field once QSCCD-2209 is implemented.
    # Update query should include `total_lab_groups_received` and `average_labs_per_test_group`.
    return list(
        DailyPatientDataReceived.objects.filter(
            action_date__gte=start_date,
            action_date__lte=end_date,
        )
        .values('patient__legacy_id')
        .annotate(
            patient_ser_num=models.F('patient__legacy_id'),
            first_lab_received_utc=models.Min('last_lab_received'),
            last_lab_received_utc=models.Max('last_lab_received'),
            # total_lab_groups_received=models.Sum('lab_groups_received'),   noqa: E800
            total_labs_received=models.Sum('labs_received'),
            # average_labs_per_test_group=models.F('total_labs_received')    noqa: E800
            # / models.F('total_lab_groups_received'),  noqa: E800
        )
        .order_by('patient_ser_num'),
    )


def fetch_logins_summary_per_user(
    start_date: dt.date,
    end_date: dt.date,
) -> list[dict[str, Any]]:
    """
    Fetch individual user login statistics from the `DailyUserAppActivity` model.

    The statistics show user's total login time and login frequency in a given date range.

    Args:
        start_date: the starting date of the time period for the user login stats (inclusive).
        end_date: the ending date of the time period for the user login stats (inclusive).

    Returns:
        individual login statistics (per user).
    """
    return list(
        DailyUserAppActivity.objects.filter(
            action_date__gte=start_date,
            action_date__lte=end_date,
        )
        .values('action_by_user_id')
        .annotate(
            user_id=models.F('action_by_user_id'),
            total_logged_in_days=models.Count('action_by_user_id'),
            total_logins=models.Sum('count_logins'),
            avg_logins_per_day=models.F('total_logins') / models.F('total_logged_in_days'),
        )
        .values(
            'user_id',
            'total_logged_in_days',
            'total_logins',
            'avg_logins_per_day',
        )
        .order_by('user_id'),
    )


def fetch_patient_demographic_diagnosis_summary(
    start_date: dt.date,
    end_date: dt.date,
) -> list[dict[str, Any]]:
    """
    Fetch demographic statistics and the latest diagnosis for each individual patient.

    The purpose of the query is to show patient basic information and the latest diagnosis only
    in a given date range.

    Args:
        start_date: the starting date of the time period for the demographic stats (inclusive).
        end_date: the ending date of the time period for the demographic stats (inclusive).

    Returns:
        demographic information and latest diagnosis per patient.
    """
    # TODO: QSCCD-2254 - update the query when Diagnosis model is implemented in django-backend
    latest_diagnosis_sernum_list = (
        legacy_models.LegacyDiagnosis.objects.values(
            'patient_ser_num',
        )
        .annotate(
            latest_diagnosis_date=models.Max('creation_date'),
            latest_diagnosis_sernum=models.Subquery(
                legacy_models.LegacyDiagnosis.objects.filter(
                    patient_ser_num=models.OuterRef('patient_ser_num'),
                )
                .order_by('-creation_date')
                .values('diagnosis_ser_num')[:1],
            ),
        )
        .values_list(
            'latest_diagnosis_sernum',
            flat=True,
        )
    )
    demographics_and_diagnosis = (
        legacy_models.LegacyPatientControl.objects.filter(
            models.Q(patient__legacydiagnosis__diagnosis_ser_num__in=latest_diagnosis_sernum_list)
            | models.Q(patient__legacydiagnosis__diagnosis_ser_num__isnull=True),
            patient__last_updated__date__gte=start_date,
            patient__last_updated__date__lte=end_date,
        )
        .annotate(
            patient_ser_num=models.F('patient__patientsernum'),
            age=models.F('patient__age'),
            date_of_birth=Trunc('patient__date_of_birth', 'second', tzinfo=dt.UTC),
            sex=models.F('patient__sex'),
            email=models.F('patient__email'),
            language=models.F('patient__language'),
            registration_date_utc=Trunc('patient__registration_date', 'second', tzinfo=dt.UTC),
            latest_diagnosis_description=models.F('patient__legacydiagnosis__description_en'),
            latest_diagnosis_date_utc=Trunc('patient__legacydiagnosis__creation_date', 'second', tzinfo=dt.UTC),
        )
        .values(
            'patient_ser_num',
            'age',
            'date_of_birth',
            'sex',
            'email',
            'language',
            'registration_date_utc',
            'latest_diagnosis_description',
            'latest_diagnosis_date_utc',
        )
    )

    return list(demographics_and_diagnosis)


def _fetch_received_medical_records_summary(
    start_date: dt.date,
    end_date: dt.date,
    filters: dict[str, models.Expression],
    annotated_summary_fields: dict[str, Any],
    group_by: GroupByComponent = GroupByComponent.DAY,
) -> list[dict[str, Any]]:
    """
    Fetch received medical records summary from the `DailyPatientDataReceived` model.

    The summary contains:
        - the total number of received medical records
        - the total number of unique patients
        - the average number of received medical records per patient

    The results can be grouped by day (by default), by month, by year.

    Args:
        start_date: the beginning of the time period of the received medical records summary (inclusive)
        end_date: the end of the time period of the received medical records summary (inclusive)
        filters: additional filters on the received medical records (e.g., to eliminate records where the count is 0)
        annotated_summary_fields: annotation fields with the statistics/summary aggregation
        group_by: the date component to group by. By default it is grouped by day.

    Returns:
        grouped received medical records summary for a given time period
    """
    queryset = DailyPatientDataReceived.objects.filter(
        action_date__gte=start_date,
        action_date__lte=end_date,
        **filters,
    )

    queryset = _annotate_queryset_with_grouping_field(queryset, 'action_date', group_by)
    group_field = group_by.name.lower()

    return list(
        queryset.values(
            group_field,
        )
        .annotate(
            **annotated_summary_fields,
        )
        .order_by(f'-{group_field}'),
    )


def _annotate_queryset_with_grouping_field[ModelType: models.Model](
    queryset: models.QuerySet[ModelType],
    field_name: str,
    group_by: GroupByComponent,
) -> models.QuerySet[ModelType]:
    """
    Add an aggregation field to the queryset based on the grouping component.

    Args:
        queryset: the queryset to annotate with a new grouping field
        field_name: the name of the queryset's field that is used to create new aggregation field
        group_by: the date component to group by

    Returns:
        queryset with annotated grouping component field
    """
    # First, cast the field to a DateTimeField (to avoid the ValueError if it's a DateField).
    datetime_expr = Cast(field_name, output_field=models.DateTimeField())

    if group_by == GroupByComponent.YEAR:
        annotated_queryset: models.QuerySet[ModelType] = queryset.annotate(
            year=TruncYear(datetime_expr, tzinfo=dt.UTC, output_field=models.DateField()),
        )
    elif group_by == GroupByComponent.MONTH:
        annotated_queryset = queryset.annotate(
            month=TruncMonth(datetime_expr, tzinfo=dt.UTC, output_field=models.DateField()),
        )
    else:
        annotated_queryset = queryset.annotate(
            day=TruncDay(datetime_expr, tzinfo=dt.UTC, output_field=models.DateField()),
        )

    return annotated_queryset
