from datetime import date, datetime
from enum import StrEnum, auto

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    status_code: int
    message: str


class HospitalNumber(BaseModel):
    mrn: str = Field(min_length=1, max_length=10)
    site: str = Field(min_length=3, max_length=10)


class SexType(StrEnum):
    MALE = auto()
    FEMALE = auto()
    OTHER = auto()
    UNKNOWN = auto()


class Patient(BaseModel):
    first_name: str = Field(min_length=1, max_length=150)
    last_name: str = Field(min_length=1, max_length=150)
    sex: SexType
    date_of_birth: date
    date_of_death: datetime | None
    health_insurance_number: str | None = Field(min_length=1, max_length=12)
    mrns: list[HospitalNumber] = Field(min_length=1)


class PatientByHINRequest(BaseModel):
    health_insurance_number: str


class PatientByMRNRequest(HospitalNumber):
    pass  # noqa: WPS420, WPS604
