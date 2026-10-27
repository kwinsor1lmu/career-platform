def test_database_outage_keeps_profile_and_returns_503(outage_client):
    for path in ("/", "/resume"):
        response = outage_client.get(path)
        assert response.status_code == 503
        assert "Ada Example" in response.text
        assert "Projects temporarily unavailable" in response.text
