# SPDX-FileCopyrightText: Copyright (C) 2025 Opal Health Informatics Group at the Research Institute of the McGill University Health Centre <john.kildea@mcgill.ca>
#
# SPDX-License-Identifier: AGPL-3.0-or-later

"""
Module containing Pydantic models that define schemas for APIs that an integration engine exposes.

To avoid confusion with the actual models, the Pydantic models are named with a Schema suffix.
"""

from datetime import date, datetime
from enum import StrEnum, auto
from typing import Self

from pydantic import AwareDatetime, Base64Bytes, BaseModel, Field, model_validator


class ErrorResponseSchema(BaseModel):
    """An error response that is provided for any non-OK (200) HTTP response."""

    status: int
    message: str


class _MRNSiteSchema(BaseModel):
    """A patient's hospital number consisting of an MRN and a site code."""

    mrn: str = Field(min_length=1, max_length=10)
    site: str = Field(min_length=3, max_length=10)


class HospitalNumberSchema(_MRNSiteSchema):
    """A patient's hospital number consisting of an MRN and a site code."""

    is_active: bool = True


class SexTypeSchema(StrEnum):
    """The sex of a patient."""

    MALE = auto()
    FEMALE = auto()
    OTHER = auto()
    UNKNOWN = auto()


class PatientSchema(BaseModel):
    """A patient with their details as stored in an institution."""

    first_name: str = Field(min_length=1, max_length=150)
    last_name: str = Field(min_length=1, max_length=150)
    sex: SexTypeSchema
    date_of_birth: date
    date_of_death: datetime | None
    health_insurance_number: str | None = Field(min_length=1, max_length=12)
    mrns: list[HospitalNumberSchema]

    @model_validator(mode='after')
    def check_medical_number(self) -> Self:
        """
        Check that a patient has at least one medical number (MRN or health insurance number).

        Raises:
            ValueError: if neither MRN nor health insurance number is provided

        Returns:
            the model instance
        """
        if not self.mrns and not self.health_insurance_number:
            raise ValueError('Patient must have at least one medical number (MRN or health insurance number)')

        return self


class PatientByHINSchema(BaseModel):
    """The request to search for a patient by health insurance number."""

    health_insurance_number: str


class PatientByMRNSchema(HospitalNumberSchema):
    """The request to search for a patient by hospital number (MRN and site code)."""

    pass


class QuestionnaireReportRequestSchema(_MRNSiteSchema):
    """The request to generate a questionnaire report."""

    document: Base64Bytes
    document_datetime: AwareDatetime
