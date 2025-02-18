# SPDX-FileCopyrightText: Copyright (C) 2022 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

from datetime import timedelta

from django.utils import timezone

from dateutil.relativedelta import relativedelta

from opal.services.hospital.hospital_data import (
    SourceSystemMRNData,
    SourceSystemPatientData,
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


def test_patient_data_type() -> None:
    """Ensure `SourceSystemPatientData` NamedTuple and `SourceSystemMRNData` NamedTuple can be instantiated."""
    assert SourceSystemPatientData(
        date_of_birth=timezone.now().date(),
        first_name='aaa',
        last_name='bbb',
        sex='M',
        alias='',
        deceased=True,
        death_date_time=timezone.now() + relativedelta(years=70),
        ramq='RAMQ12345678',
        ramq_expiration=timezone.now() + timedelta(days=100),
        mrns=[
            SourceSystemMRNData(
                site='RVH',
                mrn='9999996',
                active=True,
            ),
        ],
    )
