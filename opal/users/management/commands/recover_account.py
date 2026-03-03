# SPDX-FileCopyrightText: Copyright (C) 2024 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Management command for recovering the caregiver user profile and patient data."""

from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand, CommandParser
from django.core.serializers import deserialize


class Command(BaseCommand):
    """
    Command to recover the caregiver data from the backup file.

    The command recover caregiver profile, user, relationship, related patient data.
    """

    help = 'Recover the caregiver profile and related data from the backup.'

    def add_arguments(self, parser: CommandParser) -> None:
        """
        Add arguments to the command.

        Args:
            parser: the command parser to add arguments to
        """
        parser.add_argument(
            'file_path',
            type=str,
            help='The file path of the data that will be recover',
        )

    def handle(self, *args: Any, **options: Any) -> None:
        """
        Command to recover the caregiver data in the database.

        Args:
            args: input arguments
            options:  additional keyword arguments
        """
        file_path = options['file_path']
        with Path(file_path).open('r', encoding='utf-8') as user_data:
            for data in deserialize('json', user_data):
                data.save()

        self.stdout.write(self.style.SUCCESS('Data successfully recovered! Please delete the backup file.'))
