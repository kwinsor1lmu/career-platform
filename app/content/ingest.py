from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.models import (
    Certification,
    ContactLink,
    Education,
    Experience,
    Profile,
    Skill,
)
from app.schemas import ResumeSource

DEFAULT_OWNER_ID = "owner-1"

_SECTION_MODELS: tuple[tuple[str, type[Any], str], ...] = (
    ("experience", Experience, "experience"),
    ("education", Education, "education"),
    ("skills", Skill, "skills"),
    ("certifications", Certification, "certifications"),
    ("contact_links", ContactLink, "contact_links"),
)


def ingest_resume(session: Session, source: ResumeSource) -> None:
    profile_id = source.profile.id
    owner_id = DEFAULT_OWNER_ID

    with session.begin():
        profile = session.query(Profile).filter_by(id=profile_id, owner_id=owner_id).one_or_none()
        if profile is None:
            profile = Profile(
                id=profile_id,
                owner_id=owner_id,
                name=source.profile.name,
                headline=source.profile.headline,
                summary=source.profile.summary,
                visibility=source.profile.visibility,
            )
            session.add(profile)
        else:
            profile.name = source.profile.name
            profile.headline = source.profile.headline
            profile.summary = source.profile.summary
            profile.visibility = source.profile.visibility
            session.add(profile)

        for _, model_cls, field_name in _SECTION_MODELS:
            incoming_items = list(getattr(source, field_name, ()))
            incoming_ids = {item.id for item in incoming_items}
            existing_rows = (
                session.query(model_cls)
                .filter(model_cls.profile_id == profile_id, model_cls.owner_id == owner_id)
                .all()
            )
            existing_by_stable_id = {row.stable_id: row for row in existing_rows}

            for item in incoming_items:
                row = existing_by_stable_id.get(item.id)
                if row is None:
                    row = model_cls(
                        profile_id=profile_id,
                        owner_id=owner_id,
                        stable_id=item.id,
                        visibility=item.visibility,
                        display_order=item.order,
                    )
                row.profile_id = profile_id
                row.owner_id = owner_id
                row.stable_id = item.id
                row.visibility = item.visibility
                row.display_order = item.order

                if model_cls is Experience:
                    row.employer = item.employer
                    row.title = item.title
                    row.summary = item.summary
                    row.start_date = item.start_date
                    row.end_date = item.end_date
                elif model_cls is Education:
                    row.institution = item.institution
                    row.degree = item.degree
                    row.summary = item.summary
                    row.start_date = item.start_date
                    row.end_date = item.end_date
                elif model_cls is Skill:
                    row.name = item.name
                    row.level = item.level
                elif model_cls is Certification:
                    row.name = item.name
                    row.issuer = item.issuer
                    row.summary = item.summary
                    row.start_date = item.start_date
                    row.end_date = item.end_date
                elif model_cls is ContactLink:
                    row.label = item.label
                    row.url = str(item.url)

                session.add(row)

            for stable_id in list(existing_by_stable_id):
                if stable_id not in incoming_ids:
                    session.delete(existing_by_stable_id[stable_id])

        session.flush()
