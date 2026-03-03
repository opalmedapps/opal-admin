# SPDX-FileCopyrightText: Copyright (C) 2025 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Command for cleaning up expired IPS bundles."""

import datetime
import ftplib
import re
from typing import Any

from django.conf import settings
from django.core.management.base import BaseCommand, CommandParser
from django.utils import timezone

import structlog
from storages.backends.ftp import FTPStorage, FTPStorageException

LOGGER = structlog.get_logger()

# The number of hours after which IPS bundles will be deleted
# If this value is changed, please also update the instructions in the app (ips-preview-share.html)
# The value of 1 hour was chosen as the easiest way to comply with the SHL specification: https://docs.smarthealthit.org/smart-health-links/spec/#fileslocation-links
IPS_EXPIRY_HOURS = 1


class FTPStoragePlus(FTPStorage):
    """Subclass of FTPStorage that can check a file's last modified datetime."""

    def __init__(self, **settings: Any) -> None:
        """Default constructor."""
        super().__init__(**settings)

    def _datetime_from_string(self, datetime_string: str) -> datetime.datetime:
        # The datetime representation is in UTC
        return datetime.datetime.strptime(datetime_string, '%Y%m%d%H%M%S').replace(tzinfo=datetime.UTC)

    # Function modeled on `_get_dir_details` of the FTPStorage class
    def _get_dir_last_modified_details(self) -> dict[str, str]:
        # Connection must be open!
        try:
            # Get metadata from the files in the current directory
            lines: list[str] = []
            self._connection.retrlines('MLSD', lines.append)
            entries = {}

            for line in lines:
                # Example line: type=file;size=256;modify=20251028155020;UNIX.mode=0644;UNIX.uid=1000;UNIX.gid=1000;unique=123456789ab; file-name.ext
                # Break the line around 'modify=', then parse the timestamp and file name out of the string that comes after it
                parts = line.split('modify=')[1].split(';')
                modify = parts[0]
                filename = parts[-1].strip()

                entries[filename] = modify

        except IndexError as error:
            raise FTPStorageException('Output of MLSD in this directory is not in the expected format') from error

        except ftplib.all_errors as error:
            raise FTPStorageException('Error getting directory listing') from error

        else:
            return entries

    # Implements `get_modified_time` of the Storage class (from FTPStorage(BaseStorage(Storage)))
    # Function modeled on `listdir` of the FTPStorage class
    def get_modified_time(self, name: str) -> datetime.datetime:
        """
        Return the last modified time (as a datetime) of the file specified by name.

        Args:
            name: The name of the file to check.

        Returns:
            The last modified datetime for the given file.

        Raises:
            FileNotFoundError: if information about the specified file cannot be found on the server.
        """
        self._start_connection()

        entries = self._get_dir_last_modified_details()

        if name in entries:
            return self._datetime_from_string(entries[name])
        raise FileNotFoundError()


class Command(BaseCommand):
    """Command for deleting IPS bundles after a certain amount of time has elapsed since their creation."""

    help = 'Delete expired IPS bundles from their storage location.'

    def add_arguments(self, parser: CommandParser) -> None:
        """
        Add arguments to the command.

        Args:
            parser: the command parser to add arguments to
        """
        parser.add_argument(
            '--dry-run',
            action='store_true',
            default=False,
            help='Runs the command with printouts of all planned actions, without actually deleting any files.',
        )

    def handle(self, *args: Any, **options: Any) -> None:
        """
        Handle deletion of expired IPS bundles.

        Args:
            args: non-keyword input arguments.
            options: additional keyword input arguments.
        """
        dry_run: bool = options['dry_run']

        num_deleted = 0
        num_errors = 0

        if settings.IPS_STORAGE_BACKEND != 'storages.backends.ftp.FTPStorage':
            raise NotImplementedError(
                f'The expire_ips_bundles command currently only supports storages.backends.ftp.FTPStorage (see IPS_STORAGE_BACKEND); current value: {settings.IPS_STORAGE_BACKEND}'
            )

        if dry_run:
            LOGGER.info('Running command in dry-run mode; no files will be deleted')

        storage_backend = FTPStoragePlus()

        file_list = storage_backend.listdir('../bundles')[1]
        file_list = [name for name in file_list if re.match(r'^.+\.ips$', name)]

        LOGGER.info(
            f'Checking {len(file_list)} {"file" if len(file_list) == 1 else "files"} to clean up expired IPS bundles (from storage backend: {settings.IPS_STORAGE_BACKEND})',
        )

        for file_name in file_list:
            # Calculate the bundle's validity based on the time since it was last modified
            # Note that last modified is used instead of creation time (not available); it offers the same result, since bundle files aren't updated
            try:
                last_modified = storage_backend.get_modified_time(file_name)
            except (FTPStorageException, FileNotFoundError):
                LOGGER.exception(
                    f'ERROR - Bundle "{file_name}" last modified information failed to be retrieved from the server'
                )
                num_errors += 1
                continue
            except ValueError:
                LOGGER.exception(f'ERROR - Bundle "{file_name}" last modified date is not in the expected format')
                num_errors += 1
                continue

            now = timezone.now()  # UTC
            delta = now - last_modified
            expired = delta >= datetime.timedelta(hours=IPS_EXPIRY_HOURS)

            LOGGER.debug(
                f'{"DELETE" if expired else "KEEP"} - Bundle "{file_name}" last modified {delta} ago ({last_modified} UTC)',
            )

            if expired:
                try:
                    if not dry_run:
                        storage_backend.delete(file_name)

                    num_deleted += 1
                # Bare except: catch any possible error here in order to properly log it and continue
                except:  # noqa: E722
                    # Example of a one-off error: PermissionError: [WinError 10013] An attempt was made to access a socket in a way forbidden by its access permissions
                    LOGGER.exception(f'ERROR - Failed to delete IPS bundle "{file_name}"')
                    num_errors += 1

        LOGGER.info(
            f'{num_deleted} IPS {"bundle" if num_deleted == 1 else "bundles"} out of {len(file_list)} {"would be" if dry_run else "was" if num_deleted == 1 else "were"} deleted ({num_errors} {"error" if num_errors == 1 else "errors"})',
        )
