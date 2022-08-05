import re

from opal.utils.base64 import Base64Util

from .hospital import OIEReportExportData


def is_report_export_data_valid(
    report_data: OIEReportExportData,
) -> bool:
    """Check if OIE report export data is valid.

    Args:
        report_data (OIEReportExportData): OIE report export data needed to call OIE endpoint

    Returns:
        bool: boolean value showing if OIE report export data is valid
    """
    # TODO: Add more validation/checks for the MRN and Site fields once the requirements are clarified
    # TODO: Confirm the regex pattern for the document number
    reg_exp = re.compile('(^FU-[a-zA-Z0-9]+$)|(^FMU-[a-zA-Z0-9]+$)')
    return (  # check if MRN is not empty
        bool(report_data.mrn.strip())
        # check if site is not empty
        and bool(report_data.site.strip())
        # check if report content is base64
        and Base64Util().is_base64(report_data.base64_content)
        # check if document type format is valid
        and bool(reg_exp.match(report_data.document_number))
    )


def is_report_export_response_valid(
    response_data: dict,
) -> bool:
    return True
