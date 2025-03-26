from django.urls import reverse

import pytest
from rest_framework.test import APIClient

from opal.caregivers import factories as caregiver_factories
from opal.legacy import factories, models
from opal.legacy_questionnaires import factories as questionnaires_factories
from opal.legacy_questionnaires import models as questionnaires_models
from opal.patients import factories as patient_factories
from opal.users import factories as user_factories
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
        assert 'unread_research_questionnaire_count' in response.data
        assert 'unread_consent_questionnaire_count' in response.data

    def test_get_unread_appointment_count(self) -> None:
        """Test if function returns number of unread appointments."""
        relationship = patient_factories.Relationship(status='CON')
        patient = factories.LegacyPatientFactory(patientsernum=relationship.patient.legacy_id)
        user = relationship.caregiver.user
        alias = factories.LegacyAliasFactory()
        alias_expression = factories.LegacyAliasExpressionFactory(aliassernum=alias)

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

    @pytest.mark.parametrize(
        'clear_questionnairedb',
        [['answerQuestionnaire', 'questionnaire', 'purpose']],
        indirect=True,
    )
    def test_get_unread_questionnaire_count(self, clear_questionnairedb: None) -> None:
        """Test if function returns number of new clinical questionnaires."""
        dictionary = questionnaires_factories.LegacyDictionaryFactory(content='Caregiver', language_id=2)
        respondent = questionnaires_factories.LegacyRespondentFactory(title=dictionary)
        clinical_purpose = questionnaires_factories.LegacyPurposeFactory(id=1)
        research_purpose = questionnaires_factories.LegacyPurposeFactory(id=2)
        consent_purpose = questionnaires_factories.LegacyPurposeFactory(id=4)
        clinical_questionnaire = questionnaires_factories.LegacyQuestionnaireFactory(
            purpose=clinical_purpose,
            respondent=respondent,
        )
        research_questionnaire = questionnaires_factories.LegacyQuestionnaireFactory(
            purpose=research_purpose,
            respondent=respondent,
        )
        consent_questionnaire = questionnaires_factories.LegacyQuestionnaireFactory(
            purpose=consent_purpose,
            respondent=respondent,
        )
        patient_one = questionnaires_factories.LegacyPatientFactory()
        patient_two = questionnaires_factories.LegacyPatientFactory(external_id=52)

        user = user_factories.Caregiver()
        caregiver_profile = caregiver_factories.CaregiverProfile(user=user)
        patient = patient_factories.Patient(legacy_id=patient_one.external_id)
        relationship_type = patient_factories.RelationshipType(can_answer_questionnaire=True)
        relationship = patient_factories.Relationship(
            caregiver=caregiver_profile,
            patient=patient,
            type=relationship_type,
            status='CON',
        )
        relationship.refresh_from_db()

        # status=0 by default for new questionnaires
        questionnaires_factories.LegacyAnswerQuestionnaireFactory(
            questionnaire=clinical_questionnaire,
            patient=patient_one,
        )
        # status=1 indicates in progress
        questionnaires_factories.LegacyAnswerQuestionnaireFactory(
            questionnaire=clinical_questionnaire,
            patient=patient_one,
            status=1,
        )
        questionnaires_factories.LegacyAnswerQuestionnaireFactory(
            questionnaire=research_questionnaire,
            patient=patient_one,
        )
        questionnaires_factories.LegacyAnswerQuestionnaireFactory(
            questionnaire=consent_questionnaire,
            patient=patient_one,
        )
        questionnaires_factories.LegacyAnswerQuestionnaireFactory(
            questionnaire=clinical_questionnaire,
            patient=patient_two,
        )
        new_questionnaires = questionnaires_models.LegacyQuestionnaire.objects.new_questionnaires(
            patient_sernum=patient_one.external_id,
            username=user.username,
            purpose_id=1,
        ).count()
        assert new_questionnaires == 1
        new_questionnaires = questionnaires_models.LegacyQuestionnaire.objects.new_questionnaires(
            patient_sernum=patient_one.external_id,
            username=user.username,
            purpose_id=2,
        ).count()
        assert new_questionnaires == 1
        new_questionnaires = questionnaires_models.LegacyQuestionnaire.objects.new_questionnaires(
            patient_sernum=patient_one.external_id,
            username=user.username,
            purpose_id=4,
        ).count()
        assert new_questionnaires == 1
