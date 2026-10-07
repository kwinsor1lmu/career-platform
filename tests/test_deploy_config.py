import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_railway_builds_dockerfile_and_gates_on_health():
    config = tomllib.loads((ROOT / "railway.toml").read_text(encoding="utf-8"))

    assert config["build"]["builder"] == "DOCKERFILE"
    assert config["deploy"]["healthcheckPath"] == "/health"
    assert "startCommand" not in config["deploy"], "the Dockerfile CMD (scripts/dev.sh) must stay the start command"


def test_container_trusts_proxy_forwarded_headers():
    # Without this, url_for() emits http:// asset URLs behind Railway's HTTPS edge and browsers block the stylesheet.
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")

    assert 'FORWARDED_ALLOW_IPS="*"' in dockerfile
