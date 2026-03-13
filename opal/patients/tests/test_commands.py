# SPDX-FileCopyrightText: Copyright (C) 2023 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

import datetime
from datetime import date
from ftplib import FTP, error_perm
from typing import Any

from django.conf import LazySettings
from django.utils.timezone import make_naive

import pytest
from pytest_mock import MockerFixture, MockType
from storages.backends.ftp import FTPStorage
from structlog.testing import LogCapture

from opal.core.test_utils import CommandTestMixin
from opal.patients import factories as patient_factories
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

        # Fake the current time and date for consistent results
        fake_datetime = datetime.datetime(2026, 1, 1, 9, 0, 0, tzinfo=datetime.UTC)
        if not settings.USE_TZ:
            fake_datetime = make_naive(fake_datetime)
        mocker.patch('django.utils.timezone.now', return_value=fake_datetime)

        mocker.patch.object(
            FTPStorage,
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
        mocker.patch.object(FTP, 'quit')
        mocker.patch.object(FTPStorage, 'delete')

    def _mock_files(self, mocker: MockerFixture, file_timestamps: dict[str, str], **kwargs: Any) -> None:
        # Can be used to test what happens if the modify attribute is missing
        hide_modify = kwargs.get('hide_modify')

        # Metadata info line for a given file
        def format_info_line(file_name: str, date_str: str) -> str:
            modify_part = '' if hide_modify else f'modify={date_str}'
            return (
                # This line starts with one space on purpose; this is part of the format
                f' type=test;size=0;{modify_part};UNIX.mode=0000;UNIX.uid=1;UNIX.gid=1;unique=123456789ab; {file_name}'
            )

        # The complete response given when requesting a file's metadata
        def info_lines(file_name: str) -> str:
            return '\n'.join([
                '250-Begin',
                format_info_line(file_name, file_timestamps[file_name]) if file_name in file_timestamps else ' ',
                '250 End.',
            ])

        # Function used to mock a file metadata command, which extracts the file name from the command and returns the metadata
        def mock_sendcmd(command: str) -> str:
            if 'MLST ' in command:
                file_name = command.split('MLST ')[1]

                if file_name in file_timestamps:
                    return info_lines(file_name)
                raise error_perm("550 Can't check for file existence")

            # Treat any other commands as successful
            return '200'

        # Mock the directory listing
        all_files = ['.htaccess', *file_timestamps.keys()]
        mocker.patch.object(
            FTPStorage,
            '_get_dir_details',
            return_value=((
                {'.': 0, '..': 0},
                {**dict.fromkeys(all_files, 0)},
            )),
        )

        # Mock the command to request a file's metadata
        mocker.patch.object(FTP, 'sendcmd', side_effect=mock_sendcmd)

    def _get_logs(self, structlog_output: LogCapture) -> list[str]:
        """Gets log data as a list of strings from a structlog LogCapture fixture."""
        return [entry['event'] for entry in structlog_output.entries]

    def test_non_ftp_storage(self, settings: LazySettings) -> None:
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
        delete_spy = mocker.spy(FTPStorage, 'delete')

        self._call_command('expire_ips_bundles')

        assert delete_spy.call_count == 0
        logs = self._get_logs(structlog_output)
        assert (
            'Checking 0 files to clean up expired IPS bundles (from storage backend: storages.backends.ftp.FTPStorage)'
            in logs
        )

    @pytest.mark.parametrize(
        'timestamp',
        [
            '20260101081500',  # Average bundle, last modified 45m ago
            '20260101080001',  # Bundle just about to expire, last updated 59m and 59s ago
            '20260101090000',  # Bundle created just now, last modified 0s ago
            '20260101090001',  # Bundle that was modified in the future (in case of clock issues), last modified -1s ago
        ],
    )
    def test_keep(self, mocker: MockerFixture, structlog_output: LogCapture, timestamp: str) -> None:
        """Keep a non-expired bundle."""
        self._mock_files(
            mocker,
            {
                '1304efc5-9961-4249-bfa5-68af94cb0982.ips': timestamp,
            },
        )
        delete_spy = mocker.spy(FTPStorage, 'delete')

        self._call_command('expire_ips_bundles')

        assert delete_spy.call_count == 0
        logs = self._get_logs(structlog_output)
        assert '0 IPS bundles out of 1 were deleted (0 errors)' in logs

    @pytest.mark.parametrize(
        'timestamp',
        [
            '20260101074500',  # Average bundle, last modified 1h 15m ago
            '20260101080000',  # Bundle just expired, last updated 1h ago
        ],
    )
    def test_delete(self, mocker: MockerFixture, structlog_output: LogCapture, timestamp: str) -> None:
        """Delete an expired bundle."""
        self._mock_files(
            mocker,
            {
                '1304efc5-9961-4249-bfa5-68af94cb0982.ips': timestamp,
            },
        )
        delete_spy = mocker.spy(FTPStorage, 'delete')

        self._call_command('expire_ips_bundles')

        assert delete_spy.call_count == 1
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
        delete_spy = mocker.spy(FTPStorage, 'delete')

        self._call_command('expire_ips_bundles')

        assert delete_spy.call_count == 1
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
        delete_spy = mocker.spy(FTPStorage, 'delete')

        self._call_command('expire_ips_bundles', '--dry-run')

        assert delete_spy.call_count == 0
        logs = self._get_logs(structlog_output)
        assert '1 IPS bundle out of 1 would be deleted (0 errors)' in logs

    def test_file_not_found(self, mocker: MockerFixture, structlog_output: LogCapture) -> None:
        """Log an error and continue if information about a file is missing from the server."""
        self._mock_files(
            mocker,
            {
                '1304efc5-9961-4249-bfa5-68af94cb0982.ips': '20260101074500',
            },
        )
        # Overwrite the directory listing with an additional file that doesn't have metadata like a last modified time
        mocker.patch.object(
            FTPStorage,
            'listdir',
            return_value=(
                ['.', '..'],
                ['.htaccess', 'bd7c9cdc-1605-4839-9473-8109f488c1fd.ips', '1304efc5-9961-4249-bfa5-68af94cb0982.ips'],
            ),
        )

        self._call_command('expire_ips_bundles')

        logs = self._get_logs(structlog_output)
        assert (
            'ERROR - Bundle "bd7c9cdc-1605-4839-9473-8109f488c1fd.ips" last modified information failed to be retrieved from the server'
            in logs
        )
        assert '1 IPS bundle out of 2 was deleted (1 error)' in logs

    def test_file_delete_error(self, mocker: MockerFixture, structlog_output: LogCapture) -> None:
        """Log an error and continue if a file fails to be deleted."""
        self._mock_files(
            mocker,
            {
                '1304efc5-9961-4249-bfa5-68af94cb0982.ips': '20260101070000',
                'bd7c9cdc-1605-4839-9473-8109f488c1fd.ips': '20260101070000',
            },
        )
        # Throw a PermissionError only for the first file, do nothing for the second
        mocker.patch.object(FTPStorage, 'delete', side_effect=[PermissionError, None])

        self._call_command('expire_ips_bundles')

        logs = self._get_logs(structlog_output)
        assert 'ERROR - Failed to delete IPS bundle "1304efc5-9961-4249-bfa5-68af94cb0982.ips"' in logs
        assert '1 IPS bundle out of 2 was deleted (1 error)' in logs

    def test_file_date_format_error(self, mocker: MockerFixture, structlog_output: LogCapture) -> None:
        """Log an error and continue if a file's metadata for last modified time isn't in the expected format."""
        self._mock_files(
            mocker,
            {
                '1304efc5-9961-4249-bfa5-68af94cb0982.ips': '20260101',
                'bd7c9cdc-1605-4839-9473-8109f488c1fd.ips': '20260101070000',
            },
        )

        self._call_command('expire_ips_bundles')

        logs = self._get_logs(structlog_output)
        assert (
            'ERROR - Bundle "1304efc5-9961-4249-bfa5-68af94cb0982.ips" last modified information failed to be retrieved from the server'
            in logs
        )
        assert '1 IPS bundle out of 2 was deleted (1 error)' in logs

    def test_modify_missing_error(self, mocker: MockerFixture, structlog_output: LogCapture) -> None:
        """Log an error if the 'modify' metadata attribute is missing."""
        self._mock_files(
            mocker,
            {
                '1304efc5-9961-4249-bfa5-68af94cb0982.ips': '20260101070000',
            },
            hide_modify=True,
        )

        self._call_command('expire_ips_bundles')

        logs = self._get_logs(structlog_output)
        assert (
            'ERROR - Bundle "1304efc5-9961-4249-bfa5-68af94cb0982.ips" last modified information failed to be retrieved from the server'
            in logs
        )
        assert '0 IPS bundles out of 1 were deleted (1 error)' in logs

    def test_24_hour_time(self, mocker: MockerFixture, structlog_output: LogCapture) -> None:
        """Correctly parse times in the 24-hour system."""
        self._mock_files(
            mocker,
            {
                '1304efc5-9961-4249-bfa5-68af94cb0982.ips': '20251231230000',
            },
        )

        self._call_command('expire_ips_bundles')

        logs = self._get_logs(structlog_output)
        assert (
            'DELETE - Bundle "1304efc5-9961-4249-bfa5-68af94cb0982.ips" last modified 10:00:00 ago (2025-12-31 23:00:00+00:00 UTC)'
            in logs
        )


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
