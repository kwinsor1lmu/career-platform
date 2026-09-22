from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.content.ingest import DEFAULT_OWNER_ID
from app.models import (
    Certification,
    ContactLink,
    Education,
    Experience,
    Profile,
    Skill,
)
from app.schemas import (
    Certification as PublicCertification,
    ContactLink as PublicContactLink,
    Education as PublicEducation,
    Experience as PublicExperience,
    Profile as PublicProfile,
    ResumeSource,
    Skill as PublicSkill,
)


@dataclass
class PublicResume:
    profile: PublicProfile
    experience: list[PublicExperience] = field(default_factory=list)
    education: list[PublicEducation] = field(default_factory=list)
    skills: list[PublicSkill] = field(default_factory=list)
    certifications: list[PublicCertification] = field(default_factory=list)
    contact_links: list[PublicContactLink] = field(default_factory=list)

    def all_items(self):
        return [
            *self.experience,
            *self.education,
            *self.skills,
            *self.certifications,
            *self.contact_links,
        ]


def _to_profile_model(row: Profile) -> PublicProfile:
    return PublicProfile(
        id=row.id,
        name=row.name,
        headline=row.headline,
        summary=row.summary,
        visibility=row.visibility,
    )


def _to_experience_model(row: Experience) -> PublicExperience:
    return PublicExperience(
        id=row.stable_id,
        employer=row.employer,
        title=row.title,
        summary=row.summary,
        start_date=row.start_date,
        end_date=row.end_date,
        order=row.display_order,
        visibility=row.visibility,
    )


def _to_education_model(row: Education) -> PublicEducation:
    return PublicEducation(
        id=row.stable_id,
        institution=row.institution,
        degree=row.degree,
        summary=row.summary,
        start_date=row.start_date,
        end_date=row.end_date,
        order=row.display_order,
        visibility=row.visibility,
    )


def _to_skill_model(row: Skill) -> PublicSkill:
    return PublicSkill(
        id=row.stable_id,
        name=row.name,
        level=row.level,
        order=row.display_order,
        visibility=row.visibility,
    )


def _to_certification_model(row: Certification) -> PublicCertification:
    return PublicCertification(
        id=row.stable_id,
        name=row.name,
        issuer=row.issuer,
        summary=row.summary,
        start_date=row.start_date,
        end_date=row.end_date,
        order=row.display_order,
        visibility=row.visibility,
    )


def _to_contact_link_model(row: ContactLink) -> PublicContactLink:
    return PublicContactLink(
        id=row.stable_id,
        label=row.label,
        url=row.url,
        order=row.display_order,
        visibility=row.visibility,
    )


def _ordered_rows(rows, *, order_by: str = "display_order") -> list:
    return sorted(rows, key=lambda row: (getattr(row, order_by), getattr(row, "stable_id", "")))


def get_public_resume(session: Session) -> PublicResume:
    profile_row = (
        session.query(Profile)
        .filter(Profile.owner_id == DEFAULT_OWNER_ID, Profile.visibility == "published")
        .order_by(Profile.id.asc())
        .first()
    )
    if profile_row is None:
        raise ValueError("No published profile is available for this owner.")

    experience_rows = (
        session.query(Experience)
        .filter(Experience.profile_id == profile_row.id, Experience.owner_id == DEFAULT_OWNER_ID, Experience.visibility == "published")
        .order_by(Experience.display_order.asc(), Experience.stable_id.asc())
        .all()
    )
    education_rows = (
        session.query(Education)
        .filter(Education.profile_id == profile_row.id, Education.owner_id == DEFAULT_OWNER_ID, Education.visibility == "published")
        .order_by(Education.display_order.asc(), Education.stable_id.asc())
        .all()
    )
    skill_rows = (
        session.query(Skill)
        .filter(Skill.profile_id == profile_row.id, Skill.owner_id == DEFAULT_OWNER_ID, Skill.visibility == "published")
        .order_by(Skill.display_order.asc(), Skill.stable_id.asc())
        .all()
    )
    certification_rows = (
        session.query(Certification)
        .filter(Certification.profile_id == profile_row.id, Certification.owner_id == DEFAULT_OWNER_ID, Certification.visibility == "published")
        .order_by(Certification.display_order.asc(), Certification.stable_id.asc())
        .all()
    )
    contact_rows = (
        session.query(ContactLink)
        .filter(ContactLink.profile_id == profile_row.id, ContactLink.owner_id == DEFAULT_OWNER_ID, ContactLink.visibility == "published")
        .order_by(ContactLink.display_order.asc(), ContactLink.stable_id.asc())
        .all()
    )

    return PublicResume(
        profile=_to_profile_model(profile_row),
        experience=[_to_experience_model(row) for row in experience_rows],
        education=[_to_education_model(row) for row in education_rows],
        skills=[_to_skill_model(row) for row in skill_rows],
        certifications=[_to_certification_model(row) for row in certification_rows],
        contact_links=[_to_contact_link_model(row) for row in contact_rows],
    )


def get_owner_resume(session: Session) -> ResumeSource:
    profile_row = (
        session.query(Profile)
        .filter(Profile.owner_id == DEFAULT_OWNER_ID)
        .order_by(Profile.id.asc())
        .first()
    )
    if profile_row is None:
        raise ValueError("No profile is available for this owner.")

    return ResumeSource(
        profile=_to_profile_model(profile_row),
        experience=[_to_experience_model(row) for row in _ordered_rows(session.query(Experience).filter(Experience.profile_id == profile_row.id, Experience.owner_id == DEFAULT_OWNER_ID).all())],
        education=[_to_education_model(row) for row in _ordered_rows(session.query(Education).filter(Education.profile_id == profile_row.id, Education.owner_id == DEFAULT_OWNER_ID).all())],
        skills=[_to_skill_model(row) for row in _ordered_rows(session.query(Skill).filter(Skill.profile_id == profile_row.id, Skill.owner_id == DEFAULT_OWNER_ID).all())],
        certifications=[_to_certification_model(row) for row in _ordered_rows(session.query(Certification).filter(Certification.profile_id == profile_row.id, Certification.owner_id == DEFAULT_OWNER_ID).all())],
        contact_links=[_to_contact_link_model(row) for row in _ordered_rows(session.query(ContactLink).filter(ContactLink.profile_id == profile_row.id, ContactLink.owner_id == DEFAULT_OWNER_ID).all())],
    )
