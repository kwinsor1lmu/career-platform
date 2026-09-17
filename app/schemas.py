from __future__ import annotations

from datetime import date
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator, model_validator

Visibility = Literal["draft", "private", "published"]
DateValue = Annotated[str, Field(pattern=r"^\d{4}(?:-\d{2}(?:-\d{2})?)?$")]
Identifier = Annotated[str, Field(min_length=1, max_length=120, pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]*$")]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Profile(StrictModel):
    id: Identifier
    name: str = Field(min_length=1)
    headline: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    visibility: Visibility


class DatedRecord(StrictModel):
    id: Identifier
    start_date: DateValue | None = None
    end_date: DateValue | None = None
    summary: str = Field(min_length=1)
    order: int = Field(ge=0)
    visibility: Visibility

    @field_validator("start_date", "end_date")
    @classmethod
    def validate_partial_date(cls, value: str | None) -> str | None:
        if value is None:
            return value
        parts = [int(part) for part in value.split("-")]
        if len(parts) == 2 and not 1 <= parts[1] <= 12:
            raise ValueError("date month must be between 01 and 12")
        if len(parts) == 3:
            date(*parts)
        return value

    @model_validator(mode="after")
    def validate_date_order(self) -> DatedRecord:
        if self.start_date and self.end_date:
            if _date_parts(self.end_date) < _date_parts(self.start_date):
                raise ValueError("end_date must be on or after start_date")
        return self


class Experience(DatedRecord):
    employer: str = Field(min_length=1)
    title: str = Field(min_length=1)


class Education(DatedRecord):
    institution: str = Field(min_length=1)
    degree: str = Field(min_length=1)


class Skill(StrictModel):
    id: Identifier
    name: str = Field(min_length=1)
    level: str | None = None
    order: int = Field(ge=0)
    visibility: Visibility


class Certification(DatedRecord):
    name: str = Field(min_length=1)
    issuer: str = Field(min_length=1)


class ContactLink(StrictModel):
    id: Identifier
    label: str = Field(min_length=1)
    url: HttpUrl
    order: int = Field(ge=0)
    visibility: Visibility


class ResumeSource(StrictModel):
    profile: Profile
    experience: list[Experience] = Field(default_factory=list)
    education: list[Education] = Field(default_factory=list)
    skills: list[Skill] = Field(default_factory=list)
    certifications: list[Certification] = Field(default_factory=list)
    contact_links: list[ContactLink] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_unique_section_ids(self) -> ResumeSource:
        for section_name in (
            "experience",
            "education",
            "skills",
            "certifications",
            "contact_links",
        ):
            records = getattr(self, section_name)
            ids = [record.id for record in records]
            if len(ids) != len(set(ids)):
                raise ValueError(f"duplicate id in {section_name}")
        return self


def _date_parts(value: str) -> tuple[int, int, int]:
    parts = [int(part) for part in value.split("-")]
    return tuple(parts + [0] * (3 - len(parts)))
