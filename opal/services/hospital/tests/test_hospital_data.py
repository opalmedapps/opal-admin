from datetime import datetime, timedelta

from opal.services.hospital.hospital_data import OIEMRNData, OIEPatientData, OIEReportExportData


def test_report_data_type() -> None:
    """Ensure `OIEReportExportData` NamedTuple can be instantiated."""
    assert OIEReportExportData(
        mrn='9999996',
        site='RVH',
        base64_content='base64',
        document_number='FMU',
        document_date=datetime.now(),
    )


def test_patient_data_type() -> None:
    """Ensure `OIEPatientData` NamedTuple and `OIEMRNData` NamedTuple can be instantiated."""
    assert OIEPatientData(
        date_of_birth=datetime.now(),
        first_name='aaa',
        last_name='bbb',
        sex='M',
        alias='',
        ramq='RAMQ12345678',
        ramq_expiration=datetime.now() + timedelta(days=100),
        mrns=[
            OIEMRNData(
                site='RVH',
                mrn='9999996',
                active=True,
            ),
        ],
    )
