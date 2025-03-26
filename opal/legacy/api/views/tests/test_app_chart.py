from django.urls import reverse

import pytest
from rest_framework.response import Response
from rest_framework.test import APIClient

from opal.legacy import factories, models
from opal.legacy_questionnaires import factories as questionnaires_factories
from opal.legacy_questionnaires import models as questionnaires_models
from opal.patients import factories as patient_factories
from opal.patients import models as patient_models

pytestmark = pytest.mark.django_db(databases=['default', 'legacy', 'questionnaire'])


class TestAppChartView:
    """Class wrapper for chart page request tests."""

    def test_get_chart_data_request(self, admin_api_client: APIClient) -> None:
        """Test if the response has the required keys."""
        response = self._call_chart_data_request(admin_api_client, self.patient.patientsernum, self.user.username)
        assert 'unread_appointment_count' in response.data
        assert 'unread_lab_result_count' in response.data
        assert 'unread_document_count' in response.data
        assert 'unread_txteammessage_count' in response.data
        assert 'unread_educationalmaterial_count' in response.data
        assert 'unread_questionnaire_count' in response.data
        assert 'unread_research_reference_count' in response.data
        assert 'unread_research_questionnaire_count' in response.data
        assert 'unread_consent_questionnaire_count' in response.data

    def test_get_unread_appointment_count(self, admin_api_client: APIClient) -> None:
        """Test if function returns number of unread appointments."""
        # Insert appointment with different state, status and read status.
        alias_expression = factories.LegacyAliasExpressionFactory()
        # List of all possible appointment status
        possible_appt_status = [
            'Open',
            'Deleted',
            'In Progress',
            'Cancelled',
            'Completed',
            'Manually Completed',
            'Cancelled - Patient No-Show',
        ]
        for status in possible_appt_status:
            factories.LegacyAppointmentFactory(
                patientsernum=self.patient,
                aliasexpressionsernum=alias_expression,
                status=status,
                state='Active',
            )
            factories.LegacyAppointmentFactory(
                patientsernum=self.patient,
                aliasexpressionsernum=alias_expression,
                status=status,
                state='Deleted',
            )
            factories.LegacyAppointmentFactory(
                patientsernum=self.patient,
                aliasexpressionsernum=alias_expression,
                status=status,
                state='Active',
                readby=self.user.username,
            )

        # Direct function call
        appointments = models.LegacyAppointment.objects.get_unread_queryset(
            self.patient.patientsernum,
            self.user.username,
        ).count()
        assert appointments == 14

        # API results
        response = self._call_chart_data_request(admin_api_client, self.patient.patientsernum, self.user.username)
        assert response.data['unread_appointment_count'] == 14

    def test_get_unread_labs_count(self, admin_api_client: APIClient) -> None:
        """Test whether the right number of unread lab results is returned."""
        factories.LegacyPatientTestResultFactory(patient_ser_num=self.patient)
        factories.LegacyPatientTestResultFactory(patient_ser_num=self.patient)
        factories.LegacyPatientTestResultFactory(patient_ser_num=self.patient, read_by=self.user.username)

        # Direct function call
        unread_labs = models.LegacyPatientTestResult.objects.get_unread_queryset(
            self.patient.patientsernum,
            self.user.username,
        ).count()
        assert unread_labs == 2

        # API results
        response = self._call_chart_data_request(admin_api_client, self.patient.patientsernum, self.user.username)
        assert response.data['unread_lab_result_count'] == 2

    def test_get_unread_document_count(self, admin_api_client: APIClient) -> None:
        """Test whether the right number of unread documents is returned."""
        factories.LegacyDocumentFactory(patientsernum=self.patient)
        factories.LegacyDocumentFactory(patientsernum=self.patient)
        factories.LegacyDocumentFactory(patientsernum=self.patient, readby=self.user.username)

        # Direct function call
        unread_documents = models.LegacyDocument.objects.get_unread_queryset(
            self.patient.patientsernum,
            self.user.username,
        ).count()
        assert unread_documents == 2

        # API results
        response = self._call_chart_data_request(admin_api_client, self.patient.patientsernum, self.user.username)
        assert response.data['unread_document_count'] == 2

    def test_get_unread_txteammessage_count(self, admin_api_client: APIClient) -> None:
        """Test if function returns number of unread txteammessages."""
        factories.LegacyTxTeamMessageFactory(patientsernum=self.patient)
        factories.LegacyTxTeamMessageFactory(patientsernum=self.patient)
        factories.LegacyTxTeamMessageFactory(patientsernum=self.patient, readby=self.user.username)

        # Direct function call
        txteammessages = models.LegacyTxTeamMessage.objects.get_unread_queryset(
            self.patient.patientsernum,
            self.user.username,
        ).count()
        assert txteammessages == 2

        # API results
        response = self._call_chart_data_request(admin_api_client, self.patient.patientsernum, self.user.username)
        assert response.data['unread_txteammessage_count'] == 2

    def test_get_unread_clinical_edumaterial_count(self, admin_api_client: APIClient) -> None:
        """Test if function returns the right number of unread clinical educational materials."""
        self._get_new_clinical_material(patient_ser_num=self.patient)
        self._get_new_clinical_material(patient_ser_num=self.patient)
        self._get_new_clinical_material(patient_ser_num=self.patient, read_by=self.user.username)
        self._get_new_research_material(patient_ser_num=self.patient)
        self._get_new_research_material(patient_ser_num=self.patient, read_by=self.user.username)

        # Direct function call
        edumaterials = models.LegacyEducationalMaterial.objects.get_unread_queryset(
            self.patient.patientsernum,
            self.user.username,
        ).filter(
            educationalmaterialcontrolsernum__educationalmaterialcategoryid__title_en='Clinical',
        ).count()
        assert edumaterials == 2

        # API results
        response = self._call_chart_data_request(admin_api_client, self.patient.patientsernum, self.user.username)
        assert response.data['unread_educationalmaterial_count'] == 2

    def test_get_unread_research_edumaterial_count(self, admin_api_client: APIClient) -> None:
        """Test if function returns the right number of unread research educational materials."""
        self._get_new_research_material(patient_ser_num=self.patient)
        self._get_new_research_material(patient_ser_num=self.patient)
        self._get_new_research_material(patient_ser_num=self.patient, read_by=self.user.username)
        self._get_new_clinical_material(patient_ser_num=self.patient)
        self._get_new_clinical_material(patient_ser_num=self.patient, read_by=self.user.username)

        # Direct function call
        edumaterials = models.LegacyEducationalMaterial.objects.get_unread_queryset(
            self.patient.patientsernum,
            self.user.username,
        ).filter(
            educationalmaterialcontrolsernum__educationalmaterialcategoryid__title_en='Research',
        ).count()
        assert edumaterials == 2

        # API results
        response = self._call_chart_data_request(admin_api_client, self.patient.patientsernum, self.user.username)
        assert response.data['unread_research_reference_count'] == 2

    @pytest.mark.parametrize(
        'clear_questionnairedb',
        [['answerQuestionnaire', 'questionnaire', 'purpose']],
        indirect=True,
    )
    def test_get_unread_questionnaire_count(self, clear_questionnairedb: None, admin_api_client: APIClient) -> None:
        """Test if function returns number of new clinical questionnaires."""
        respondent = questionnaires_factories.LegacyRespondentFactory(title__content='Caregiver', title__language_id=2)
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
        patient_one = questionnaires_factories.LegacyPatientFactory(external_id=self.patient.patientsernum)
        patient_two = questionnaires_factories.LegacyPatientFactory(external_id=52)

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

        # Direct function calls
        new_questionnaires = questionnaires_models.LegacyQuestionnaire.objects.new_questionnaires(
            patient_sernum=patient_one.external_id,
            username=self.user.username,
            purpose_id=1,
        ).count()
        assert new_questionnaires == 1
        new_questionnaires = questionnaires_models.LegacyQuestionnaire.objects.new_questionnaires(
            patient_sernum=patient_one.external_id,
            username=self.user.username,
            purpose_id=2,
        ).count()
        assert new_questionnaires == 1
        new_questionnaires = questionnaires_models.LegacyQuestionnaire.objects.new_questionnaires(
            patient_sernum=patient_one.external_id,
            username=self.user.username,
            purpose_id=4,
        ).count()
        assert new_questionnaires == 1

        # API results
        response = self._call_chart_data_request(admin_api_client, patient_one.external_id, self.user.username)
        assert response.data['unread_questionnaire_count'] == 1
        assert response.data['unread_research_questionnaire_count'] == 1
        assert response.data['unread_consent_questionnaire_count'] == 1

    @pytest.fixture(autouse=True)
    def _before_each(self) -> None:
        """Create patient and user objects for each test."""
        relationship = patient_factories.Relationship(
            status=patient_models.RelationshipStatus.CONFIRMED,
            type__can_answer_questionnaire=True,
        )
        self.patient = factories.LegacyPatientFactory(patientsernum=relationship.patient.legacy_id)
        self.user = relationship.caregiver.user

    def _get_new_research_material(self, patient_ser_num: int, read_by: str = '[]') -> models.LegacyEducationalMaterial:
        """Create and return a new research material."""
        return factories.LegacyEducationalMaterialFactory(
            educationalmaterialcontrolsernum__educationalmaterialcategoryid__title_en='Research',
            patientsernum=patient_ser_num,
            readby=read_by,
        )

    def _get_new_clinical_material(self, patient_ser_num: int, read_by: str = '[]') -> models.LegacyEducationalMaterial:
        """Create and return a new clinical educational material."""
        return factories.LegacyEducationalMaterialFactory(
            educationalmaterialcontrolsernum__educationalmaterialcategoryid__title_en='Clinical',
            patientsernum=patient_ser_num,
            readby=read_by,
        )

    def _call_chart_data_request(
        self,
        admin_api_client: APIClient,
        patient_legacy_id: int,
        username: str,
    ) -> Response:
        """Call the AppChartView API."""
        admin_api_client.credentials(HTTP_APPUSERID=username)
        return admin_api_client.get(reverse('api:app-chart', kwargs={'legacy_id': patient_legacy_id}))
