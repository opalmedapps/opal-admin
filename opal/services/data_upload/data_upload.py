# SPDX-FileCopyrightText: Copyright (C) 2025 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""Functions in this module provide the ability to upload files to an external server."""

# TODO find different library?
from ftplib import FTP_TLS
from io import BytesIO

from django.conf import settings


class DataUpload:
    """Class that manages interactions with an FTP server for file uploads."""

    def upload(self, working_directory: str, filename: str, contents: bytes):
        """Uploads a file to an FTP server."""
        if not settings.FTP_ENABLED:
            raise NotImplementedError("DataUpload can't be used, because FTP isn't enabled")

        bytes_file = BytesIO(contents)

        ftps = FTP_TLS(host=settings.FTP_HOST, user=settings.FTP_USER, passwd=settings.FTP_PASSWORD)
        ftps.prot_p()

        ftps.cwd(working_directory)
        ftps.storbinary(f'STOR {filename}', bytes_file)
        ftps.retrlines('LIST')
