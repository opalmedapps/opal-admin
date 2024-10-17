"""Shared functionality for report generation functionality."""
from typing import Literal

from fpdf import Align
from typing_extensions import TypedDict


class FPDFCellDictType(TypedDict):
    """The required arguments to pass to FPDF's cell() function."""

    w: float | None  # noqa: WPS111
    h: float | None  # noqa: WPS111
    text: str
    border: bool | str | Literal[0, 1]
    align: str | Align


class FPDFMultiCellDictType(TypedDict):
    """The required arguments to pass to FPDF's multi_cell() function."""

    w: float  # noqa: WPS111
    h: float | None  # noqa: WPS111
    text: str
    align: str | Align


class FPDFFontDictType(TypedDict):
    """The required arguments to pass to FPDF's set_font() function."""

    family: str | None
    style: Literal['', 'B', 'I', 'U', 'BU', 'UB', 'BI', 'IB', 'IU', 'UI', 'BIU', 'BUI', 'IBU', 'IUB', 'UBI', 'UIB']
    size: int


class FPDFRectDictType(TypedDict):
    """The required arguments to pass to FPDF's rect() function."""

    x: float  # noqa: WPS111
    y: float  # noqa: WPS111
    w: float  # noqa: WPS111
    h: float  # noqa: WPS111
    style: str | None
