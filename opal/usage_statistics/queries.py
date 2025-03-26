"""Statistics queries used by usage statistics app."""
import datetime as dt
from enum import Enum
from typing import Any, TypeVar

from django.conf import settings
from django.db import models
from django.db.models.functions import TruncDay, TruncMonth, TruncYear

from opal.caregivers import models as caregivers_models
from opal.legacy import models as legacy_models
from opal.patients import models as patients_models
from opal.users import models as users_models

from .models import DailyPatientDataReceived, DailyUserAppActivity, DailyUserPatientActivity

# Create a type variable to represent any model type
_ModelT = TypeVar('_ModelT', bound=models.Model)


class GroupByComponent(Enum):
    """An enumeration of supported group by components."""

    DATE = 'date'  # noqa: WPS115
    MONTH = 'month'  # noqa: WPS115
    YEAR = 'year'  # noqa: WPS115


# GROUP REPORTING

def fetch_registration_summary(
    start_date: dt.date,
    end_date: dt.date,
) -> dict[str, Any]:
    """Fetch registration summary from `RegistrationCode` model.

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
            'id', filter=~models.Q(status=caregivers_models.RegistrationCodeStatus.REGISTERED),
        ),
        completed_registration=models.Count(
            'id', filter=models.Q(status=caregivers_models.RegistrationCodeStatus.REGISTERED),
        ),
        total_registration_codes=models.F('uncompleted_registration') + models.F('completed_registration'),
    )


def fetch_grouped_registration_summary(
    start_date: dt.date,
    end_date: dt.date,
    group_by: GroupByComponent = GroupByComponent.DATE,
) -> list[dict[str, Any]]:
    """Fetch grouped registration summary from `RegistrationCode` model.

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
    group_field = group_by.value

    return list(
        queryset.values(
            group_field,
        ).annotate(
            uncompleted_registration=models.Count(
                'id', filter=~models.Q(status=caregivers_models.RegistrationCodeStatus.REGISTERED),
            ),
            completed_registration=models.Count(
                'id', filter=models.Q(status=caregivers_models.RegistrationCodeStatus.REGISTERED),
            ),
            total_registration_codes=models.F('uncompleted_registration') + models.F('completed_registration'),
        ).order_by(f'-{group_field}'),
    )


def fetch_caregivers_summary(
    start_date: dt.date,
    end_date: dt.date,
) -> dict[str, Any]:
    """Fetch grouped caregivers summary from `Caregiver` model.

    Args:
        start_date: the beginning of the time period of the caregivers summary (inclusive)
        end_date: the end of the time period of the caregivers summary (inclusive)

    Returns:
        caregivers summary for a given time period
    """
    lang_codes = [lang[0] for lang in settings.LANGUAGES]
    lang_dict = {
        lang: models.Count('id', filter=models.Q(language=lang)) for lang in lang_codes
    }

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
    """Fetch grouped patients summary from `Patient` model.

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
    """Fetch grouped device identifiers summary from `LegacyPatientDeviceIdentifier` model.

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
    """Fetch grouped patients received data summary from the `DailyPatientDataReceived` model.

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
    group_by: GroupByComponent = GroupByComponent.DATE,
) -> list[dict[str, Any]]:
    """Fetch grouped logins summary from `DailyUserAppActivity` model.

    Args:
        start_date: the beginning of the time period of the logins summary (inclusive)
        end_date: the end of the time period of the logins summary (inclusive)
        group_by: the date component to group by. By default is grouped by date.

    Returns:
        grouped logins summary for a given time period
    """
    queryset = DailyUserAppActivity.objects.filter(
        action_date__gte=start_date,
        action_date__lte=end_date,
    )

    queryset = _annotate_queryset_with_grouping_field(queryset, 'action_date', group_by)
    group_field = group_by.value

    return list(
        queryset.values(
            group_field,
        ).annotate(
            total_logins=models.Sum('count_logins'),
            unique_user_logins=models.Count('action_by_user', distinct=True),
            avg_logins_per_user=models.F('total_logins') / models.F('unique_user_logins'),
        ).order_by(f'-{group_field}'),
    )


def fetch_users_clicks_summary(
    start_date: dt.date,
    end_date: dt.date,
    group_by: GroupByComponent = GroupByComponent.DATE,
) -> list[dict[str, Any]]:
    """Fetch grouped users' clicks from `DailyUserAppActivity` model.

    Args:
        start_date: the beginning of the time period of the users' clicks summary (inclusive)
        end_date: the end of the time period of the users' clicks summary (inclusive)
        group_by: the date component to group by. By default is grouped by date.

    Returns:
        grouped users' clicks summary for a given time period
    """
    queryset = DailyUserAppActivity.objects.filter(
        action_date__gte=start_date,
        action_date__lte=end_date,
    )

    queryset = _annotate_queryset_with_grouping_field(queryset, 'action_date', group_by)
    group_field = group_by.value

    # TODO: QSCCD-2173 - add count of the announcement clicks
    return list(
        queryset.values(
            group_field,
        ).annotate(
            login_count=models.Sum('count_logins'),
            feedback_count=models.Sum('count_feedback'),
            update_security_answers_count=models.Sum('count_update_security_answers'),
            update_passwords_count=models.Sum('count_update_passwords'),
        ).order_by(f'-{group_field}'),
    )


def fetch_user_patient_clicks_summary(
    start_date: dt.date,
    end_date: dt.date,
    group_by: GroupByComponent = GroupByComponent.DATE,
) -> list[dict[str, Any]]:
    """Fetch grouped user's clicks on behalf of a patient from `DailyUserPatientActivity` model.

    Args:
        start_date: the beginning of the time period of the patients' clicks summary (inclusive)
        end_date: the end of the time period of the patients' clicks summary (inclusive)
        group_by: the date component to group by. By default is grouped by date.

    Returns:
        grouped patients' clicks summary for a given time period
    """
    queryset = DailyUserPatientActivity.objects.filter(
        action_date__gte=start_date,
        action_date__lte=end_date,
    )

    # generate the user patient activity report
    queryset = _annotate_queryset_with_grouping_field(queryset, 'action_date', group_by)
    group_field = group_by.value

    return list(
        queryset.values(
            group_field,
        ).annotate(
            checkins_count=models.Sum('count_checkins'),
            documents_count=models.Sum('count_documents'),
            educational_materials_count=models.Sum('count_educational_materials'),
            completed_questionnaires_count=models.Sum('count_questionnaires_complete'),
            labs_count=models.Sum('count_labs'),
        ).order_by(f'-{group_field}'),
    )


def fetch_received_labs_summary(
    start_date: dt.date,
    end_date: dt.date,
    group_by: GroupByComponent = GroupByComponent.DATE,
) -> list[dict[str, Any]]:
    """Fetch received lab results statistics from the `DailyPatientDataReceived` model.

    The results can be grouped by date (by default), by month, by year.

    Args:
        start_date: the beginning of the time period of the received lab results summary (inclusive)
        end_date: the end of the time period of the received lab results summary (inclusive)
        group_by: the date component to group by. By default is grouped by date.

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
    group_by: GroupByComponent = GroupByComponent.DATE,
) -> list[dict[str, Any]]:
    """Fetch received appointments summary from the `DailyPatientDataReceived` model.

    The results can be grouped by date (by default), by month, by year.

    Args:
        start_date: the beginning of the time period of the received appointments summary (inclusive)
        end_date: the end of the time period of the received appointments summary (inclusive)
        group_by: the date component to group by. By default is grouped by date.

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
            'avg_received_appointments_per_patient':
                models.F('total_received_appointments') / models.F('total_unique_patients'),
        },
        group_by=group_by,
    )


# TODO: QSCCD-2173 - implement fetch_received_diagnoses_summary() function once diagnoses_received field is added.


def fetch_received_educational_materials_summary(
    start_date: dt.date,
    end_date: dt.date,
    group_by: GroupByComponent = GroupByComponent.DATE,
) -> list[dict[str, Any]]:
    """Fetch received educational materials summary from the `DailyPatientDataReceived` model.

    The results can be grouped by date (by default), by month, by year.

    Args:
        start_date: the beginning of the time period of the received educational materials summary (inclusive)
        end_date: the end of the time period of the received educational materials summary (inclusive)
        group_by: the date component to group by. By default is grouped by date.

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
            'avg_received_edu_materials_per_patient':
                models.F('total_received_edu_materials') / models.F('total_unique_patients'),
        },
        group_by=group_by,
    )


def fetch_received_documents_summary(
    start_date: dt.date,
    end_date: dt.date,
    group_by: GroupByComponent = GroupByComponent.DATE,
) -> list[dict[str, Any]]:
    """Fetch received documents summary from the `DailyPatientDataReceived` model.

    The results can be grouped by date (by default), by month, by year.

    Args:
        start_date: the beginning of the time period of the received documents summary (inclusive)
        end_date: the end of the time period of the received documents summary (inclusive)
        group_by: the date component to group by. By default is grouped by date.

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
            'avg_received_documents_per_patient':
                models.F('total_received_documents') / models.F('total_unique_patients'),
        },
        group_by=group_by,
    )


def fetch_received_questionnaires_summary(
    start_date: dt.date,
    end_date: dt.date,
    group_by: GroupByComponent = GroupByComponent.DATE,
) -> list[dict[str, Any]]:
    """Fetch received questionnaires summary from the `DailyPatientDataReceived` model.

    The results can be grouped by date (by default), by month, by year.

    Args:
        start_date: the beginning of the time period of the received questionnaires summary (inclusive)
        end_date: the end of the time period of the received questionnaires summary (inclusive)
        group_by: the date component to group by. By default is grouped by date.

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
            'avg_received_questionnaires_per_patient':
                models.F('total_received_questionnaires') / models.F('total_unique_patients'),
        },
        group_by=group_by,
    )


# INDIVIDUAL REPORTS
def fetch_user_last_login_year_report(report_date: dt.date, start_year: int = 2016) -> dict[str, int]:
    """Fetch the daily report of basic information for user last login year before the given date.

    Args:
        report_date: the date required of the daily basic statistics report for user last login.
        start_year: the start year of the report, 2016 by default.

    Returns:
        the daily basic statistics report for user last login.
    """
    last_login_records = DailyUserAppActivity.objects.filter(
        action_date__lte=report_date,
    ).values('action_by_user_id').annotate(
        last_login_year=TruncYear(models.Max('last_login')),
    )
    login_report = {
        f'last_login_with_the_year_{year}': last_login_records.aggregate(
            login_stats=models.Sum(
                models.Case(
                    models.When(last_login_year__year=year - 1, then=1),
                    default=0,
                ),
            ),
        )['login_stats'] for year in range(start_year, dt.datetime.now().year + 1)
    }

    login_report['last_login_with_none_date'] = last_login_records.aggregate(
        login_stats=models.Sum(
            models.Case(
                models.When(last_login_year__isnull=True, then=1),
                default=0,
            ),
        ),
    )['login_stats']
    return login_report


def fetch_basic_functionality_stats_report(report_date: dt.date) -> dict[str, int]:
    """Fetch the basic statistics report of number of user who use app functionnality.

    Args:
        report_date: the date required of the daily basic statistics report for functionality using.

    Returns:
        the daily basic statistics report for functionality using by user.
    """
    return DailyPatientDataReceived.objects.filter(action_date=report_date).aggregate(
        received_nothing=models.Sum(
            models.Case(
                models.When(
                    last_appointment_received__isnull=True,
                    last_document_received__isnull=True,
                    last_lab_received__isnull=True,
                    last_educational_material_received__isnull=True,
                    last_questionnaire_received__isnull=True,
                    then=1,
                ),
                default=0,
            ),
        ),
        received_new_data=models.Sum(
            models.Case(
                models.When(
                    models.Q(last_appointment_received__isnull=False)
                    | models.Q(last_document_received__isnull=False)
                    | models.Q(last_lab_received__isnull=False)
                    | models.Q(last_educational_material_received__isnull=False)
                    | models.Q(last_questionnaire_received__isnull=False),
                    then=1,
                ),
                default=0,
            ),
        ),
        received_only_appointment=models.Sum(
            models.Case(
                models.When(
                    last_appointment_received__isnull=False,
                    last_document_received__isnull=True,
                    last_lab_received__isnull=True,
                    last_educational_material_received__isnull=True,
                    last_questionnaire_received__isnull=True,
                    then=1,
                ),
                default=0,
            ),
        ),
        received_only_document=models.Sum(
            models.Case(
                models.When(
                    last_appointment_received__isnull=True,
                    last_document_received__isnull=False,
                    last_lab_received__isnull=True,
                    last_educational_material_received__isnull=True,
                    last_questionnaire_received__isnull=True,
                    then=1,
                ),
                default=0,
            ),
        ),
        received_only_lab=models.Sum(
            models.Case(
                models.When(
                    last_appointment_received__isnull=True,
                    last_document_received__isnull=False,
                    last_lab_received__isnull=True,
                    last_educational_material_received__isnull=True,
                    last_questionnaire_received__isnull=True,
                    then=1,
                ),
                default=0,
            ),
        ),
        received_only_educational_material=models.Sum(
            models.Case(
                models.When(
                    last_appointment_received__isnull=True,
                    last_document_received__isnull=True,
                    last_lab_received__isnull=True,
                    last_educational_material_received__isnull=False,
                    last_questionnaire_received__isnull=True,
                    then=1,
                ),
                default=0,
            ),
        ),
        received_only_questionnaire=models.Sum(
            models.Case(
                models.When(
                    last_appointment_received__isnull=True,
                    last_document_received__isnull=True,
                    last_lab_received__isnull=True,
                    last_educational_material_received__isnull=True,
                    last_questionnaire_received__isnull=False,
                    then=1,
                ),
                default=0,
            ),
        ),
    )


def fetch_patient_labs_statistics_report() -> list[dict[str, Any]]:
    """Fetch the statistics report of patients when the first and last time they received their test.

    Note that when patient first signs up, the system will import as many of their tests.
    So the number of records might be large for the first time.

    Returns:
        the basic individual statistics report for labs.
    """
    lab_report = DailyPatientDataReceived.objects.values('patient__legacy_id').annotate(
        patient_sernum=models.F('patient__legacy_id'),
        first_received=models.Min('last_lab_received'),
        last_received=models.Max('last_lab_received'),
        number_test=models.Count('last_lab_received'),
        number_lab_received=models.Sum('labs_received'),
        average_labs_per_test=models.F('number_lab_received') / models.F('number_test'),
    ).values(
        'patient_sernum',
        'first_received',
        'last_received',
        'number_test',
        'number_lab_received',
        'average_labs_per_test',
    ).order_by('patient_sernum')
    return list(lab_report.all())


def fetch_individual_average_login_report() -> list[dict[str, Any]]:
    """Fetch the statistics report of individual patients for the average times they log into app.

    Returns:
        the basic individual statistics report for average login group by user.
    """
    login_report = DailyUserAppActivity.objects.values('action_by_user_id').annotate(
        user_id=models.F('action_by_user_id'),
        number_of_days=models.Count('action_by_user_id'),
        number_of_logins=models.Sum('count_logins'),
        average_login_per_day=models.F('number_of_logins') / models.F('number_of_days'),
    ).values(
        'user_id',
        'number_of_days',
        'number_of_logins',
        'average_login_per_day',
    ).order_by('user_id')
    return list(login_report.all())


def fetch_average_login_per_year_by_month_report() -> list[dict[str, Any]]:
    """Fetch the statistics report of individual years and months for the average times user log into app.

    Returns:
        the basic annually statistics report for average login group by month.
    """
    month_number = {
        'january': 12,
        'february': 1,
        'march': 2,
        'april': 3,
        'may': 4,
        'june': 5,
        'july': 6,
        'august': 7,
        'september': 8,
        'october': 9,
        'november': 10,
        'december': 11,
    }
    login_per_year_by_month_report = DailyUserAppActivity.objects.annotate(
        trunc_year=TruncYear('last_login'),
        trunc_month=TruncMonth('last_login'),
    ).values('trunc_year').annotate(
        year=models.F('trunc_year__year') + 1,
        january=models.Sum('count_logins', filter=models.Q(trunc_month__month=month_number['january'])),
        february=models.Sum('count_logins', filter=models.Q(trunc_month__month=month_number['february'])),
        march=models.Sum('count_logins', filter=models.Q(trunc_month__month=month_number['march'])),
        april=models.Sum('count_logins', filter=models.Q(trunc_month__month=month_number['april'])),
        may=models.Sum('count_logins', filter=models.Q(trunc_month__month=month_number['may'])),
        june=models.Sum('count_logins', filter=models.Q(trunc_month__month=month_number['june'])),
        july=models.Sum('count_logins', filter=models.Q(trunc_month__month=month_number['july'])),
        august=models.Sum('count_logins', filter=models.Q(trunc_month__month=month_number['august'])),
        september=models.Sum('count_logins', filter=models.Q(trunc_month__month=month_number['september'])),
        october=models.Sum('count_logins', filter=models.Q(trunc_month__month=month_number['october'])),
        november=models.Sum('count_logins', filter=models.Q(trunc_month__month=month_number['november'])),
        december=models.Sum('count_logins', filter=models.Q(trunc_month__month=month_number['december'])),
    ).values(
        'year',
        'january',
        'february',
        'march',
        'april',
        'may',
        'june',
        'july',
        'august',
        'september',
        'october',
        'november',
        'december',
    ).order_by('-year')
    return list(login_per_year_by_month_report.all())


# JOHN'S REPORT
def fetch_patient_demographic_diagnosis_report() -> list[dict[str, Any]]:
    """Fetch the patient demographic report with diagnosis.

    Returns:
        the patient demographic report with diagnosis.
    """
    test_patient_list = ['9999991', '9999992', '9999993', '9999994', '9999995', '9999996', '9999997', '9999998']
    test_patient_id = [
        patient['patient'] for patient in legacy_models.LegacyPatientHospitalIdentifier.objects.filter(
            mrn__in=test_patient_list,
        ).values('patient').all()
    ]
    diagnoses = legacy_models.LegacyDiagnosis.objects.exclude(
        patient_ser_num__in=test_patient_id,
    ).values('patient_ser_num').annotate(
        diagnosis_id=models.Max('diagnosis_ser_num'),
    ).all()

    diagnosis_id_list = [
        diagnosis['diagnosis_id'] for diagnosis in diagnoses
    ]

    demographics_diagnosis_report = legacy_models.LegacyPatient.objects.exclude(
        patientsernum__in=test_patient_id,
    ).filter(
        models.Q(legacydiagnosis__diagnosis_ser_num__in=diagnosis_id_list)
        | models.Q(legacydiagnosis__diagnosis_ser_num=None),
    ).annotate(
        description_en=models.F('legacydiagnosis__description_en'),
        creation_date=models.F('legacydiagnosis__creation_date'),
    ).values(
        'patientsernum',
        'age',
        'date_of_birth',
        'sex',
        'email',
        'language',
        'registration_date',
        'description_en',
        'creation_date',
    )
    return list(demographics_diagnosis_report.all())


def _fetch_received_medical_records_summary(
    start_date: dt.date,
    end_date: dt.date,
    filters: dict[str, models.Expression],
    annotated_summary_fields: dict[str, Any],
    group_by: GroupByComponent = GroupByComponent.DATE,
) -> list[dict[str, Any]]:
    """Fetch received medical records summary from the `DailyPatientDataReceived` model.

    The summary contains:
        - the total number of received medical records
        - the total number of unique patients
        - the average number of received medical records per patient

    The results can be grouped by date (by default), by month, by year.

    Args:
        start_date: the beginning of the time period of the received medical records summary (inclusive)
        end_date: the end of the time period of the received medical records summary (inclusive)
        filters: additional filters on the received medical records (e.g., to eliminate records where the count is 0)
        annotated_summary_fields: annotation fields with the statistics/summary aggregation
        group_by: the date component to group by. By default is grouped by date.

    Returns:
        grouped received medical records summary for a given time period
    """
    queryset = DailyPatientDataReceived.objects.filter(
        action_date__gte=start_date,
        action_date__lte=end_date,
        **filters,
    )

    queryset = _annotate_queryset_with_grouping_field(queryset, 'action_date', group_by)
    group_field = group_by.value

    return list(
        queryset.values(
            group_field,
        ).annotate(
            **annotated_summary_fields,
        ).order_by(f'-{group_field}'),
    )


def _annotate_queryset_with_grouping_field(
    queryset: models.QuerySet[_ModelT],
    field_name: str,
    group_by: GroupByComponent,
) -> models.QuerySet[_ModelT]:
    """Add an aggregation field to the queryset based on the grouping component.

    Args:
        queryset: the queryset to annotate with a new grouping field
        field_name: the name of the queryset's field that is used to create new aggregation field
        group_by: the date component to group by

    Returns:
        queryset with annotated grouping component field
    """
    if group_by == GroupByComponent.YEAR:
        annotated_queryset: models.QuerySet[_ModelT] = queryset.annotate(year=TruncYear(field_name))
    elif group_by == GroupByComponent.MONTH:
        annotated_queryset = queryset.annotate(month=TruncMonth(field_name))
    else:
        annotated_queryset = queryset.annotate(date=TruncDay(field_name))

    return annotated_queryset
