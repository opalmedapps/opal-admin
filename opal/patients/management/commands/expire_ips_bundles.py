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


class FTPStorageWithModifiedTime(FTPStorage):
    """Subclass of FTPStorage that can check a file's last modified datetime."""

    def __init__(self, **settings: Any) -> None:
        """Default constructor."""
        super().__init__(**settings)

    def _datetime_from_string(self, datetime_string: str) -> datetime.datetime:
        # The datetime representation is in UTC
        return datetime.datetime.strptime(datetime_string, '%Y%m%d%H%M%S').replace(tzinfo=datetime.UTC)

    # Function inspired by `_get_dir_details` of the FTPStorage class
    def _get_dir_last_modified_details(self, file_name: str) -> str:
        # Connection must be open!
        try:
            # Get metadata for the requested file
            # For more about MLST, see: https://datatracker.ietf.org/doc/html/rfc3659#section-7
            response = self._connection.sendcmd(f'MLST {file_name}')

            # Example response (note that the middle line starts with one space; this is part of the format):
            # 250-Begin
            #  type=file;size=256;modify=20251028155020;UNIX.mode=0644;UNIX.uid=1000;UNIX.gid=1000;unique=123456789ab; file-name.ext
            # 250 End.

            # Make sure the modify attribute is present
            if 'modify=' not in response:
                raise FTPStorageException(
                    'Output of MLST in this directory is not in the expected format, or does not contain a "modify" attribute'
                )

            # Extract the timestamp between 'modify=' and the next ';'
            modify = response.split('modify=')[1].split(';')[0]

        except ftplib.all_errors as error:
            raise FTPStorageException(f'Error getting directory listing for file {file_name}') from error

        else:
            return modify

    # Implements `get_modified_time` of the Storage class (from FTPStorage(BaseStorage(Storage)))
    # Function inspired by `listdir` of the FTPStorage class
    def get_modified_time(self, name: str) -> datetime.datetime:
        """
        Return the last modified time (as a datetime) of the file specified by name.

        Args:
            name: The name of the file to check.

        Returns:
            The last modified datetime for the given file.
        """
        self._start_connection()
        last_modified_string = self._get_dir_last_modified_details(name)
        return self._datetime_from_string(last_modified_string)


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

        storage_backend = FTPStorageWithModifiedTime()

        file_list = storage_backend.listdir('../bundles')[1]
        file_list = [name for name in file_list if re.match(r'^.+\.ips$', name)]

        LOGGER.info(
            'Checking %s %s to clean up expired IPS bundles (from storage backend: %s)',
            len(file_list),
            'file' if len(file_list) == 1 else 'files',
            settings.IPS_STORAGE_BACKEND,
        )

        for file_name in file_list:
            # Calculate the bundle's validity based on the time since it was last modified
            # Note that last modified is used instead of creation time (not available); it offers the same result, since bundle files aren't updated
            try:
                last_modified = storage_backend.get_modified_time(file_name)
            except FTPStorageException:
                LOGGER.exception(
                    'ERROR - Bundle "%s" last modified information failed to be retrieved from the server',
                    file_name,
                )
                num_errors += 1
                continue
            except ValueError:
                LOGGER.exception(
                    'ERROR - Bundle "%s" last modified date is not in the expected format',
                    file_name,
                )
                num_errors += 1
                continue

            now = timezone.now()  # UTC
            delta = now - last_modified
            expired = delta >= datetime.timedelta(hours=IPS_EXPIRY_HOURS)

            LOGGER.debug(
                '%s - Bundle "%s" last modified %s ago (%s UTC)',
                'DELETE' if expired else 'KEEP',
                file_name,
                delta,
                last_modified,
            )

            if expired:
                try:
                    if not dry_run:
                        storage_backend.delete(file_name)

                    num_deleted += 1
                # Bare except: catch any possible error here in order to properly log it and continue
                except:  # noqa: E722
                    # Example of a one-off error: PermissionError: [WinError 10013] An attempt was made to access a socket in a way forbidden by its access permissions
                    LOGGER.exception('ERROR - Failed to delete IPS bundle "%s"', file_name)
                    num_errors += 1

        LOGGER.info(
            '%s IPS %s out of %s %s deleted (%s %s)',
            num_deleted,
            'bundle' if num_deleted == 1 else 'bundles',
            len(file_list),
            'would be' if dry_run else 'was' if num_deleted == 1 else 'were',
            num_errors,
            'error' if num_errors == 1 else 'errors',
        )
