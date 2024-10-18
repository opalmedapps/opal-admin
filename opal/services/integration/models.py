from datetime import date, datetime

from pydantic import BaseModel


class ErrorResponse(BaseModel):
    status_code: int
    message: str


class HospitalNumber(BaseModel):
    mrn: str
    site: str


class Patient(BaseModel):
    first_name: str
    last_name: str
    sex: str
    date_of_birth: date
    # TODO: derive?
    deceased: bool = False
    # TODO: date_of_death
    datetime_of_death: datetime | None = None
    health_insurance_number: str
    mrns: list[HospitalNumber]


class RequestPatientByHIN(BaseModel):
    health_insurance_number: str


class RequestPatientByMRN(HospitalNumber):
    pass  # noqa: WPS420, WPS604
