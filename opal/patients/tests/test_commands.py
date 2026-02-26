# SPDX-FileCopyrightText: Copyright (C) 2023 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import datetime
from datetime import date
from ftplib import FTP
from itertools import starmap

from django.conf import LazySettings

import pytest
from pytest_mock import MockerFixture, MockType
from structlog.testing import LogCapture

from opal.core.test_utils import CommandTestMixin
from opal.patients import factories as patient_factories
from opal.patients.management.commands.expire_ips_bundles import FTPStoragePlus
from opal.patients.models import Patient, Relationship, RelationshipStatus

pytestmark = pytest.mark.django_db(databases=['default'])


calculate_age_original = Patient.calculate_age


def calculate_age_fixed_date(date_of_birth: date) -> int:
    """
    Mock today's date (reference date) before each test, to ensure results don't vary based on the current date.

    Args:
        date_of_birth: Same input parameter as for Patient.calculate_age.

    Returns:
        The result of Patient.calculate_age called with the input date_of_birth and a fixed reference date.
    """
    return calculate_age_original(date_of_birth=date_of_birth, reference_date=date(2014, 1, 15))


class TestExpireIPSBundlesCommand(CommandTestMixin):
    """Test class for expire_ips_bundles management command."""

    @pytest.fixture(autouse=True)
    def before_each(self, mocker: MockerFixture, settings: LazySettings) -> None:
        """Setup for tests."""
        settings.IPS_STORAGE_BACKEND = 'storages.backends.ftp.FTPStorage'
        settings.FTP_STORAGE_LOCATION = ''

        # Fake the current time for consistent results
        mocker.patch(
            'django.utils.timezone.now', return_value=datetime.datetime(2026, 1, 1, 9, 0, 0, tzinfo=datetime.UTC)
        )

        mocker.patch.object(
            FTPStoragePlus,
            '_decode_location',
            return_value={
                'active': False,
                'host': '',
                'passwd': '',
                'path': '',
                'port': '',
                'secure': False,
                'user': '',
            },
        )
        mocker.patch.object(FTP, 'connect')
        mocker.patch.object(FTP, 'login')
        mocker.patch.object(FTP, 'pwd')

    def _mock_files(self, mocker: MockerFixture, files: dict[str, str]) -> None:
        def format_info_line(file_name: str, date_str: str) -> str:
            return f'type=test;size=0;modify={date_str};UNIX.mode=0000;UNIX.uid=1;UNIX.gid=1;unique=123456789ab; {file_name}'

        basic_date = '20000101000000'

        mocker.patch.object(FTPStoragePlus, 'listdir', return_value=(['.', '..'], ['.htaccess', *files.keys()]))

        info_lines = [
            format_info_line('.', basic_date),
            format_info_line('..', basic_date),
            *list(starmap(format_info_line, files.items())),
            format_info_line('.htaccess', basic_date),
        ]

        mocker.patch.object(FTP, 'retrlines', side_effect=lambda command, append: [append(line) for line in info_lines])

    def _get_logs(self, structlog_output: LogCapture) -> list[str]:
        """Gets log data as a list of strings from a structlog LogCapture fixture."""
        return [entry['event'] for entry in structlog_output.entries]

    def test_ftp_storage_only(self, settings: LazySettings) -> None:
        """Raises a NotImplementedError when using a different storage backend than FTPStorage."""
        settings.IPS_STORAGE_BACKEND = 'django.core.files.storage.FileSystemStorage'

        with pytest.raises(NotImplementedError) as error:
            self._call_command('expire_ips_bundles')

        assert 'The expire_ips_bundles command currently only supports storages.backends.ftp.FTPStorage' in str(
            error.value
        )

    def test_no_bundles(self, mocker: MockerFixture, structlog_output: LogCapture) -> None:
        """No effect when there are no bundles."""
        self._mock_files(mocker, {})

        self._call_command('expire_ips_bundles')

        logs = self._get_logs(structlog_output)
        assert (
            'Checking 0 files to clean up expired IPS bundles (from storage backend: storages.backends.ftp.FTPStorage)'
            in logs
        )

    def test_keep(self, mocker: MockerFixture, structlog_output: LogCapture) -> None:
        """Keep a non-expired bundle."""
        self._mock_files(
            mocker,
            {
                '1304efc5-9961-4249-bfa5-68af94cb0982.ips': '20260101081500',
            },
        )

        self._call_command('expire_ips_bundles')

        logs = self._get_logs(structlog_output)
        assert '0 IPS bundles out of 1 were deleted (0 errors)' in logs

    def test_keep_almost_expired(self, mocker: MockerFixture, structlog_output: LogCapture) -> None:
        """Keep a non-expired bundle that is right about to expire."""
        self._mock_files(
            mocker,
            {
                '1304efc5-9961-4249-bfa5-68af94cb0982.ips': '20260101080001',
            },
        )

        self._call_command('expire_ips_bundles')

        logs = self._get_logs(structlog_output)
        assert '0 IPS bundles out of 1 were deleted (0 errors)' in logs

    def test_keep_now(self, mocker: MockerFixture, structlog_output: LogCapture) -> None:
        """Keep a bundle that was created just now."""
        self._mock_files(
            mocker,
            {
                '1304efc5-9961-4249-bfa5-68af94cb0982.ips': '20260101090000',
            },
        )

        self._call_command('expire_ips_bundles')

        logs = self._get_logs(structlog_output)
        assert '0 IPS bundles out of 1 were deleted (0 errors)' in logs

    def test_keep_future(self, mocker: MockerFixture, structlog_output: LogCapture) -> None:
        """In case of a clock being out of sync, keep a bundle that is marked as last updated in the future."""
        self._mock_files(
            mocker,
            {
                '1304efc5-9961-4249-bfa5-68af94cb0982.ips': '20260101090001',
            },
        )

        self._call_command('expire_ips_bundles')

        logs = self._get_logs(structlog_output)
        assert '0 IPS bundles out of 1 were deleted (0 errors)' in logs

    def test_delete(self, mocker: MockerFixture, structlog_output: LogCapture) -> None:
        """Delete an expired bundle."""
        self._mock_files(
            mocker,
            {
                '1304efc5-9961-4249-bfa5-68af94cb0982.ips': '20260101074500',
            },
        )

        self._call_command('expire_ips_bundles')

        logs = self._get_logs(structlog_output)
        assert '1 IPS bundle out of 1 was deleted (0 errors)' in logs

    def test_delete_just_expired(self, mocker: MockerFixture, structlog_output: LogCapture) -> None:
        """Delete an expired bundle that has just expired."""
        self._mock_files(
            mocker,
            {
                '1304efc5-9961-4249-bfa5-68af94cb0982.ips': '20260101080000',
            },
        )

        self._call_command('expire_ips_bundles')

        logs = self._get_logs(structlog_output)
        assert '1 IPS bundle out of 1 was deleted (0 errors)' in logs

    def test_delete_one_keep_one(self, mocker: MockerFixture, structlog_output: LogCapture) -> None:
        """Delete one expired bundle while leaving the other untouched."""
        self._mock_files(
            mocker,
            {
                '1304efc5-9961-4249-bfa5-68af94cb0982.ips': '20260101080000',
                'bd7c9cdc-1605-4839-9473-8109f488c1fd.ips': '20260101081500',
            },
        )

        self._call_command('expire_ips_bundles')

        logs = self._get_logs(structlog_output)
        assert '1 IPS bundle out of 2 was deleted (0 errors)' in logs

    def test_no_deletions_during_dry_run(self, mocker: MockerFixture, structlog_output: LogCapture) -> None:
        """Don't delete expired bundles when running in dry-run mode."""
        self._mock_files(
            mocker,
            {
                '1304efc5-9961-4249-bfa5-68af94cb0982.ips': '20260101074500',
            },
        )

        # TODO spy on storage_backend.delete (shouldn't run)

        self._call_command('expire_ips_bundles', '--dry-run')

        logs = self._get_logs(structlog_output)
        assert '1 IPS bundle out of 1 would be deleted (0 errors)' in logs


class TestExpireRelationshipsCommand(CommandTestMixin):
    """Test class for expire_relationships management command."""

    @pytest.fixture(autouse=True)
    def before(self, mocker: MockerFixture) -> MockType:
        """Mock `Patient.calculate_age` with a fixed date in place of `date.today()`."""
        return mocker.patch.object(Patient, 'calculate_age', side_effect=calculate_age_fixed_date)

    def test_not_expired(self) -> None:
        """Test patient born shortly before today's date (relationship is not expired)."""
        relationship = self._create_relationship(date(2010, 12, 31))
        self._call_command('expire_relationships')
        relationship.refresh_from_db()
        assert relationship.status == RelationshipStatus.CONFIRMED

    def test_expired(self) -> None:
        """Test patient born long before today's date (relationship is expired)."""
        relationship = self._create_relationship(date(1960, 12, 31))
        self._call_command('expire_relationships')
        relationship.refresh_from_db()
        assert relationship.status == RelationshipStatus.EXPIRED

    def test_born_today(self) -> None:
        """Test patient born today (relationship is not expired)."""
        relationship = self._create_relationship(date(2014, 1, 15))
        self._call_command('expire_relationships')
        relationship.refresh_from_db()
        assert relationship.status == RelationshipStatus.CONFIRMED

    def test_future_birthday(self) -> None:
        """Test patient born in the future (relationship is not expired)."""
        relationship = self._create_relationship(date(2024, 1, 15))
        self._call_command('expire_relationships')
        relationship.refresh_from_db()
        assert relationship.status == RelationshipStatus.CONFIRMED

    def test_birthday_yesterday(self) -> None:
        """Test a patient close to the expiry age, whose birthday was yesterday (relationship has just expired)."""
        relationship = self._create_relationship(date(2000, 1, 14))
        self._call_command('expire_relationships')
        relationship.refresh_from_db()
        assert relationship.status == RelationshipStatus.EXPIRED

    def test_birthday_today(self) -> None:
        """Test a patient close to the expiry age, whose birthday is today (relationship has just expired today)."""
        relationship = self._create_relationship(date(2000, 1, 15))
        self._call_command('expire_relationships')
        relationship.refresh_from_db()
        assert relationship.status == RelationshipStatus.EXPIRED

    def test_birthday_tomorrow(self) -> None:
        """Test a patient close to the expiry age, whose birthday is tomorrow (relationship isn't expired just yet)."""
        relationship = self._create_relationship(date(2000, 1, 16))
        self._call_command('expire_relationships')
        relationship.refresh_from_db()
        assert relationship.status == RelationshipStatus.CONFIRMED

    def test_no_end_age(self) -> None:
        """Test a relationship with no end age, which shouldn't be affected."""
        relationship = self._create_relationship(date(1900, 1, 1), end_age=None)
        self._call_command('expire_relationships')
        relationship.refresh_from_db()
        assert relationship.status == RelationshipStatus.CONFIRMED

    def test_pending_unaffected(self) -> None:
        """Test a relationship with pending status, which shouldn't be affected."""
        relationship = self._create_relationship(date(1900, 1, 1), status=RelationshipStatus.PENDING)
        self._call_command('expire_relationships')
        relationship.refresh_from_db()
        assert relationship.status == RelationshipStatus.PENDING

    def test_denied_unaffected(self) -> None:
        """Test a relationship with denied status, which shouldn't be affected."""
        relationship = self._create_relationship(date(1900, 1, 1), status=RelationshipStatus.DENIED)
        self._call_command('expire_relationships')
        relationship.refresh_from_db()
        assert relationship.status == RelationshipStatus.DENIED

    def test_expired_unaffected(self) -> None:
        """Test a relationship with already expired status, which shouldn't be affected."""
        relationship = self._create_relationship(date(1900, 1, 1), status=RelationshipStatus.EXPIRED)
        self._call_command('expire_relationships')
        relationship.refresh_from_db()
        assert relationship.status == RelationshipStatus.EXPIRED

    def test_revoked_unaffected(self) -> None:
        """Test a relationship with revoked status, which shouldn't be affected."""
        relationship = self._create_relationship(date(1900, 1, 1), status=RelationshipStatus.REVOKED)
        self._call_command('expire_relationships')
        relationship.refresh_from_db()
        assert relationship.status == RelationshipStatus.REVOKED

    def _create_relationship(
        self,
        patient_date_of_birth: date,
        end_age: int | None = 14,
        status: RelationshipStatus = RelationshipStatus.CONFIRMED,
    ) -> Relationship:
        """
        Quickly create a relationship with a patient who has a specific birthday.

        Returns:
            New Relationship with provided parameters.
        """
        return patient_factories.Relationship.create(
            patient=patient_factories.Patient.create(date_of_birth=patient_date_of_birth),
            type=patient_factories.RelationshipType.create(end_age=end_age),
            status=status,
        )
