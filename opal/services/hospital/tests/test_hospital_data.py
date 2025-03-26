from datetime import datetime

from opal.services.hospital.hospital_data import OIEReportExportData


def test_report_data_type() -> None:
    """Ensure `OIEReportExportData` NamedTuple can be instantiated."""
    assert OIEReportExportData(
        mrn='9999996',
        site='RVH',
        base64_content='base64',
        document_number='FMU',
        document_date=datetime.now(),
    )
