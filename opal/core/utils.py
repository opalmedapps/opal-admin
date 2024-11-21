"""App core util functions."""
import io
import random
import secrets
import string
import uuid
import zipfile
from typing import Any, TypeAlias

import qrcode
from openpyxl import Workbook
from qrcode.image import svg

# Type aliases
RowData: TypeAlias = dict[str, Any]
SheetData: TypeAlias = list[RowData]
WorkbookData: TypeAlias = dict[str, SheetData]


def generate_random_number(length: int) -> str:
    """Generate random number with the parameter length.

    Args:
        length: length of the number.

    Returns:
        return a string number
    """
    return ''.join(secrets.choice(string.digits) for _ in range(length))


def generate_random_uuid(length: int) -> str:
    """Generate a random uuid hexadecimal string with a given length.

    Args:
        length: length of a random uuid hexadecimal string.

    Returns:
        return a random uuid hexadecimal string
    """
    return uuid.uuid4().hex[:length]


def generate_random_registration_code(institution_code: str, length: int) -> str:
    """Generate a random alphanumeric string with a given length.

    Args:
        institution_code: intitution code for registration.
        length: length of a random alphanumeric string.

    Returns:
        return a random alphanumeric string
    """
    # getting systemRandom instance out of random class to prevent flake8 S311 vioaltion
    # and generate cryptographically secure random.
    system_random = random.SystemRandom()
    return institution_code + ''.join(
        system_random.choices(string.ascii_letters + string.digits, k=length),
    )


def qr_code(text: str) -> bytes:
    """
    Create a QR code for the given text.

    Args:
        text: text to encode in the QR code

    Returns:
        the in-memory image as bytes
    """
    code = qrcode.QRCode(
        version=1,
        border=0,
    )
    code.add_data(text)
    code.make(fit=True)

    image = code.make_image(
        image_factory=svg.SvgImage,
        back_color='white',
        fill_color='white',
    )

    stream = io.BytesIO()
    image.save(stream)

    return stream.getvalue()


def create_zip(files: dict[str, bytes]) -> bytes:
    """Create a ZIP file from a mapping of files.

    The ZIP file is returned as bytes.

    Args:
        files: dictionary of files to be archived, where the key is filename and the value is `bytes` object.

    Returns:
        `bytes` object containing the ZIP file
    """
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(file=zip_buffer, mode='w', compression=zipfile.ZIP_DEFLATED) as zip_file:
        for filename, file_content in files.items():
            zip_file.writestr(filename, file_content)
    return zip_buffer.getvalue()


def dict_to_xlsx(dicts: WorkbookData) -> bytes:
    """Create an XLSX file from a mapping of dictionaries and return it as bytes.

    Each `RowData` dictionary is expected to have the same keys, as the sheet header is
    determined by the keys of the first dictionary.

    Args:
        dicts: a mapping where each key is a sheet name, and the value is a list of dictionaries representing rows.

    Returns:
        bytes: the XLSX file content as bytes.
    """
    workbook = Workbook()
    # Remove the default sheet created by openpyxl
    workbook.remove(workbook.active)

    for sheet_name, rows in dicts.items():
        _add_sheet_to_workbook(workbook, sheet_name, rows)

    output_stream = io.BytesIO()
    workbook.save(output_stream)
    return output_stream.getvalue()


def _add_sheet_to_workbook(workbook: Workbook, sheet_name: str, rows: SheetData) -> None:
    """Add a sheet with the given name and rows to the workbook.

    Args:
        workbook: the workbook to add the sheet to.
        sheet_name: The name of the sheet.
        rows: the data rows to add to the sheet.
    """
    # If sheet data is empty, continue to next sheet
    if not rows:
        return

    worksheet = workbook.create_sheet(title=sheet_name)
    headers = list(rows[0].keys())
    worksheet.append(headers)

    for row_data in rows:
        worksheet.append([row_data.get(header, '') for header in headers])
