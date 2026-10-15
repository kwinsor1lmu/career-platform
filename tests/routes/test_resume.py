from datetime import date

from fastapi.testclient import TestClient

from app.main import create_app
from app.repositories.resume import PublicResume
from app.routes.resume import display_url, format_date, format_duration
from app.schemas import Certification, Education, Experience, Profile, Skill


def _profile() -> Profile:
    return Profile(
        id="profile",
        name="Ada Example",
        headline="Software engineer",
        summary="Builds useful systems.",
        visibility="published",
    )


def _public_resume() -> PublicResume:
    return PublicResume(profile=_profile())


def _full_resume() -> PublicResume:
    return PublicResume(
        profile=_profile(),
        experience=[
            Experience(
                id="work",
                employer="Example Co",
                title="Engineer",
                summary="Public work.",
                start_date="2020-01",
                end_date="2021-06",
                order=1,
                visibility="published",
            ),
            Experience(
                id="undated",
                employer="Undated Co",
                title="Contractor",
                summary="Undated work.",
                order=2,
                visibility="published",
            ),
        ],
        education=[
            Education(
                id="school",
                institution="Example University",
                degree="BSc",
                summary="Study.",
                start_date="2016-09",
                end_date="2020-06",
                order=1,
                visibility="published",
            )
        ],
        skills=[Skill(id="python", name="Python", level="Advanced", order=1, visibility="published")],
        certifications=[
            Certification(
                id="cert",
                name="Cloud Certificate",
                issuer="Example Institute",
                summary="Certified.",
                start_date="2023",
                order=1,
                visibility="published",
            )
        ],
    )


def _get(monkeypatch, resume: PublicResume, source: str = "database"):
    monkeypatch.setattr(
        "app.routes.resume.load_resume_with_fallback",
        lambda session_factory, fallback_path: (resume, source),
    )
    return TestClient(create_app()).get("/")


def test_resume_page_contains_core_sections(monkeypatch):
    response = _get(monkeypatch, _full_resume())

    assert response.status_code == 200
    assert "<main" in response.text
    assert "Experience" in response.text
    assert "Education" in response.text
    assert "Skills" in response.text
    assert "Credentials" in response.text


def test_resume_page_formats_dates_for_people(monkeypatch):
    html = _get(monkeypatch, _full_resume()).text

    assert '<time datetime="2020-01">Jan 2020</time> – <time datetime="2021-06">Jun 2021</time>' in html
    assert "1 yr 6 mo" in html
    assert '<time datetime="2023">2023</time>' in html
    assert "Undated Co" in html
    assert "– Present" not in html.split("Undated Co", 1)[1].split("</li>", 1)[0]


def test_resume_page_hides_skill_self_ratings(monkeypatch):
    html = _get(monkeypatch, _full_resume()).text

    assert "Python" in html
    assert "Advanced" not in html


def test_resume_page_hides_empty_sections(monkeypatch):
    html = _get(monkeypatch, _public_resume()).text

    assert 'id="experience"' not in html
    assert 'id="skills"' not in html
    assert 'id="credentials"' not in html
    assert "listed." not in html


def test_resume_page_announces_saved_copy_only_for_fallback(monkeypatch):
    assert "saved copy" in _get(monkeypatch, _public_resume(), "fallback").text
    assert "saved copy" not in _get(monkeypatch, _public_resume(), "database").text


def test_resume_page_does_not_render_private_content(monkeypatch):
    response = _get(monkeypatch, _public_resume(), "fallback")

    assert "private fixture text" not in response.text


def test_format_date_handles_partial_dates():
    assert format_date("2020-01") == "Jan 2020"
    assert format_date("2020-12-31") == "Dec 2020"
    assert format_date("2019") == "2019"
    assert format_date(None) == ""


def test_format_duration_counts_inclusive_months():
    assert format_duration("2020-01", "2021-06") == "1 yr 6 mo"
    assert format_duration("2020-01", "2020-12") == "1 yr"
    assert format_duration("2020-01", None, today=date(2020, 3, 15)) == "3 mo"
    assert format_duration("2020", "2021") == ""
    assert format_duration(None, "2021-01") == ""


def test_display_url_strips_scheme():
    assert display_url("https://www.github.com/example/") == "github.com/example"
    assert display_url("mailto:ada@example.com") == "ada@example.com"
