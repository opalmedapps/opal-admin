from django.db import connections
from django.urls import reverse

import pytest
from pytest_django.plugin import _DatabaseBlocker  # noqa: WPS450
from rest_framework.test import APIClient

from opal.legacy import factories, models
from opal.legacy_questionnaires import factories as questionnaires_factories
from opal.legacy_questionnaires import models as questionnaires_models
from opal.patients import factories as patient_factories
from opal.users.models import User

pytestmark = pytest.mark.django_db(databases=['default', 'legacy', 'questionnaire'])


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
        relationship = patient_factories.Relationship(status='CON')
        patient = factories.LegacyPatientFactory(patientsernum=relationship.patient.legacy_id)
        user = relationship.caregiver.user
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
            readby=user.username,
        )

        appointments = models.LegacyAppointment.objects.get_unread_queryset(
            patient.patientsernum,
            user.username,
        ).count()
        assert appointments == 2

    def test_get_unread_txteammessage_count(self) -> None:
        """Test if function returns number of unread txteammessages."""
        relationship = patient_factories.Relationship(status='CON')
        patient = factories.LegacyPatientFactory(patientsernum=relationship.patient.legacy_id)
        user = relationship.caregiver.user
        factories.LegacyTxTeamMessageFactory(patientsernum=patient)
        factories.LegacyTxTeamMessageFactory(patientsernum=patient)
        factories.LegacyTxTeamMessageFactory(patientsernum=patient, readby=user.username)
        txteammessages = models.LegacyTxTeamMessage.objects.get_unread_queryset(
            patient.patientsernum,
            user.username,
        ).count()
        assert txteammessages == 2

    def test_get_unread_edumaterial_count(self) -> None:
        """Test if function returns number of unread educational materials."""
        relationship = patient_factories.Relationship(status='CON')
        patient = factories.LegacyPatientFactory(patientsernum=relationship.patient.legacy_id)
        user = relationship.caregiver.user
        factories.LegacyEducationalMaterialFactory(patientsernum=patient)
        factories.LegacyEducationalMaterialFactory(patientsernum=patient)
        factories.LegacyEducationalMaterialFactory(patientsernum=patient, readby=user.username)
        edumaterials = models.LegacyEducationalMaterial.objects.get_unread_queryset(
            patient.patientsernum,
            user.username,
        ).count()
        assert edumaterials == 2

    def test_get_unread_questionnaire_count(self, django_db_blocker: _DatabaseBlocker) -> None:
        """Test if function returns number of new clinical questionnaires."""
        # Because of the test_QuestionnaireDB setup for the export reports,
        # there are already random test data in test_QuestionnaireDB
        # So we have to clear and re-populate with the correct factories...
        with django_db_blocker.unblock():
            with connections['questionnaire'].cursor() as conn:
                conn.execute('SET FOREIGN_KEY_CHECKS=0;DELETE FROM answerQuestionnaire;DELETE FROM questionnaire;DELETE FROM purpose;')  # noqa: E501
                conn.close()
        clinical_purpose = questionnaires_factories.LegacyPurposeFactory(id=1)
        research_purpose = questionnaires_factories.LegacyPurposeFactory(id=2)
        clinical_questionnaire = questionnaires_factories.LegacyQuestionnaireFactory(purposeid=clinical_purpose)
        research_questionnaire = questionnaires_factories.LegacyQuestionnaireFactory(purposeid=research_purpose)
        patient_one = questionnaires_factories.LegacyPatientFactory()
        patient_two = questionnaires_factories.LegacyPatientFactory(externalid=52)

        # status=0 by default for new questionnaires
        questionnaires_factories.LegacyAnswerQuestionnaireFactory(
            questionnaireid=clinical_questionnaire,
            patientid=patient_one,
        )
        # status=1 indicates in progress
        questionnaires_factories.LegacyAnswerQuestionnaireFactory(
            questionnaireid=clinical_questionnaire,
            patientid=patient_one,
            status=1,
        )
        questionnaires_factories.LegacyAnswerQuestionnaireFactory(
            questionnaireid=research_questionnaire,
            patientid=patient_one,
        )
        questionnaires_factories.LegacyAnswerQuestionnaireFactory(
            questionnaireid=clinical_questionnaire,
            patientid=patient_two,
        )
        new_questionnaires = questionnaires_models.LegacyQuestionnaire.objects.get_new_queryset(
            patient_sernum=51,
        ).count()
        assert new_questionnaires == 1
