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
from opal.usage_statistics.models import DailyUserAppActivity
from opal.users import models as users_models

# Create a type variable to represent any model type
_ModelT = TypeVar('_ModelT', bound=models.Model)


class GroupByComponent(Enum):
    """An enumeration of supported group by components."""

    DATE = 'date'  # noqa: WPS115
    MONTH = 'month'  # noqa: WPS115
    YEAR = 'year'  # noqa: WPS115


# GROUP REPORTING - POPULATION-LEVEL AGGREGATE STATISTICS


def fetch_registration_summary(
    start_date: dt.date,
    end_date: dt.date,
) -> dict[str, Any]:
    """Fetch grouped registration summary from `RegistrationCode` model.

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
        total=models.Count('id'),
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
            unique_user_logins=models.Count('id'),
            avg_logins_per_user=models.Avg('count_logins'),
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
        annotated_queryset: models.QuerySet[_ModelT] = queryset.annotate(
            year=TruncYear(field_name),  # type: ignore[arg-type]
        )
    elif group_by == GroupByComponent.MONTH:
        annotated_queryset = queryset.annotate(month=TruncMonth(field_name))  # type: ignore[arg-type]
    else:
        annotated_queryset = queryset.annotate(date=TruncDay(field_name))  # type: ignore[arg-type]

    return annotated_queryset
