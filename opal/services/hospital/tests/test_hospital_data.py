# SPDX-FileCopyrightText: Copyright (C) 2022 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later


from django.utils import timezone

from opal.services.hospital.hospital_data import (
    SourceSystemReportExportData,
)


def test_report_data_type() -> None:
    """Ensure `SourceSystemReportExportData` NamedTuple can be instantiated."""
    assert SourceSystemReportExportData(
        mrn='9999996',
        site='RVH',
        base64_content='base64',
        document_number='FMU',
        document_date=timezone.now(),
    )
