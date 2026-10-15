from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def _client(app_client, measurement_id: str) -> TestClient:
    settings = app_client.app.state.settings
    return TestClient(
        create_app(
            Settings(
                environment="test",
                database_url="sqlite://",
                fallback_path=settings.fallback_path,
                ga_measurement_id=measurement_id,
            )
        )
    )


def test_pages_have_no_analytics_or_banner_without_a_measurement_id(app_client):
    for path in ("/", "/privacy"):
        html = app_client.get(path).text
        assert "data-ga-id" not in html
        assert "googletagmanager.com/gtag/js" not in html
        assert "consent.js" not in html
        assert "data-consent-banner" not in html


def test_analytics_waits_for_consent_when_configured(app_client):
    client = _client(app_client, "G-TEST123")

    for path in ("/", "/resume", "/privacy"):
        html = client.get(path).text
        assert 'data-ga-id="G-TEST123"' in html
        assert "consent.js" in html
        # gtag.js is only injected by consent.js after Accept, never by the page itself.
        assert "googletagmanager.com/gtag/js" not in html
        assert "data-consent-banner" in html and "hidden" in html
        assert "data-consent-accept" in html and "data-consent-reject" in html
        assert "data-consent-open" in html


def test_consent_script_defaults_to_denied_and_grants_only_analytics():
    js = (Path(__file__).resolve().parents[2] / "app" / "static" / "consent.js").read_text(encoding="utf-8")

    assert "gtag(\"consent\", \"default\"" in js
    for signal in ("analytics_storage", "ad_storage", "ad_user_data", "ad_personalization"):
        assert f'{signal}: "denied"' in js
    assert 'gtag("consent", "update", { analytics_storage: "granted" })' in js
    assert "googletagmanager.com/gtag/js?id=" in js
