"""
Module containing Pydantic models that define schemas for APIs that an integration engine exposes.

To avoid confusion with the actual models, the Pydantic models are named with a Schema suffix.
"""

from datetime import date, datetime
from enum import StrEnum, auto

from pydantic import BaseModel, Field


class ErrorResponseSchema(BaseModel):
    """An error response that is provided for any non-OK (200) HTTP response."""

    status_code: int
    message: str


class HospitalNumberSchema(BaseModel):
    """A patient's hospital number consisting of an MRN and a site code."""

    mrn: str = Field(min_length=1, max_length=10)
    site: str = Field(min_length=3, max_length=10)


class SexType(StrEnum):
    """The sex of a patient."""

    MALE = auto()
    FEMALE = auto()
    OTHER = auto()
    UNKNOWN = auto()


class PatientSchema(BaseModel):
    """A patient with their details as stored in an institution."""

    first_name: str = Field(min_length=1, max_length=150)
    last_name: str = Field(min_length=1, max_length=150)
    sex: SexType
    date_of_birth: date
    date_of_death: datetime | None
    health_insurance_number: str | None = Field(min_length=1, max_length=12)
    mrns: list[HospitalNumberSchema] = Field(min_length=1)


class PatientByHINSchema(BaseModel):
    """The request to search for a patient by health insurance number."""

    health_insurance_number: str


class PatientByMRNSchema(HospitalNumberSchema):
    """The request to search for a patient by hospital number (MRN and site code)."""

    pass
