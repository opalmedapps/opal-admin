from datetime import date, datetime, timedelta

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
        document_date=datetime.now(),
    )


def test_patient_data_type() -> None:
    """Ensure `SourceSystemPatientData` NamedTuple and `SourceSystemMRNData` NamedTuple can be instantiated."""
    assert SourceSystemPatientData(
        date_of_birth=date.today(),
        first_name='aaa',
        last_name='bbb',
        sex='M',
        alias='',
        deceased=True,
        death_date_time=datetime.now() + relativedelta(years=70),
        ramq='RAMQ12345678',
        ramq_expiration=datetime.now() + timedelta(days=100),
        mrns=[
            SourceSystemMRNData(
                site='RVH',
                mrn='9999996',
                active=True,
            ),
        ],
    )
