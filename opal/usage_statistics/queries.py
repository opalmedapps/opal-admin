"""Statistics queries used by usage statistics app."""
import datetime as dt
from typing import Any

from django.conf import settings
from django.db import models

from opal.caregivers import models as caregivers_models
from opal.legacy import models as legacy_models
from opal.patients import models as patients_models
from opal.users import models as users_models

from .models import DailyPatientDataReceived

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


def fetch_patients_received_data_summary(
    start_date: dt.date,
    end_date: dt.date,
) -> dict[str, Any]:
    """Fetch grouped patients received data summary from the `DailyPatientDataReceived` model.

    Args:
        start_date: the beginning of the time period of the patients received data summary (inclusive)
        end_date: the end of the time period of the patients received data summary (inclusive)

    Returns:
        patients received data summary for a given time period
    """
    self_relationships = patients_models.Relationship.objects.select_related(
        'patient',
        'caregiver__user',
    ).filter(
        type__role_type=patients_models.RoleType.SELF,
    )
    patients_with_logins = [rel.patient.id for rel in self_relationships.exclude(caregiver__user__last_login=None)]
    patients_with_no_logins = [rel.patient.id for rel in self_relationships.filter(caregiver__user__last_login=None)]

    aggregated_patients_received_data = {
        'no_appointment_labs_notes': models.Count(
            'id',
            filter=models.Q(
                last_appointment_received=None,
                last_lab_received=None,
                last_document_received=None,
                patient_id__in=patients_with_logins,
            ),
        ),
        'has_appointment_only': models.Count(
            'id',
            filter=models.Q(
                last_appointment_received__isnull=False,
                last_lab_received=None,
                last_document_received=None,
                patient_id__in=patients_with_logins,
            ),
        ),
        'has_labs_only': models.Count(
            'id',
            filter=models.Q(
                last_appointment_received=None,
                last_lab_received__isnull=False,
                last_document_received=None,
                patient_id__in=patients_with_logins,
            ),
        ),
        'has_clinical_notes_only': models.Count(
            'id',
            filter=models.Q(
                last_appointment_received=None,
                last_lab_received=None,
                last_document_received__isnull=False,
                patient_id__in=patients_with_logins,
            ),
        ),
        'using_app_after_receiving_new_data': models.Count(
            'id',
            filter=models.Q(
                last_appointment_received__isnull=False,
                last_lab_received__isnull=False,
                last_document_received__isnull=False,
                patient_id__in=patients_with_logins,
            ),
        ),
        'not_using_app_after_receiving_new_data': models.Count(
            'id',
            filter=models.Q(
                last_appointment_received__isnull=False,
                last_lab_received__isnull=False,
                last_document_received__isnull=False,
                patient_id__in=patients_with_no_logins,
            ),
        ),
        'not_using_app_and_no_data': models.Count(
            'id',
            filter=models.Q(
                last_appointment_received=None,
                last_lab_received=None,
                last_document_received=None,
                patient_id__in=patients_with_no_logins,
            ),
        ),
    }

    return DailyPatientDataReceived.objects.filter(
        action_date__gte=start_date,
        action_date__lte=end_date,
    ).aggregate(
        **aggregated_patients_received_data,
    )
