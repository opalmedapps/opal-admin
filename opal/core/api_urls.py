"""
URL configuration for the project-wide REST API.

Inspired by Two Scoops of Django Section 17.3.
"""
# TODO: determine whether to move API Urls to config module (and support versioning)
from django.conf import settings
from django.urls import path
from django.urls.conf import include

from rest_framework.routers import DefaultRouter, SimpleRouter

from opal.caregivers.api import views as caregivers_views
from opal.caregivers.api.viewsets import SecurityAnswerViewSet, SecurityQuestionViewSet
from opal.core.api import views as core_views
from opal.databank.api.views import CreateDatabankConsentView
from opal.health_data.api import views as data_views
from opal.hospital_settings.api import views as settings_views
from opal.hospital_settings.api import viewsets as settings_viewsets
from opal.legacy.api.views.app_appointments import AppAppointmentsView
from opal.legacy.api.views.app_chart import AppChartView
from opal.legacy.api.views.app_general import AppGeneralView
from opal.legacy.api.views.app_home import AppHomeView
from opal.legacy.api.views.caregiver_permissions import CaregiverPermissionsView
from opal.legacy.api.views.orms_auth import ORMSLoginView, ORMSValidateView
from opal.legacy.api.views.questionnaires_report import QuestionnairesReportView
from opal.patients.api import views as patient_views
from opal.test_results.api.views import CreatePathologyView
from opal.users.api import views as user_views
from opal.users.api import viewsets as user_viewsets

# show APIRootView only in debug mode
# add trailing_slash=False if the trailing slash should not be enforced
# see: https://www.django-rest-framework.org/api-guide/routers/#defaultrouter

if settings.DEBUG:
    router: SimpleRouter = DefaultRouter()
else:
    router = SimpleRouter()


router.register('institutions', settings_viewsets.InstitutionViewSet, basename='institutions')
router.register('sites', settings_viewsets.SiteViewSet, basename='sites')
router.register('security-questions', SecurityQuestionViewSet, basename='security-questions')
router.register('users', user_viewsets.UserViewSet, basename='users')

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
    # validate session endpoint for the ORMS
    path('auth/orms/validate/', ORMSValidateView.as_view(), name='orms-validate'),

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
    path(
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
    path(
        'caregivers/<str:username>/',
        caregivers_views.RetrieveCaregiverView.as_view(),
        name='caregivers-detail',
    ),

    # INSTITUTIONS ENDPOINTS
    path(
        'institution/',
        settings_views.RetrieveInstitutionView.as_view(),
        name='institution-detail',
    ),
    path(
        'institutions/<int:pk>/terms-of-use/',
        settings_viewsets.InstitutionViewSet.as_view({'get': 'retrieve_terms_of_use'}),
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
        'patients/legacy/<int:legacy_id>/caregiver-devices/',
        patient_views.PatientCaregiverDevicesView.as_view(),
        name='patient-caregiver-devices',
    ),
    path(
        'patients/legacy/<int:legacy_id>/',
        patient_views.PatientView.as_view(),
        name='patients-legacy',
    ),
    path(
        'patients/demographic/',
        patient_views.PatientDemographicView.as_view(),
        name='patient-demographic-update',
    ),
    # patients (by new ID) for the health data quantity samples
    path(
        'patients/<uuid:uuid>/health-data/quantity-samples/',
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
    # databank consent instances for patients
    path(
        'patients/<uuid:uuid>/databank/consent/',
        CreateDatabankConsentView.as_view(),
        name='databank-consent-create',
    ),
    path(
        'patients/health-data/quantity-samples/unviewed/',
        data_views.UnviewedQuantitySampleView.as_view(),
        name='unviewed-health-data-patient-list',
    ),
    path(
        'patients/<uuid:uuid>/health-data/quantity-samples/viewed/',
        data_views.MarkQuantitySampleAsViewedView.as_view(),
        name='patient-viewed-health-data-update',
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
        caregivers_views.RegistrationCompletionView.as_view(),
        name='registration-register',
    ),

    # USERS ENDPOINTS
    path(
        'groups/',
        user_views.ListGroupView.as_view(),
        name='groups-list',
    ),
    path(
        'users/caregivers/<str:username>/',
        user_views.UserCaregiverUpdateView.as_view(),
        name='users-caregivers-update',
    ),

    path('', include(router.urls)),
]
