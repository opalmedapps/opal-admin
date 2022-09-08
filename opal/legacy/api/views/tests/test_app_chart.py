from django.urls import reverse

import pytest
from rest_framework.test import APIClient

from opal.legacy import factories, models
from opal.users.models import User

pytestmark = pytest.mark.django_db(databases=['default', 'legacy'])


class TestChartAppView:
    """
    Class wrapper for chart page request tests.

    PatientSernum 51 is define in the legacy databse by DBV script for testing purpose.
    """

    def test_get_chart_data_request(self, api_client: APIClient, admin_user: User) -> None:
        """Test if the response as the required keys."""
        user = factories.LegacyUserFactory()
        api_client.force_login(user=admin_user)
        api_client.credentials(HTTP_APPUSERID=user.username)
        response = api_client.get(reverse('api:app-chart', kwargs={'legacy_id': 51}))
        assert 'unread_appointment_count' in response.data
        assert 'unread_document_count' in response.data
        assert 'unread_txteammessage_count' in response.data
        assert 'unread_educationalmaterial_count' in response.data
        assert 'unread_questionnaire_count' in response.data

    def test_get_unread_appointment_count(self) -> None:
        """Test if function returns number of unread appointments."""
        patient = factories.LegacyPatientFactory()
        alias = factories.LegacyAliasFactory()
        alias_expression = factories.LegacyAliasexpressionFactory(aliassernum=alias)

        factories.LegacyAppointmentFactory(
            patientsernum=patient,
            aliasexpressionsernum=alias_expression,
        )
        factories.LegacyAppointmentFactory(
            patientsernum=patient,
            aliasexpressionsernum=alias_expression,
        )
        factories.LegacyAppointmentFactory(
            patientsernum=patient,
            aliasexpressionsernum=alias_expression,
            readstatus=1,
        )

        appointments = models.LegacyAppointment.objects.get_unread_queryset(patient.patientsernum).count()
        assert appointments == 2

    def test_get_unread_txteammessage_count(self) -> None:
        """Test if function returns number of unread txteammessages."""
        patient = factories.LegacyPatientFactory()
        factories.LegacyTxTeamMessageFactory(patientsernum=patient)
        factories.LegacyTxTeamMessageFactory(patientsernum=patient)
        factories.LegacyTxTeamMessageFactory(patientsernum=patient, readstatus=1)
        txteammessages = models.LegacyTxTeamMessage.objects.get_unread_queryset(patient.patientsernum).count()
        assert txteammessages == 2

    def test_get_unread_edumaterial_count(self) -> None:
        """Test if function returns number of unread educational materials."""
        patient = factories.LegacyPatientFactory()
        factories.LegacyEducationalMaterialFactory(patientsernum=patient)
        factories.LegacyEducationalMaterialFactory(patientsernum=patient)
        factories.LegacyEducationalMaterialFactory(patientsernum=patient, readstatus=1)
        edumaterials = models.LegacyEducationalMaterial.objects.get_unread_queryset(patient.patientsernum).count()
        assert edumaterials == 2

    def test_get_unread_questionnaire_count(self) -> None:
        """Test if function returns number of unread questionnaires."""
        patient = factories.LegacyPatientFactory()
        factories.LegacyQuestionnaireFactory(patientsernum=patient)
        factories.LegacyQuestionnaireFactory(patientsernum=patient)
        factories.LegacyQuestionnaireFactory(patientsernum=patient, completedflag=1)
        questionnaires = models.LegacyQuestionnaire.objects.get_unread_queryset(patient.patientsernum).count()
        assert questionnaires == 2
