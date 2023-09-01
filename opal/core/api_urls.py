"""
URL configuration for the project-wide REST API.

Inspired by Two Scoops of Django Section 17.3.
"""
from django.conf import settings
from django.urls import path
from django.urls.conf import include

from rest_framework.routers import DefaultRouter, SimpleRouter

from opal.caregivers.api import views as caregivers_views
from opal.caregivers.api.viewsets import SecurityAnswerViewSet, SecurityQuestionViewSet
from opal.core.api import views as core_views
from opal.health_data.api import views as data_views
from opal.hospital_settings.api import viewsets as settings_views
from opal.legacy.api.views.app_appointments import AppAppointmentsView
from opal.legacy.api.views.app_chart import AppChartView
from opal.legacy.api.views.app_general import AppGeneralView
from opal.legacy.api.views.app_home import AppHomeView
from opal.legacy.api.views.caregiver_permissions import CaregiverPermissionsView
from opal.legacy.api.views.orms_auth import ORMSLoginView
from opal.legacy.api.views.questionnaires_report import QuestionnairesReportView
from opal.patients.api import views as patient_views
from opal.test_results.api.views import CreatePathologyView

# show APIRootView only in debug mode
# add trailing_slash=False if the trailing slash should not be enforced
# see: https://www.django-rest-framework.org/api-guide/routers/#defaultrouter
if settings.DEBUG:
    router: SimpleRouter = DefaultRouter()
else:
    router = SimpleRouter()


router.register('institutions', settings_views.InstitutionViewSet, basename='institutions')
router.register('sites', settings_views.SiteViewSet, basename='sites')
router.register('security-questions', SecurityQuestionViewSet, basename='security-questions')


app_name = 'core'

urlpatterns = [
    # APP ENDPOINTS
    path('app/chart/<int:legacy_id>/', AppChartView.as_view(), name='app-chart'),
    path('app/home/', AppHomeView.as_view(), name='app-home'),
    path('app/appointments/', AppAppointmentsView.as_view(), name='app-appointments'),
    path('app/general/', AppGeneralView.as_view(), name='app-general'),

    # AUTH ENDPOINTS
    path('auth/', include('dj_rest_auth.urls')),
    # authentication endpoint for the ORMS
    path('auth/orms/login/', ORMSLoginView.as_view(), name='orms-login'),

    # CAREGIVERS ENDPOINTS
    path(
        'caregivers/patients/',
        caregivers_views.GetCaregiverPatientsList.as_view(),
        name='caregivers-patient-list',
    ),
    path(
        'caregivers/profile/',
        caregivers_views.CaregiverProfileView.as_view(),
        name='caregivers-profile',
    ),
    path(  # Only use this endpoint between the Listener and the backend
        'caregivers/<str:username>/security-questions/',
        SecurityAnswerViewSet.as_view({'get': 'list'}),
        name='caregivers-securityquestions-list',
    ),
    path(
        'caregivers/<str:username>/security-questions/<int:pk>/',
        SecurityAnswerViewSet.as_view({'get': 'retrieve', 'put': 'update'}),
        name='caregivers-securityquestions-detail',
    ),
    path(
        # Security: this endpoint exposes security answers, and should only be called by the listener
        # TODO: Use permissions (e.g. group permissions) to restrict access of this endpoint only to the listener
        'caregivers/<str:username>/security-questions/random/',
        SecurityAnswerViewSet.as_view({'get': 'random'}),
        name='caregivers-securityquestions-random',
    ),
    path(
        'caregivers/<str:username>/security-questions/<int:pk>/verify/',
        SecurityAnswerViewSet.as_view({'post': 'verify_answer'}),
        name='caregivers-securityquestions-verify',
    ),
    path(
        'caregivers/devices/<str:device_id>/',
        caregivers_views.UpdateDeviceView.as_view(),
        name='devices-update-or-create',
    ),

    # INSTITUTIONS ENDPOINTS
    path(
        'institutions/<int:pk>/terms-of-use/',
        settings_views.InstitutionViewSet.as_view({'get': 'retrieve_terms_of_use'}),
        name='institutions-terms-of-use',
    ),

    # LANGUAGES ENDPOINTS
    path('languages/', core_views.LanguagesView.as_view(), name='languages'),

    # PATIENTS ENDPOINTS
    path(
        'patients/legacy/<int:legacy_id>/check-permissions/',
        CaregiverPermissionsView.as_view(),
        name='caregiver-permissions',
    ),
    path(
        'patients/legacy/<int:legacy_id>/caregivers/',
        patient_views.CaregiverRelationshipView.as_view(),
        name='caregivers-list',
    ),
    path(
        'patients/legacy/<int:legacy_id>/',
        patient_views.PatientCaregiversView.as_view(),
        name='patient-caregivers',
    ),
    path(
        'patients/demographic/',
        patient_views.PatientDemographicView.as_view(),
        name='patient-demographic-update',
    ),
    # patients (by new ID) for the health data quantity samples
    path(
        'patients/<int:patient_id>/health-data/quantity-samples/',
        data_views.CreateQuantitySampleView.as_view(),
        name='patients-data-quantity-create',
    ),
    path(
        'patients/exists',
        patient_views.PatientExistsView.as_view(),
        name='patient-exists',
    ),
    path(
        'patients/<uuid:uuid>/pathology-reports/',
        CreatePathologyView.as_view(),
        name='patient-pathology-create',
    ),


    # QUESTIONNAIRES ENDPOINTS
    path(
        'questionnaires/reviewed/',
        QuestionnairesReportView.as_view(),
        name='questionnaires-reviewed',
    ),

    # REGISTRATION ENDPOINTS
    path(
        'registration/by-hash/<str:hash>/',
        caregivers_views.GetRegistrationEncryptionInfoView.as_view(),
        name='registration-by-hash',
    ),
    path(
        'registration/<str:code>/',
        patient_views.RetrieveRegistrationDetailsView.as_view(),
        name='registration-code',
    ),
    path(
        'registration/<str:code>/verify-email/',
        caregivers_views.VerifyEmailView.as_view(),
        name='verify-email',
    ),
    path(
        'registration/<str:code>/verify-email-code/',
        caregivers_views.VerifyEmailCodeView.as_view(),
        name='verify-email-code',
    ),
    path(
        'registration/<str:code>/register/',
        patient_views.RegistrationCompletionView.as_view(),
        name='registration-register',
    ),

    path('', include(router.urls)),
]
