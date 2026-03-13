# SPDX-FileCopyrightText: Copyright (C) 2025 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Command for cleaning up expired IPS bundles."""

import datetime
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

        storage_backend = FTPStorage()

        file_list = storage_backend.listdir('../bundles')[1]
        file_list = [name for name in file_list if re.match(r'^.+\.ips$', name)]

        LOGGER.info(
            'Checking %s file%s to clean up expired IPS bundles (from storage backend: %s)',
            len(file_list),
            '' if len(file_list) == 1 else 's',
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
            '%s IPS bundle%s out of %s %s deleted (%s error%s)',
            num_deleted,
            '' if num_deleted == 1 else 's',
            len(file_list),
            'would be' if dry_run else 'was' if num_deleted == 1 else 'were',
            num_errors,
            '' if num_errors == 1 else 's',
        )

        storage_backend.disconnect()
