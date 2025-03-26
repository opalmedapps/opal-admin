from datetime import timedelta

from django.utils import timezone

import pytest

from opal.caregivers import factories as caregiver_factories
from opal.caregivers.models import RegistrationCode, RegistrationCodeStatus
from opal.core.test_utils import CommandTestMixin
from opal.hospital_settings import factories as hospital_factories

pytestmark = pytest.mark.django_db


class TestRegistrationCodeExpiration(CommandTestMixin):
    """Test class for security questions migration."""

    def test_registration_code_past_allowed_duration(self) -> None:
        """Test `NEW` registration codes that have past expiry duration are set to `EXPIRED`."""
        reg_code1 = caregiver_factories.RegistrationCode(code='code11111115')
        reg_code2 = caregiver_factories.RegistrationCode(code='code11111116')
        institution = hospital_factories.Institution()

        # update creation date to be overdue the expiration date
        longer_expiry = institution.registration_code_valid_period + 10
        reg_code1.created_at = timezone.now() - timedelta(hours=longer_expiry)
        # just expired
        reg_code2.created_at = timezone.now() - timedelta(hours=institution.registration_code_valid_period)
        reg_code1.save()
        reg_code2.save()

        # run management command
        message, error = self._call_command('expire_outdated_registration_codes')
        registration_codes = RegistrationCode.objects.filter(status=RegistrationCodeStatus.EXPIRED)

        # assertions
        assert len(registration_codes) == 2
        assert message == (
            'Number of expired registration codes: 2\n'
        )

    def test_registration_code_within_allowed_duration(self) -> None:
        """Test `NEW` registration codes that have not past expiry duration are not set to `EXPIRED`."""
        reg_code1 = caregiver_factories.RegistrationCode(code='code11111115')
        reg_code2 = caregiver_factories.RegistrationCode(code='code11111116')
        reg_code3 = caregiver_factories.RegistrationCode(code='code11111117')
        institution = hospital_factories.Institution()

        # update creation date to be within the allowed date to remain in `NEW` status
        barely_allowed_duration = timedelta(hours=institution.registration_code_valid_period) - timedelta(seconds=1)
        reg_code1.created_at = timezone.now() - timedelta(hours=10)
        reg_code2.created_at = timezone.now()
        # barely allowed
        reg_code3.created_at = timezone.now() - barely_allowed_duration

        reg_code1.save()
        reg_code2.save()
        reg_code3.save()

        # run management command
        message, error = self._call_command('expire_outdated_registration_codes')
        registration_codes = RegistrationCode.objects.filter(status=RegistrationCodeStatus.EXPIRED)

        # assertions
        assert not registration_codes
        assert message == (
            'Number of expired registration codes: 0\n'
        )

    def test_registration_code_not_new_status(self) -> None:
        """Test not `NEW` registration codes that have past expiry duration are not set to `EXPIRED`."""
        reg_code1 = caregiver_factories.RegistrationCode(code='code11111115', status=RegistrationCodeStatus.REGISTERED)
        reg_code2 = caregiver_factories.RegistrationCode(code='code11111116', status=RegistrationCodeStatus.BLOCKED)
        institution = hospital_factories.Institution()

        # update creation date to be overdue the expiration date
        longer_expiry = institution.registration_code_valid_period + 10
        reg_code1.created_at = timezone.now() - timedelta(hours=longer_expiry)
        reg_code2.created_at = timezone.now() - timedelta(hours=institution.registration_code_valid_period)
        reg_code1.save()
        reg_code2.save()

        # run management command
        message, error = self._call_command('expire_outdated_registration_codes')
        registration_codes = RegistrationCode.objects.filter(status=RegistrationCodeStatus.EXPIRED)

        # assertions
        assert not registration_codes
        assert message == (
            'Number of expired registration codes: 0\n'
        )

    def test_registration_code_combination_status(self) -> None:
        """Test combination of statuses and creation dates."""
        # only reg_code_1 should be set to expired
        reg_code1 = caregiver_factories.RegistrationCode(code='code11111115', status=RegistrationCodeStatus.NEW)
        reg_code2 = caregiver_factories.RegistrationCode(code='code11111116', status=RegistrationCodeStatus.REGISTERED)
        reg_code3 = caregiver_factories.RegistrationCode(code='code11111117', status=RegistrationCodeStatus.NEW)
        institution = hospital_factories.Institution()

        # update created at date to be combination of dates.
        reg_code1.created_at = timezone.now() - timedelta(hours=institution.registration_code_valid_period)
        reg_code2.created_at = timezone.now() - timedelta(hours=institution.registration_code_valid_period)
        reg_code3.created_at = timezone.now()
        reg_code1.save()
        reg_code2.save()
        reg_code3.save()

        # run management command
        message, error = self._call_command('expire_outdated_registration_codes')
        registration_codes = RegistrationCode.objects.filter(status=RegistrationCodeStatus.EXPIRED)

        # assertions
        assert len(registration_codes) == 1
        assert registration_codes[0].code == 'code11111115'
        assert message == (
            'Number of expired registration codes: 1\n'
        )
