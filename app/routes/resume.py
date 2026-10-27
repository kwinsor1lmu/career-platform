from datetime import date
from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

from app.db import SessionLocal
from app.services.resume import load_public_projects, load_resume_with_fallback

router = APIRouter()
templates = Jinja2Templates(directory=Path(__file__).resolve().parent.parent / "templates")

_MONTHS = ("Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec")


def _month_index(value: str) -> tuple[int, int] | None:
    parts = value.split("-")
    if len(parts) < 2:
        return None
    return int(parts[0]), int(parts[1])


def format_date(value: str | None) -> str:
    """Render a partial ISO date ("2020", "2020-01", "2020-01-15") as "Jan 2020"."""
    if not value:
        return ""
    month = _month_index(value)
    if month is None:
        return value
    return f"{_MONTHS[month[1] - 1]} {month[0]}"


def format_duration(start: str | None, end: str | None, today: date | None = None) -> str:
    """Render the span between two month-precision dates as "4 yr 9 mo"."""
    if not start:
        return ""
    start_month = _month_index(start)
    if start_month is None:
        return ""
    if end:
        end_month = _month_index(end)
        if end_month is None:
            return ""
    else:
        today = today or date.today()
        end_month = (today.year, today.month)
    months = (end_month[0] - start_month[0]) * 12 + end_month[1] - start_month[1] + 1
    if months < 1:
        return ""
    years, months = divmod(months, 12)
    parts = [f"{years} yr" if years else "", f"{months} mo" if months else ""]
    return " ".join(part for part in parts if part)


def display_url(value: object) -> str:
    """Strip the scheme and trailing slash so a link reads as "github.com/name"."""
    text = str(value)
    for prefix in ("mailto:", "https://", "http://", "www."):
        text = text.removeprefix(prefix)
    return text.rstrip("/")


templates.env.filters["resume_date"] = format_date
templates.env.filters["resume_duration"] = format_duration
templates.env.filters["display_url"] = display_url
templates.env.tests["mailto"] = lambda value: str(value).startswith("mailto:")


def _render_resume(request: Request):
    settings = request.app.state.settings
    resume, source = load_resume_with_fallback(SessionLocal, settings.fallback_path)
    projects = load_public_projects(SessionLocal)
    return templates.TemplateResponse(
        request=request,
        name="resume.html",
        context={
            "resume": resume,
            "source": source,
            "projects": projects,
            "canonical_url": str(request.url_for("resume-home")),
        },
        status_code=503 if projects is None else 200,
    )


@router.get("/", name="resume-home")
def home(request: Request):
    return _render_resume(request)


@router.get("/resume", name="resume-page")
def resume_page(request: Request):
    return _render_resume(request)


@router.get("/privacy", name="privacy-page")
def privacy_page(request: Request):
    settings = request.app.state.settings
    resume, _ = load_resume_with_fallback(SessionLocal, settings.fallback_path)
    return templates.TemplateResponse(
        request=request,
        name="privacy.html",
        context={"resume": resume, "canonical_url": str(request.url_for("privacy-page"))},
    )
