# SPDX-FileCopyrightText: Copyright (C) 2025 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Command for cleaning up expired IPS bundles."""

import datetime
import re
from typing import Any

from django.conf import settings
from django.core.management.base import BaseCommand, CommandParser

import structlog
from storages.backends.ftp import FTPStorage

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

    def _datetime_from_time_string(self, time_string: str) -> datetime.datetime:
        # Convert the time representation to ISO format, in UTC
        time_string_iso = time_string[:8] + 'T' + time_string[8:] + 'Z'

        return datetime.datetime.fromisoformat(time_string_iso)

    # Function modeled on `_get_dir_details` of the FTPStorage class
    def _get_dir_last_modified_details(self) -> dict[str, str]:
        # Get metadata from the files in the current directory
        lines: list[str] = []
        self._connection.retrlines('MLSD', lines.append)
        entries = {}

        for line in lines:
            # Break down each part of the string (for example): ;modify=20251028155020;
            attributes: list[str] = line.split(';')
            # The last part of each line is the file name
            filename = attributes[-1].strip()
            # Break attributes into their component parts (for example): ['modify', '20251028155020']
            attributes_parsed: list[list[str]] = [x.split('=') for x in attributes]
            # Keep only the 'modify' value
            modify = [x[1] for x in attributes_parsed if x[0] == 'modify']
            entries[filename] = modify[0]

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
            return self._datetime_from_time_string(entries[name])
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
            last_modified = storage_backend.get_modified_time(file_name)
            now = datetime.datetime.now(datetime.UTC)
            delta = now - last_modified
            valid = delta < datetime.timedelta(hours=IPS_EXPIRY_HOURS)

            LOGGER.debug(
                f'{"KEEP" if valid else "DELETE"} - Bundle "{file_name}" last modified {delta} ago ({last_modified} UTC)',
            )

            if not valid:
                try:
                    if not dry_run:
                        storage_backend.delete(file_name)

                    num_deleted += 1
                # Bare except: catch any possible error here in order to properly log it and continue
                except:  # noqa: E722
                    # Example of a one-off error: PermissionError: [WinError 10013] An attempt was made to access a socket in a way forbidden by its access permissions
                    LOGGER.exception(f'Failed to delete IPS bundle "{file_name}"')
                    num_errors += 1

        LOGGER.info(
            f'{num_deleted} IPS {"bundle" if num_deleted == 1 else "bundles"} out of {len(file_list)} {"would be" if dry_run else "was" if num_deleted == 1 else "were"} deleted ({num_errors} {"error" if num_errors == 1 else "errors"})',
        )
