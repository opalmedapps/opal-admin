import datetime as dt
import json

from django.db import DatabaseError
from django.utils import timezone

import pytest
from pytest_django.asserts import assertRaisesMessage

from opal.legacy import factories as legacy_factories
from opal.legacy.factories import LegacyAliasExpressionFactory, LegacyPatientFactory, LegacySourceDatabaseFactory

from .. import factories
from .. import models as legacy_models

pytestmark = pytest.mark.django_db(databases=['default', 'legacy'])


def test_get_appointment_databank_data() -> None:
    """Ensure appointment data for databank is returned and formatted correctly."""
    # Prepare patient and last cron run time
    consenting_patient = factories.LegacyPatientFactory()
    last_cron_sync_time = timezone.make_aware(dt.datetime(2023, 1, 1, 0, 0, 5))
    # Prepare appointment data
    factories.LegacyAppointmentFactory(appointmentsernum=1, checkin=0, patientsernum=consenting_patient)
    factories.LegacyAppointmentFactory(appointmentsernum=2, checkin=0, patientsernum=consenting_patient)
    factories.LegacyAppointmentFactory(appointmentsernum=3, patientsernum=consenting_patient)
    factories.LegacyAppointmentFactory(appointmentsernum=4, patientsernum=consenting_patient)
    # Fetch the data
    databank_data = legacy_models.LegacyAppointment.objects.get_databank_data_for_patient(
        patient_ser_num=consenting_patient.patientsernum,
        last_synchronized=last_cron_sync_time,
    )

    # Define expected result to ensure query doesn't get accidentally altered
    expected_returned_fields = {
        'appointment_id',
        'date_created',
        'source_db_name',
        'source_db_alias_code',
        'source_db_alias_description',
        'source_db_appointment_id',
        'alias_name',
        'scheduled_start_time',
        'scheduled_end_time',
        'last_updated',
    }

    for appointment in databank_data:
        assert appointment['last_updated'] > last_cron_sync_time
        assert not (set(expected_returned_fields) - set(appointment.keys()))

    assert databank_data.count() == 2


def test_get_demographics_databank_data() -> None:
    """Ensure demographics data for databank is returned and formatted correctly."""
    # Prepare patient and last cron run time
    consenting_patient = factories.LegacyPatientFactory()
    last_cron_sync_time = timezone.make_aware(dt.datetime(2023, 1, 1, 0, 0, 5))
    # Fetch the data
    databank_data = legacy_models.LegacyPatient.objects.get_databank_data_for_patient(
        patient_ser_num=consenting_patient.patientsernum,
        last_synchronized=last_cron_sync_time,
    )

    # Define expected result to ensure query doesn't get accidentally altered
    expected_returned_fields = {
        'patient_id',
        'opal_registration_date',
        'patient_sex',
        'patient_dob',
        'patient_primary_language',
        'patient_death_date',
        'last_updated',
    }
    assert databank_data[0]['last_updated'] > last_cron_sync_time
    assert databank_data[0]['patient_id'] == consenting_patient.patientsernum
    assert databank_data.count() == 1
    assert not (set(expected_returned_fields) - set(databank_data[0].keys()))


def test_get_diagnosis_databank_data() -> None:
    """Ensure diagnosis data for databank is returned and formatted correctly."""
    # Prepare patient and last cron run time
    consenting_patient = factories.LegacyPatientFactory()
    non_consenting_patient = factories.LegacyPatientFactory(patientsernum=52)
    last_cron_sync_time = timezone.make_aware(dt.datetime(2023, 1, 1, 0, 0, 5))
    # Prepare diagnosis data
    factories.LegacyDiagnosisFactory(patient_ser_num=consenting_patient)
    factories.LegacyDiagnosisFactory(patient_ser_num=consenting_patient)
    factories.LegacyDiagnosisFactory(patient_ser_num=non_consenting_patient)
    # Fetch the data
    databank_data = legacy_models.LegacyDiagnosis.objects.get_databank_data_for_patient(
        patient_ser_num=consenting_patient.patientsernum,
        last_synchronized=last_cron_sync_time,
    )

    # Define expected result to ensure query doesn't get accidentally altered
    expected_returned_fields = {
        'diagnosis_id',
        'date_created',
        'source_system_code',
        'source_system_code_description',
        'last_updated',
    }
    for diagnosis in databank_data:
        assert diagnosis['last_updated'] > last_cron_sync_time
        assert not (set(expected_returned_fields) - set(diagnosis.keys()))

    assert databank_data.count() == 2


def test_get_labs_databank_data() -> None:
    """Ensure labs data for databank is returned and formatted correctly."""
    # Prepare patient and last cron run time
    consenting_patient = factories.LegacyPatientFactory()
    non_consenting_patient = factories.LegacyPatientFactory(patientsernum=52)
    last_cron_sync_time = timezone.make_aware(dt.datetime(2023, 1, 1, 0, 0, 5))
    # Prepare labs data
    factories.LegacyPatientTestResultFactory(patient_ser_num=consenting_patient)
    factories.LegacyPatientTestResultFactory(patient_ser_num=consenting_patient)
    factories.LegacyPatientTestResultFactory(patient_ser_num=consenting_patient)
    factories.LegacyPatientTestResultFactory(patient_ser_num=non_consenting_patient)
    # Fetch the data
    databank_data = legacy_models.LegacyPatientTestResult.objects.get_databank_data_for_patient(
        patient_ser_num=consenting_patient.patientsernum,
        last_synchronized=last_cron_sync_time,
    )

    # Define expected result to ensure query doesn't get accidentally altered
    expected_returned_fields = {
        'test_result_id',
        'specimen_collected_date',
        'component_result_date',
        'test_group_name',
        'test_group_indicator',
        'test_component_sequence',
        'test_component_name',
        'test_value',
        'test_units',
        'max_norm_range',
        'min_norm_range',
        'abnormal_flag',
        'source_system',
        'last_updated',
    }
    for lab in databank_data:
        assert lab['last_updated'] > last_cron_sync_time
        assert not (set(expected_returned_fields) - set(lab.keys()))

    assert databank_data.count() == 3


def test_create_pathology_document_success() -> None:
    """Ensure a new pathology PDF document record inserted successfully to the OpalDB.Document table."""
    legacy_patient = LegacyPatientFactory()

    LegacySourceDatabaseFactory(source_database_name='OACIS')

    LegacyAliasExpressionFactory(
        expression_name='Pathology',
        description='Pathology',
    )

    legacy_models.LegacyDocument.objects.create_pathology_document(
        legacy_patient_id=legacy_patient.patientsernum,
        prepared_by=1,  # TODO: add LegacyStaff model;
        received_at=timezone.now(),
        report_file_name='test-pathology-pdf-name',
    )

    assert legacy_models.LegacyDocument.objects.count() == 1


def test_create_pathology_document_raises_exception() -> None:
    """Ensure that create_pathology_document method raises exception in case of unsuccessful insertion."""
    legacy_patient = LegacyPatientFactory()

    with assertRaisesMessage(
        DatabaseError,
        'Failed to insert a new pathology PDF document record to the OpalDB.Document table:',
    ):
        legacy_models.LegacyDocument.objects.create_pathology_document(
            legacy_patient_id=legacy_patient.patientsernum,
            prepared_by=1,  # TODO: add LegacyStaff model;
            received_at=timezone.now(),
            report_file_name='test-pathology-pdf-name',
        )

    assert legacy_models.LegacyDocument.objects.count() == 0


def test_get_unread_lab_results_queryset() -> None:
    """Ensure LegacyPatientTestResultManager returns lab results counts where available_at is less or equal than now."""
    patient = factories.LegacyPatientFactory()
    factories.LegacyPatientTestResultFactory(patient_ser_num=patient)
    factories.LegacyPatientTestResultFactory(patient_ser_num=patient)
    factories.LegacyPatientTestResultFactory(patient_ser_num=patient, read_by='[QXmz5ANVN3Qp9ktMlqm2tJ2YYBz2]')
    available_at = timezone.now() + dt.timedelta(seconds=1)
    factories.LegacyPatientTestResultFactory(
        patient_ser_num=patient,
        available_at=available_at,
    )
    factories.LegacyPatientTestResultFactory(
        patient_ser_num=patient,
        test_expression_ser_num__test_control_ser_num__publish_flag=0,
    )

    assert legacy_models.LegacyPatientTestResult.objects.count() == 5
    assert legacy_models.LegacyPatientTestResult.objects.get_unread_queryset(
        patient_sernum=patient.patientsernum,
        username='QXmz5ANVN3Qp9ktMlqm2tJ2YYBz2',
    ).count() == 2


# tests for populating user app activities

def test_get_aggregated_user_app_no_activities() -> None:
    """Ensure that get_aggregated_user_app_activities function does not fail when there is no app statistics."""
    start_datetime_period = dt.datetime.combine(
        dt.datetime.now() - dt.timedelta(days=1),
        dt.datetime.min.time(),
        timezone.get_current_timezone(),
    )
    end_datetime_period = dt.datetime.combine(
        start_datetime_period,
        dt.datetime.max.time(),
        timezone.get_current_timezone(),
    )
    assert legacy_models.LegacyPatientActivityLog.objects.get_aggregated_user_app_activities(
        start_datetime_period,
        end_datetime_period,
    ).count() == 0


def test_get_aggregated_user_app_activities_previous_day() -> None:
    """Ensure that get_aggregated_user_app_activities function returns users' previous day activities."""
    _create_log_record()
    _create_log_record(request='Feedback', parameters='OMITTED')
    _create_log_record(request='UpdateSecurityQuestionAnswer', parameters='OMITTED')
    _create_log_record(username='second_user')
    _create_log_record(request='Feedback', parameters='OMITTED', username='second_user')
    _create_log_record(request='AccountChange', parameters='OMITTED', username='second_user')
    # current day records should not be included to the final queryset
    _create_log_record(username='third_user', days_delta=0)
    _create_log_record(request='Feedback', parameters='OMITTED', username='third_user', days_delta=0)

    start_datetime_period = dt.datetime.combine(
        dt.datetime.now() - dt.timedelta(days=1),
        dt.datetime.min.time(),
        timezone.get_current_timezone(),
    )
    end_datetime_period = dt.datetime.combine(
        start_datetime_period,
        dt.datetime.max.time(),
        timezone.get_current_timezone(),
    )
    app_activities = legacy_models.LegacyPatientActivityLog.objects.get_aggregated_user_app_activities(
        start_datetime_period,
        end_datetime_period,
    )
    assert app_activities.count() == 2
    assert app_activities.filter(username='username')[0]['count_logins'] == 1
    assert app_activities.filter(username='username')[0]['count_feedback'] == 1
    assert app_activities.filter(username='username')[0]['count_update_security_answers'] == 1
    assert app_activities.filter(username='second_user')[0]['count_logins'] == 1
    assert app_activities.filter(username='second_user')[0]['count_feedback'] == 1
    assert app_activities.filter(username='second_user')[0]['count_update_security_answers'] == 0


def test_get_aggregated_user_app_activities_current_day() -> None:
    """Ensure that get_aggregated_user_app_activities function returns users' current day activities."""
    _create_log_record(days_delta=0)
    _create_log_record(request='Feedback', parameters='OMITTED', days_delta=0)
    _create_log_record(request='UpdateSecurityQuestionAnswer', parameters='OMITTED', days_delta=0)
    _create_log_record(username='second_user', days_delta=0)
    _create_log_record(request='Feedback', parameters='OMITTED', username='second_user', days_delta=0)
    _create_log_record(request='AccountChange', parameters='OMITTED', username='second_user', days_delta=0)
    # previous day records should not be included to the final queryset
    _create_log_record(username='third_user')
    _create_log_record(request='Feedback', parameters='OMITTED', username='third_user')

    start_datetime_period = dt.datetime.combine(
        dt.datetime.now(),
        dt.datetime.min.time(),
        timezone.get_current_timezone(),
    )
    end_datetime_period = dt.datetime.combine(
        start_datetime_period,
        dt.datetime.max.time(),
        timezone.get_current_timezone(),
    )
    app_activities = legacy_models.LegacyPatientActivityLog.objects.get_aggregated_user_app_activities(
        start_datetime_period,
        end_datetime_period,
    )
    assert app_activities.count() == 2
    assert app_activities.filter(username='username')[0]['count_logins'] == 1
    assert app_activities.filter(username='username')[0]['count_feedback'] == 1
    assert app_activities.filter(username='username')[0]['count_update_security_answers'] == 1
    assert app_activities.filter(username='second_user')[0]['count_logins'] == 1
    assert app_activities.filter(username='second_user')[0]['count_feedback'] == 1
    assert app_activities.filter(username='second_user')[0]['count_update_security_answers'] == 0


def test_get_aggregated_user_app_activities_last_login_statistics() -> None:
    """Ensure that get_aggregated_user_app_activities returns correctly last login per patient per day."""
    start_datetime_period = dt.datetime.combine(
        dt.datetime.now() - dt.timedelta(days=1),
        dt.datetime.min.time(),
        timezone.get_current_timezone(),
    )
    end_datetime_period = dt.datetime.combine(
        start_datetime_period,
        dt.datetime.max.time(),
        timezone.get_current_timezone(),
    )
    legacy_factories.LegacyPatientActivityLogFactory(
        username='marge',
        date_time=start_datetime_period + dt.timedelta(hours=1),
    )
    legacy_factories.LegacyPatientActivityLogFactory(
        username='marge',
        date_time=start_datetime_period + dt.timedelta(hours=2),
    )
    legacy_factories.LegacyPatientActivityLogFactory(
        username='marge',
        date_time=start_datetime_period + dt.timedelta(hours=3),
    )
    legacy_factories.LegacyPatientActivityLogFactory(
        username='marge',
        date_time=start_datetime_period + dt.timedelta(days=1, hours=4),
    )
    legacy_factories.LegacyPatientActivityLogFactory(
        username='homer',
        date_time=start_datetime_period + dt.timedelta(hours=1),
    )
    legacy_factories.LegacyPatientActivityLogFactory(
        username='homer',
        date_time=start_datetime_period + dt.timedelta(hours=2),
    )
    legacy_factories.LegacyPatientActivityLogFactory(
        username='homer',
        date_time=start_datetime_period + dt.timedelta(hours=3),
    )
    legacy_factories.LegacyPatientActivityLogFactory(
        username='homer',
        date_time=start_datetime_period + dt.timedelta(days=1, hours=4),
    )
    app_activities = legacy_models.LegacyPatientActivityLog.objects.get_aggregated_user_app_activities(
        start_datetime_period,
        end_datetime_period,
    )

    marge_last_login = start_datetime_period + dt.timedelta(hours=3)
    homer_last_login = start_datetime_period + dt.timedelta(hours=3)
    assert app_activities.count() == 2
    assert app_activities.filter(username='marge')[0]['last_login'] == marge_last_login
    assert app_activities.filter(username='homer')[0]['last_login'] == homer_last_login


def test_get_aggregated_user_app_activities_login_statistics() -> None:
    """Ensure that get_aggregated_user_app_activities correctly aggregates login counts per patient per day."""
    _create_log_record(username='marge')
    _create_log_record(username='marge')
    _create_log_record(username='marge')
    _create_log_record(username='marge', days_delta=0)
    _create_log_record(username='homer')
    _create_log_record(username='homer')
    _create_log_record(username='homer')
    _create_log_record(username='homer', days_delta=0)

    start_datetime_period = dt.datetime.combine(
        dt.datetime.now() - dt.timedelta(days=1),
        dt.datetime.min.time(),
        timezone.get_current_timezone(),
    )
    end_datetime_period = dt.datetime.combine(
        start_datetime_period,
        dt.datetime.max.time(),
        timezone.get_current_timezone(),
    )
    app_activities = legacy_models.LegacyPatientActivityLog.objects.get_aggregated_user_app_activities(
        start_datetime_period,
        end_datetime_period,
    )

    assert app_activities.count() == 2
    assert app_activities.filter(username='marge')[0]['count_logins'] == 3
    assert app_activities.filter(username='homer')[0]['count_logins'] == 3


def test_get_aggregated_user_app_activities_feedback_statistics() -> None:
    """Ensure that get_aggregated_user_app_activities correctly aggregates feedback counts per patient per day."""
    _create_log_record(request='Feedback', parameters='OMITTED', username='marge')
    _create_log_record(request='Feedback', parameters='OMITTED', username='marge')
    _create_log_record(request='Feedback', parameters='OMITTED', username='marge')
    _create_log_record(request='Feedback', parameters='OMITTED', username='marge', days_delta=0)
    _create_log_record(request='Feedback', parameters='OMITTED', username='homer')
    _create_log_record(request='Feedback', parameters='OMITTED', username='homer')
    _create_log_record(request='Feedback', parameters='OMITTED', username='homer')
    _create_log_record(request='Feedback', parameters='OMITTED', username='homer', days_delta=0)

    start_datetime_period = dt.datetime.combine(
        dt.datetime.now() - dt.timedelta(days=1),
        dt.datetime.min.time(),
        timezone.get_current_timezone(),
    )
    end_datetime_period = dt.datetime.combine(
        start_datetime_period,
        dt.datetime.max.time(),
        timezone.get_current_timezone(),
    )
    app_activities = legacy_models.LegacyPatientActivityLog.objects.get_aggregated_user_app_activities(
        start_datetime_period,
        end_datetime_period,
    )

    assert app_activities.count() == 2
    assert app_activities.filter(username='marge')[0]['count_feedback'] == 3
    assert app_activities.filter(username='homer')[0]['count_feedback'] == 3


def test_get_aggregated_user_app_activities_security_answer_statistics() -> None:
    """Ensure that get_aggregated_user_app_activities correctly aggregates security answers per patient per day."""
    _create_log_record(request='UpdateSecurityQuestionAnswer', parameters='OMITTED', username='marge')
    _create_log_record(request='UpdateSecurityQuestionAnswer', parameters='OMITTED', username='marge')
    _create_log_record(request='UpdateSecurityQuestionAnswer', parameters='OMITTED', username='marge')
    _create_log_record(request='UpdateSecurityQuestionAnswer', parameters='OMITTED', username='marge', days_delta=0)
    _create_log_record(request='UpdateSecurityQuestionAnswer', parameters='OMITTED', username='homer')
    _create_log_record(request='UpdateSecurityQuestionAnswer', parameters='OMITTED', username='homer')
    _create_log_record(request='UpdateSecurityQuestionAnswer', parameters='OMITTED', username='homer')
    _create_log_record(request='UpdateSecurityQuestionAnswer', parameters='OMITTED', username='homer', days_delta=0)

    start_datetime_period = dt.datetime.combine(
        dt.datetime.now() - dt.timedelta(days=1),
        dt.datetime.min.time(),
        timezone.get_current_timezone(),
    )
    end_datetime_period = dt.datetime.combine(
        start_datetime_period,
        dt.datetime.max.time(),
        timezone.get_current_timezone(),
    )
    app_activities = legacy_models.LegacyPatientActivityLog.objects.get_aggregated_user_app_activities(
        start_datetime_period,
        end_datetime_period,
    )

    assert app_activities.count() == 2
    assert app_activities.filter(username='marge')[0]['count_update_security_answers'] == 3
    assert app_activities.filter(username='homer')[0]['count_update_security_answers'] == 3


def test_get_aggregated_user_app_activities_password_update_statistics() -> None:
    """Ensure that get_aggregated_user_app_activities correctly aggregates password updates per patient per day."""
    _create_log_record(request='AccountChange', parameters='OMITTED', username='marge')
    _create_log_record(request='AccountChange', parameters='OMITTED', username='marge')
    _create_log_record(request='AccountChange', parameters='OMITTED', username='marge')
    _create_log_record(request='AccountChange', parameters='OMITTED', username='marge', days_delta=0)
    _create_log_record(request='AccountChange', parameters='OMITTED', username='homer')
    _create_log_record(request='AccountChange', parameters='OMITTED', username='homer')
    _create_log_record(request='AccountChange', parameters='OMITTED', username='homer')
    _create_log_record(request='AccountChange', parameters='OMITTED', username='homer', days_delta=0)

    start_datetime_period = dt.datetime.combine(
        dt.datetime.now() - dt.timedelta(days=1),
        dt.datetime.min.time(),
        timezone.get_current_timezone(),
    )
    end_datetime_period = dt.datetime.combine(
        start_datetime_period,
        dt.datetime.max.time(),
        timezone.get_current_timezone(),
    )
    app_activities = legacy_models.LegacyPatientActivityLog.objects.get_aggregated_user_app_activities(
        start_datetime_period,
        end_datetime_period,
    )

    assert app_activities.count() == 2
    assert app_activities.filter(username='marge')[0]['count_update_passwords'] == 3
    assert app_activities.filter(username='homer')[0]['count_update_passwords'] == 3


def test_get_aggregated_user_app_activities_language_update_statistics() -> None:
    """Ensure that get_aggregated_user_app_activities correctly aggregates language updates per patient per day."""
    _create_log_record(
        request='AccountChange',
        parameters=json.dumps({'FieldToChange': 'Language', 'NewValue': 'EN'}),
        username='marge',
    )
    _create_log_record(
        request='AccountChange',
        parameters=json.dumps({'FieldToChange': 'Language', 'NewValue': 'EN'}),
        username='marge',
    )
    _create_log_record(
        request='AccountChange',
        parameters=json.dumps({'FieldToChange': 'Language', 'NewValue': 'EN'}),
        username='marge',
    )
    _create_log_record(
        request='AccountChange',
        parameters=json.dumps({'FieldToChange': 'Language', 'NewValue': 'EN'}),
        username='marge',
        days_delta=0,
    )
    _create_log_record(
        request='AccountChange',
        parameters=json.dumps({'FieldToChange': 'Language', 'NewValue': 'EN'}),
        username='homer',
    )
    _create_log_record(
        request='AccountChange',
        parameters=json.dumps({'FieldToChange': 'Language', 'NewValue': 'EN'}),
        username='homer',
    )
    _create_log_record(
        request='AccountChange',
        parameters=json.dumps({'FieldToChange': 'Language', 'NewValue': 'EN'}),
        username='homer',
    )
    _create_log_record(
        request='AccountChange',
        parameters=json.dumps({'FieldToChange': 'Language', 'NewValue': 'EN'}),
        username='homer',
        days_delta=0,
    )

    start_datetime_period = dt.datetime.combine(
        dt.datetime.now() - dt.timedelta(days=1),
        dt.datetime.min.time(),
        timezone.get_current_timezone(),
    )
    end_datetime_period = dt.datetime.combine(
        start_datetime_period,
        dt.datetime.max.time(),
        timezone.get_current_timezone(),
    )
    app_activities = legacy_models.LegacyPatientActivityLog.objects.get_aggregated_user_app_activities(
        start_datetime_period,
        end_datetime_period,
    )

    assert app_activities.count() == 2
    assert app_activities.filter(username='marge')[0]['count_update_language'] == 3
    assert app_activities.filter(username='homer')[0]['count_update_language'] == 3


def test_get_aggregated_user_app_activities_android_device_statistics() -> None:
    """Ensure that get_aggregated_user_app_activities correctly aggregates android devices per patient per day."""
    _create_log_record(
        request='Log',
        parameters=json.dumps(
            {
                'Activity': 'Login',
                'ActivityDetails': {'deviceType': 'Android', 'isTrustedDevice': 'true'},
            },
            separators=(',', ':'),
        ),
        username='marge',
    )
    _create_log_record(
        request='Log',
        parameters=json.dumps(
            {
                'Activity': 'Login',
                'ActivityDetails': {'deviceType': 'Android', 'isTrustedDevice': 'true'},
            },
            separators=(',', ':'),
        ),
        username='marge',
    )
    _create_log_record(
        request='Log',
        parameters=json.dumps(
            {
                'Activity': 'Login',
                'ActivityDetails': {'deviceType': 'Android', 'isTrustedDevice': 'false'},
            },
            separators=(',', ':'),
        ),
        username='marge',
    )
    _create_log_record(
        request='Log',
        parameters=json.dumps(
            {
                'Activity': 'Login',
                'ActivityDetails': {'deviceType': 'Android', 'isTrustedDevice': 'false'},
            },
            separators=(',', ':'),
        ),
        username='marge',
        days_delta=0,
    )
    _create_log_record(
        request='Log',
        parameters=json.dumps(
            {
                'Activity': 'Login',
                'ActivityDetails': {'deviceType': 'Android', 'isTrustedDevice': 'true'},
            },
            separators=(',', ':'),
        ),
        username='homer',
    )
    _create_log_record(
        request='Log',
        parameters=json.dumps(
            {
                'Activity': 'Login',
                'ActivityDetails': {'deviceType': 'Android', 'isTrustedDevice': 'true'},
            },
            separators=(',', ':'),
        ),
        username='homer',
    )
    _create_log_record(
        request='Log',
        parameters=json.dumps(
            {
                'Activity': 'Login',
                'ActivityDetails': {'deviceType': 'Android', 'isTrustedDevice': 'false'},
            },
            separators=(',', ':'),
        ),
        username='homer',
    )
    _create_log_record(
        request='Log',
        parameters=json.dumps(
            {
                'Activity': 'Login',
                'ActivityDetails': {'deviceType': 'Android', 'isTrustedDevice': 'false'},
            },
            separators=(',', ':'),
        ),
        username='homer',
        days_delta=0,
    )

    start_datetime_period = dt.datetime.combine(
        dt.datetime.now() - dt.timedelta(days=1),
        dt.datetime.min.time(),
        timezone.get_current_timezone(),
    )
    end_datetime_period = dt.datetime.combine(
        start_datetime_period,
        dt.datetime.max.time(),
        timezone.get_current_timezone(),
    )
    app_activities = legacy_models.LegacyPatientActivityLog.objects.get_aggregated_user_app_activities(
        start_datetime_period,
        end_datetime_period,
    )

    assert app_activities.count() == 2
    assert app_activities.filter(username='marge')[0]['count_device_android'] == 3
    assert app_activities.filter(username='homer')[0]['count_device_android'] == 3


def test_get_aggregated_user_app_activities_ios_device_statistics() -> None:
    """Ensure that get_aggregated_user_app_activities correctly aggregates iOS devices per patient per day."""
    _create_log_record(
        request='Log',
        parameters=json.dumps(
            {
                'Activity': 'Login',
                'ActivityDetails': {'deviceType': 'iOS', 'isTrustedDevice': 'true'},
            },
            separators=(',', ':'),
        ),
        username='marge',
    )
    _create_log_record(
        request='Log',
        parameters=json.dumps(
            {
                'Activity': 'Login',
                'ActivityDetails': {'deviceType': 'iOS', 'isTrustedDevice': 'true'},
            },
            separators=(',', ':'),
        ),
        username='marge',
    )
    _create_log_record(
        request='Log',
        parameters=json.dumps(
            {
                'Activity': 'Login',
                'ActivityDetails': {'deviceType': 'iOS', 'isTrustedDevice': 'false'},
            },
            separators=(',', ':'),
        ),
        username='marge',
    )
    _create_log_record(
        request='Log',
        parameters=json.dumps(
            {
                'Activity': 'Login',
                'ActivityDetails': {'deviceType': 'iOS', 'isTrustedDevice': 'false'},
            },
            separators=(',', ':'),
        ),
        username='marge',
        days_delta=0,
    )
    _create_log_record(
        request='Log',
        parameters=json.dumps(
            {
                'Activity': 'Login',
                'ActivityDetails': {'deviceType': 'iOS', 'isTrustedDevice': 'true'},
            },
            separators=(',', ':'),
        ),
        username='homer',
    )
    _create_log_record(
        request='Log',
        parameters=json.dumps(
            {
                'Activity': 'Login',
                'ActivityDetails': {'deviceType': 'iOS', 'isTrustedDevice': 'true'},
            },
            separators=(',', ':'),
        ),
        username='homer',
    )
    _create_log_record(
        request='Log',
        parameters=json.dumps(
            {
                'Activity': 'Login',
                'ActivityDetails': {'deviceType': 'iOS', 'isTrustedDevice': 'false'},
            },
            separators=(',', ':'),
        ),
        username='homer',
    )
    _create_log_record(
        request='Log',
        parameters=json.dumps(
            {
                'Activity': 'Login',
                'ActivityDetails': {'deviceType': 'iOS', 'isTrustedDevice': 'false'},
            },
            separators=(',', ':'),
        ),
        username='homer',
        days_delta=0,
    )

    start_datetime_period = dt.datetime.combine(
        dt.datetime.now() - dt.timedelta(days=1),
        dt.datetime.min.time(),
        timezone.get_current_timezone(),
    )
    end_datetime_period = dt.datetime.combine(
        start_datetime_period,
        dt.datetime.max.time(),
        timezone.get_current_timezone(),
    )
    app_activities = legacy_models.LegacyPatientActivityLog.objects.get_aggregated_user_app_activities(
        start_datetime_period,
        end_datetime_period,
    )

    assert app_activities.count() == 2
    assert app_activities.filter(username='marge')[0]['count_device_ios'] == 3
    assert app_activities.filter(username='homer')[0]['count_device_ios'] == 3


def test_get_aggregated_user_app_activities_browser_device_statistics() -> None:
    """Ensure that get_aggregated_user_app_activities correctly aggregates browser devices per patient per day."""
    _create_log_record(
        request='Log',
        parameters=json.dumps(
            {
                'Activity': 'Login',
                'ActivityDetails': {'deviceType': 'browser', 'isTrustedDevice': 'true'},
            },
            separators=(',', ':'),
        ),
        username='marge',
    )
    _create_log_record(
        request='Log',
        parameters=json.dumps(
            {
                'Activity': 'Login',
                'ActivityDetails': {'deviceType': 'browser', 'isTrustedDevice': 'true'},
            },
            separators=(',', ':'),
        ),
        username='marge',
    )
    _create_log_record(
        request='Log',
        parameters=json.dumps(
            {
                'Activity': 'Login',
                'ActivityDetails': {'deviceType': 'browser', 'isTrustedDevice': 'false'},
            },
            separators=(',', ':'),
        ),
        username='marge',
    )
    _create_log_record(
        request='Log',
        parameters=json.dumps(
            {
                'Activity': 'Login',
                'ActivityDetails': {'deviceType': 'browser', 'isTrustedDevice': 'false'},
            },
            separators=(',', ':'),
        ),
        username='marge',
        days_delta=0,
    )
    _create_log_record(
        request='Log',
        parameters=json.dumps(
            {
                'Activity': 'Login',
                'ActivityDetails': {'deviceType': 'browser', 'isTrustedDevice': 'true'},
            },
            separators=(',', ':'),
        ),
        username='homer',
    )
    _create_log_record(
        request='Log',
        parameters=json.dumps(
            {
                'Activity': 'Login',
                'ActivityDetails': {'deviceType': 'browser', 'isTrustedDevice': 'true'},
            },
            separators=(',', ':'),
        ),
        username='homer',
    )
    _create_log_record(
        request='Log',
        parameters=json.dumps(
            {
                'Activity': 'Login',
                'ActivityDetails': {'deviceType': 'browser', 'isTrustedDevice': 'false'},
            },
            separators=(',', ':'),
        ),
        username='homer',
    )
    _create_log_record(
        request='Log',
        parameters=json.dumps(
            {
                'Activity': 'Login',
                'ActivityDetails': {'deviceType': 'browser', 'isTrustedDevice': 'false'},
            },
            separators=(',', ':'),
        ),
        username='homer',
        days_delta=0,
    )

    start_datetime_period = dt.datetime.combine(
        dt.datetime.now() - dt.timedelta(days=1),
        dt.datetime.min.time(),
        timezone.get_current_timezone(),
    )
    end_datetime_period = dt.datetime.combine(
        start_datetime_period,
        dt.datetime.max.time(),
        timezone.get_current_timezone(),
    )
    app_activities = legacy_models.LegacyPatientActivityLog.objects.get_aggregated_user_app_activities(
        start_datetime_period,
        end_datetime_period,
    )

    assert app_activities.count() == 2
    assert app_activities.filter(username='marge')[0]['count_device_browser'] == 3
    assert app_activities.filter(username='homer')[0]['count_device_browser'] == 3


# tests for populating patient app activities

def test_get_aggregated_patient_app_no_activities() -> None:
    """Ensure that get_aggregated_patient_app_activities function does not fail when there is no app statistics."""
    start_datetime_period = dt.datetime.combine(
        dt.datetime.now() - dt.timedelta(days=1),
        dt.datetime.min.time(),
        timezone.get_current_timezone(),
    )
    end_datetime_period = dt.datetime.combine(
        start_datetime_period,
        dt.datetime.max.time(),
        timezone.get_current_timezone(),
    )
    assert legacy_models.LegacyPatientActivityLog.objects.get_aggregated_patient_app_activities(
        start_datetime_period,
        end_datetime_period,
    ).count() == 0


def test_get_aggregated_patient_app_activities_previous_day() -> None:
    """Ensure that get_aggregated_patient_app_activities function returns patients' previous day activities."""
    _create_log_record(
        request='DocumentContent', parameters=json.dumps(['1']), target_patient_id=51, username='marge',
    )
    _create_log_record(
        request='DocumentContent', parameters=json.dumps(['2']), target_patient_id=51, username='marge',
    )
    _create_log_record(
        request='Log',
        parameters=json.dumps({'Activity': 'EducationalMaterialSerNum', 'ActivityDetails': '1'}),
        target_patient_id=51,
        username='marge',
    )
    _create_log_record(
        request='QuestionnaireUpdateStatus',
        parameters=json.dumps({
            'answerQuestionnaire_id': '1', 'new_status': '2', 'user_display_name': 'Marge Simpson',
        }).replace(' ', ''),
        target_patient_id=51,
        username='marge',
    )
    _create_log_record(
        request='PatientTestTypeResults',
        parameters=json.dumps({'testTypeSerNum': '1'}),
        target_patient_id=51,
        username='marge',
    )

    # current day records should not be included to the final queryset
    _create_log_record(
        request='Checkin', parameters='OMITTED', target_patient_id=51, username='marge', days_delta=0,
    )
    _create_log_record(
        request='DocumentContent',
        parameters=json.dumps(['3']),
        target_patient_id=51,
        username='marge',
        days_delta=0,
    )
    _create_log_record(
        request='QuestionnaireUpdateStatus',
        parameters=json.dumps({
            'answerQuestionnaire_id': '3', 'new_status': '2', 'user_display_name': 'Marge Simpson',
        }).replace(' ', ''),
        target_patient_id=51,
        username='marge',
        days_delta=0,
    )

    start_datetime_period = dt.datetime.combine(
        dt.datetime.now() - dt.timedelta(days=1),
        dt.datetime.min.time(),
        timezone.get_current_timezone(),
    )
    end_datetime_period = dt.datetime.combine(
        start_datetime_period,
        dt.datetime.max.time(),
        timezone.get_current_timezone(),
    )
    app_activities = legacy_models.LegacyPatientActivityLog.objects.get_aggregated_patient_app_activities(
        start_datetime_period,
        end_datetime_period,
    )

    assert app_activities.count() == 1
    assert app_activities.filter(username='marge')[0]['count_checkins'] == 0
    assert app_activities.filter(username='marge')[0]['count_documents'] == 2
    assert app_activities.filter(username='marge')[0]['count_educational_materials'] == 1
    assert app_activities.filter(username='marge')[0]['count_questionnaires_complete'] == 1
    assert app_activities.filter(username='marge')[0]['count_labs'] == 1


def test_get_aggregated_patient_app_activities_current_day() -> None:
    """Ensure that get_aggregated_patient_app_activities function returns patients' current day activities."""
    _create_log_record(
        request='DocumentContent', parameters=json.dumps(['1']), target_patient_id=51, username='marge', days_delta=0,
    )
    _create_log_record(
        request='DocumentContent', parameters=json.dumps(['2']), target_patient_id=51, username='marge', days_delta=0,
    )
    _create_log_record(
        request='Log',
        parameters=json.dumps({'Activity': 'EducationalMaterialSerNum', 'ActivityDetails': '1'}),
        target_patient_id=51,
        username='marge',
        days_delta=0,
    )
    _create_log_record(
        request='QuestionnaireUpdateStatus',
        parameters=json.dumps({
            'answerQuestionnaire_id': '1', 'new_status': '2', 'user_display_name': 'Marge Simpson',
        }).replace(' ', ''),
        target_patient_id=51,
        username='marge',
        days_delta=0,
    )
    _create_log_record(
        request='PatientTestTypeResults',
        parameters=json.dumps({'testTypeSerNum': '1'}),
        target_patient_id=51,
        username='marge',
        days_delta=0,
    )

    # previous day records should not be included to the final queryset
    _create_log_record(
        request='Checkin', parameters='OMITTED', target_patient_id=51, username='marge',
    )
    _create_log_record(
        request='DocumentContent',
        parameters=json.dumps(['3']),
        target_patient_id=51,
        username='marge',
    )
    _create_log_record(
        request='QuestionnaireUpdateStatus',
        parameters=json.dumps({
            'answerQuestionnaire_id': '3', 'new_status': '2', 'user_display_name': 'Marge Simpson',
        }).replace(' ', ''),
        target_patient_id=51,
        username='marge',
    )

    start_datetime_period = dt.datetime.combine(
        dt.datetime.now(),
        dt.datetime.min.time(),
        timezone.get_current_timezone(),
    )
    end_datetime_period = dt.datetime.combine(
        start_datetime_period,
        dt.datetime.max.time(),
        timezone.get_current_timezone(),
    )
    app_activities = legacy_models.LegacyPatientActivityLog.objects.get_aggregated_patient_app_activities(
        start_datetime_period,
        end_datetime_period,
    )

    assert app_activities.count() == 1
    assert app_activities.filter(username='marge')[0]['count_checkins'] == 0
    assert app_activities.filter(username='marge')[0]['count_documents'] == 2
    assert app_activities.filter(username='marge')[0]['count_educational_materials'] == 1
    assert app_activities.filter(username='marge')[0]['count_questionnaires_complete'] == 1
    assert app_activities.filter(username='marge')[0]['count_labs'] == 1


def test_get_aggregated_user_app_activities_checkin_statistics() -> None:
    """Ensure that get_aggregated_user_app_activities returns correctly aggregated checkins per patient per day."""
    _create_log_record(request='Checkin', parameters='OMITTED', username='marge', target_patient_id=51)
    _create_log_record(request='Checkin', parameters='OMITTED', username='marge', target_patient_id=51)
    _create_log_record(request='Checkin', parameters='OMITTED', username='marge', target_patient_id=51)
    _create_log_record(
        request='Checkin', parameters='OMITTED', username='marge', target_patient_id=51, days_delta=0,
    )
    _create_log_record(request='Checkin', parameters='OMITTED', username='homer', target_patient_id=52)
    _create_log_record(request='Checkin', parameters='OMITTED', username='homer', target_patient_id=52)
    _create_log_record(request='Checkin', parameters='OMITTED', username='homer', target_patient_id=52)
    _create_log_record(
        request='Checkin', parameters='OMITTED', username='homer', target_patient_id=52, days_delta=0,
    )

    start_datetime_period = dt.datetime.combine(
        dt.datetime.now() - dt.timedelta(days=1),
        dt.datetime.min.time(),
        timezone.get_current_timezone(),
    )
    end_datetime_period = dt.datetime.combine(
        start_datetime_period,
        dt.datetime.max.time(),
        timezone.get_current_timezone(),
    )

    app_activities = legacy_models.LegacyPatientActivityLog.objects.get_aggregated_patient_app_activities(
        start_datetime_period,
        end_datetime_period,
    )

    assert app_activities.count() == 2
    assert app_activities.filter(username='marge')[0]['count_checkins'] == 3
    assert app_activities.filter(username='homer')[0]['count_checkins'] == 3


def test_get_aggregated_user_app_activities_documents_statistics() -> None:
    """Ensure that get_aggregated_user_app_activities returns correctly aggregated documents per patient per day."""
    _create_log_record(request='DocumentContent', parameters='OMITTED', username='marge', target_patient_id=51)
    _create_log_record(request='DocumentContent', parameters='OMITTED', username='marge', target_patient_id=51)
    _create_log_record(request='DocumentContent', parameters='OMITTED', username='marge', target_patient_id=51)
    _create_log_record(
        request='DocumentContent', parameters='OMITTED', username='marge', target_patient_id=51, days_delta=0,
    )
    _create_log_record(request='DocumentContent', parameters='OMITTED', username='homer', target_patient_id=52)
    _create_log_record(request='DocumentContent', parameters='OMITTED', username='homer', target_patient_id=52)
    _create_log_record(request='DocumentContent', parameters='OMITTED', username='homer', target_patient_id=52)
    _create_log_record(
        request='DocumentContent', parameters='OMITTED', username='homer', target_patient_id=52, days_delta=0,
    )

    start_datetime_period = dt.datetime.combine(
        dt.datetime.now() - dt.timedelta(days=1),
        dt.datetime.min.time(),
        timezone.get_current_timezone(),
    )
    end_datetime_period = dt.datetime.combine(
        start_datetime_period,
        dt.datetime.max.time(),
        timezone.get_current_timezone(),
    )

    app_activities = legacy_models.LegacyPatientActivityLog.objects.get_aggregated_patient_app_activities(
        start_datetime_period,
        end_datetime_period,
    )

    assert app_activities.count() == 2
    assert app_activities.filter(username='marge')[0]['count_documents'] == 3
    assert app_activities.filter(username='homer')[0]['count_documents'] == 3


def test_get_aggregated_user_app_activities_edu_materials_statistics() -> None:
    """Ensure get_aggregated_user_app_activities correctly aggregates educational materials per patient per day."""
    _create_log_record(
        request='Log',
        parameters=json.dumps({'Activity': 'EducationalMaterialSerNum', 'ActivityDetails': '1'}),
        username='marge',
        target_patient_id=51,
    )
    _create_log_record(
        request='Log',
        parameters=json.dumps({'Activity': 'EducationalMaterialSerNum', 'ActivityDetails': '2'}),
        username='marge',
        target_patient_id=51,
    )
    _create_log_record(
        request='Log',
        parameters=json.dumps({'Activity': 'EducationalMaterialSerNum', 'ActivityDetails': '3'}),
        username='marge',
        target_patient_id=51,
    )
    _create_log_record(
        request='Log',
        parameters=json.dumps({'Activity': 'EducationalMaterialSerNum', 'ActivityDetails': '1'}),
        username='marge',
        target_patient_id=51,
        days_delta=0,
    )
    _create_log_record(
        request='Log',
        parameters=json.dumps({'Activity': 'EducationalMaterialSerNum', 'ActivityDetails': '4'}),
        username='homer',
        target_patient_id=52,
    )
    _create_log_record(
        request='Log',
        parameters=json.dumps({'Activity': 'EducationalMaterialSerNum', 'ActivityDetails': '5'}),
        username='homer',
        target_patient_id=52,
    )
    _create_log_record(
        request='Log',
        parameters=json.dumps({'Activity': 'EducationalMaterialSerNum', 'ActivityDetails': '6'}),
        username='homer',
        target_patient_id=52,
    )
    _create_log_record(
        request='Log',
        parameters=json.dumps({'Activity': 'EducationalMaterialSerNum', 'ActivityDetails': '1'}),
        username='homer',
        target_patient_id=52,
        days_delta=0,
    )

    start_datetime_period = dt.datetime.combine(
        dt.datetime.now() - dt.timedelta(days=1),
        dt.datetime.min.time(),
        timezone.get_current_timezone(),
    )
    end_datetime_period = dt.datetime.combine(
        start_datetime_period,
        dt.datetime.max.time(),
        timezone.get_current_timezone(),
    )

    app_activities = legacy_models.LegacyPatientActivityLog.objects.get_aggregated_patient_app_activities(
        start_datetime_period,
        end_datetime_period,
    )

    assert app_activities.count() == 2
    assert app_activities.filter(username='marge')[0]['count_educational_materials'] == 3
    assert app_activities.filter(username='homer')[0]['count_educational_materials'] == 3


def test_get_aggregated_user_app_activities_questionnaires_statistics() -> None:
    """Ensure get_aggregated_user_app_activities returns correctly aggregated questionnaires per patient per day."""
    _create_log_record(
        request='QuestionnaireUpdateStatus',
        parameters=json.dumps({
            'answerQuestionnaire_id': '1', 'new_status': '2', 'user_display_name': 'Marge Simpson',
        }).replace(' ', ''),
        username='marge',
        target_patient_id=51,
    )
    _create_log_record(
        request='QuestionnaireUpdateStatus',
        parameters=json.dumps({
            'answerQuestionnaire_id': '2', 'new_status': '2', 'user_display_name': 'Marge Simpson',
        }).replace(' ', ''),
        username='marge',
        target_patient_id=51,
    )
    _create_log_record(
        request='QuestionnaireUpdateStatus',
        parameters=json.dumps({
            'answerQuestionnaire_id': '3', 'new_status': '2', 'user_display_name': 'Marge Simpson',
        }).replace(' ', ''),
        username='marge',
        target_patient_id=51,
    )
    _create_log_record(
        request='QuestionnaireUpdateStatus',
        parameters=json.dumps({
            'answerQuestionnaire_id': '4', 'new_status': '2', 'user_display_name': 'Marge Simpson',
        }).replace(' ', ''),
        username='marge',
        target_patient_id=51,
        days_delta=0,
    )
    _create_log_record(
        request='QuestionnaireUpdateStatus',
        parameters=json.dumps({
            'answerQuestionnaire_id': '5', 'new_status': '2', 'user_display_name': 'Homer Simpson',
        }).replace(' ', ''),
        username='homer',
        target_patient_id=52,
    )
    _create_log_record(
        request='QuestionnaireUpdateStatus',
        parameters=json.dumps({
            'answerQuestionnaire_id': '6', 'new_status': '2', 'user_display_name': 'Homer Simpson',
        }).replace(' ', ''),
        username='homer',
        target_patient_id=52,
    )
    _create_log_record(
        request='QuestionnaireUpdateStatus',
        parameters=json.dumps({
            'answerQuestionnaire_id': '7', 'new_status': '2', 'user_display_name': 'Homer Simpson',
        }).replace(' ', ''),
        username='homer',
        target_patient_id=52,
    )
    _create_log_record(
        request='QuestionnaireUpdateStatus',
        parameters=json.dumps({
            'answerQuestionnaire_id': '8', 'new_status': '2', 'user_display_name': 'Homer Simpson',
        }).replace(' ', ''),
        username='homer',
        target_patient_id=52,
        days_delta=0,
    )

    start_datetime_period = dt.datetime.combine(
        dt.datetime.now() - dt.timedelta(days=1),
        dt.datetime.min.time(),
        timezone.get_current_timezone(),
    )
    end_datetime_period = dt.datetime.combine(
        start_datetime_period,
        dt.datetime.max.time(),
        timezone.get_current_timezone(),
    )

    app_activities = legacy_models.LegacyPatientActivityLog.objects.get_aggregated_patient_app_activities(
        start_datetime_period,
        end_datetime_period,
    )

    assert app_activities.count() == 2
    assert app_activities.filter(username='marge')[0]['count_questionnaires_complete'] == 3
    assert app_activities.filter(username='homer')[0]['count_questionnaires_complete'] == 3


def test_get_aggregated_user_app_activities_labs_statistics() -> None:
    """Ensure that get_aggregated_user_app_activities returns correctly aggregated labs per patient per day."""
    _create_log_record(
        request='PatientTestTypeResults',
        parameters=json.dumps({'testTypeSerNum': '1'}),
        username='marge',
        target_patient_id=51,
    )
    _create_log_record(
        request='PatientTestTypeResults',
        parameters=json.dumps({'testTypeSerNum': '2'}),
        username='marge',
        target_patient_id=51,
    )
    _create_log_record(
        request='PatientTestTypeResults',
        parameters=json.dumps({'testTypeSerNum': '3'}),
        username='marge',
        target_patient_id=51,
    )
    _create_log_record(
        request='PatientTestTypeResults',
        parameters=json.dumps({'testTypeSerNum': '4'}),
        username='marge',
        target_patient_id=51,
        days_delta=0,
    )
    _create_log_record(
        request='PatientTestTypeResults',
        parameters=json.dumps({'testTypeSerNum': '5'}),
        username='homer',
        target_patient_id=52,
    )
    _create_log_record(
        request='PatientTestTypeResults',
        parameters=json.dumps({'testTypeSerNum': '6'}),
        username='homer',
        target_patient_id=52,
    )
    _create_log_record(
        request='PatientTestTypeResults',
        parameters=json.dumps({'testTypeSerNum': '7'}),
        username='homer',
        target_patient_id=52,
    )
    _create_log_record(
        request='PatientTestTypeResults',
        parameters=json.dumps({'testTypeSerNum': '8'}),
        username='homer',
        target_patient_id=52,
        days_delta=0,
    )

    start_datetime_period = dt.datetime.combine(
        dt.datetime.now() - dt.timedelta(days=1),
        dt.datetime.min.time(),
        timezone.get_current_timezone(),
    )
    end_datetime_period = dt.datetime.combine(
        start_datetime_period,
        dt.datetime.max.time(),
        timezone.get_current_timezone(),
    )

    app_activities = legacy_models.LegacyPatientActivityLog.objects.get_aggregated_patient_app_activities(
        start_datetime_period,
        end_datetime_period,
    )

    assert app_activities.count() == 2
    assert app_activities.filter(username='marge')[0]['count_labs'] == 3
    assert app_activities.filter(username='homer')[0]['count_labs'] == 3


PARAMETERS_DEFAULT = json.dumps(
    {
        'Activity': 'Login',
        'ActivityDetails': {'deviceType': 'browser', 'isTrustedDevice': 'true'},
    },
    separators=(',', ':'),
)


def _create_log_record(
    request: str = 'Log',
    parameters: str = PARAMETERS_DEFAULT,
    target_patient_id: int | None = None,
    username: str = 'username',
    app_version: str = '100.100.100',
    days_delta: int = 1,
) -> legacy_factories.LegacyPatientActivityLogFactory:
    data = {
        'request': request,
        'parameters': parameters,
        'target_patient_id': target_patient_id,
        'username': username,
        'date_time': timezone.localtime(timezone.now()) - dt.timedelta(days=days_delta),
        'app_version': app_version,
    }
    return legacy_factories.LegacyPatientActivityLogFactory(**data)
