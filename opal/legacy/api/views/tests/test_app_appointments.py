import json

from django.urls import reverse

import pytest
from pytest_mock import MockerFixture
from rest_framework.test import APIClient

from opal.legacy import factories
from opal.legacy.api.views.app_appointments import AppAppointmentsView
from opal.patients import factories as patient_factories
from opal.users.models import User

pytestmark = pytest.mark.django_db(databases=['default', 'legacy'])


class TestAppAppointmentsView:
    """Class wrapper for appointments request tests."""

    class_instance = AppAppointmentsView()

    def test_get_all_appointments(self, api_client: APIClient, admin_user: User, mocker: MockerFixture) -> None:
        """Test getting all appointment details."""
        relationship = patient_factories.Relationship(status='CON')
        patient = factories.LegacyPatientFactory(patientsernum=relationship.patient.legacy_id)
        alias = factories.LegacyAliasFactory()
        alias_expression = factories.LegacyAliasexpressionFactory(aliassernum=alias)

        appointment1 = factories.LegacyAppointmentFactory(
            patientsernum=patient,
            aliasexpressionsernum=alias_expression,
        )
        appointment2 = factories.LegacyAppointmentFactory(
            patientsernum=patient,
            aliasexpressionsernum=alias_expression,
        )

        user = factories.LegacyUserFactory()
        api_client.force_login(user=admin_user)
        api_client.credentials(HTTP_APPUSERID=user.username)
        response = api_client.get(reverse('api:app-appointments'))
        assert response.data['count'] == 2
        assert response.data['results'][0]['appointmentsernum'] == appointment1.appointmentsernum
        assert response.data['results'][1]['appointmentsernum'] == appointment2.appointmentsernum

    def test_get_appointments_by_ids(self, api_client: APIClient, admin_user: User, mocker: MockerFixture) -> None:
        """Test getting appointment details by appointmentsernum array."""
        relationship = patient_factories.Relationship(status='CON')
        patient = factories.LegacyPatientFactory(patientsernum=relationship.patient.legacy_id)
        alias = factories.LegacyAliasFactory()
        alias_expression = factories.LegacyAliasexpressionFactory(aliassernum=alias)

        appointment1 = factories.LegacyAppointmentFactory(
            patientsernum=patient,
            aliasexpressionsernum=alias_expression,
        )
        appointment2 = factories.LegacyAppointmentFactory(
            patientsernum=patient,
            aliasexpressionsernum=alias_expression,
        )

        user = factories.LegacyUserFactory()
        api_client.force_login(user=admin_user)
        api_client.credentials(HTTP_APPUSERID=user.username)
        # To send json data to request body, need to use api_client.generic
        response = api_client.generic(
            method='GET',
            path=reverse('api:app-appointments'),
            data=json.dumps({'ids': [appointment1.appointmentsernum]}),
            content_type='application/json',
        )
        assert response.data['count'] == 1
        assert response.data['results'][0]['appointmentsernum'] == appointment1.appointmentsernum
        assert response.data['results'][0]['appointmentsernum'] != appointment2.appointmentsernum
        assert 'patient' in response.data['results'][0]
        assert 'alias' in response.data['results'][0]
