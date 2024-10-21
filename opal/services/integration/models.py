from datetime import date, datetime
from enum import StrEnum, auto

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    status_code: int
    message: str


class HospitalNumber(BaseModel):
    # TODO: validate this? non-empty strings
    mrn: str
    site: str


class SexType(StrEnum):
    MALE = auto()
    FEMALE = auto()
    OTHER = auto()
    UNKNOWN = auto()


class Patient(BaseModel):
    first_name: str
    last_name: str
    # limit to an enum
    sex: SexType
    date_of_birth: date
    # TODO: derive or remove? Or do deceased: datetime | None (or deceased_at)
    # deceased: bool = False
    # TODO: date_of_death
    # TODO: validate to be after date of birth
    # TODO: enforce timezone-aware?
    datetime_of_death: datetime | None = None
    # TODO: validate? what if there is none? empty string or None? should there be at least one between HIN and MRNs?
    health_insurance_number: str
    mrns: list[HospitalNumber] = Field(default_factory=list)


class PatientByHINRequest(BaseModel):
    health_insurance_number: str


class PatientByMRNRequest(HospitalNumber):
    pass  # noqa: WPS420, WPS604
