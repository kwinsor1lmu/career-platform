from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

from app.db import SessionLocal
from app.services.resume import load_resume_with_fallback

router = APIRouter()
templates = Jinja2Templates(directory=Path(__file__).resolve().parent.parent / "templates")


def _render_resume(request: Request):
    settings = request.app.state.settings
    resume, _ = load_resume_with_fallback(SessionLocal, settings.fallback_path)
    return templates.TemplateResponse(request=request, name="resume.html", context={"resume": resume})


@router.get("/", name="resume-home")
def home(request: Request):
    return _render_resume(request)


@router.get("/resume", name="resume-page")
def resume_page(request: Request):
    return _render_resume(request)
