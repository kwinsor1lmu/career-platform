def test_database_outage_still_returns_profile(outage_client):
    for path in ("/", "/resume"):
        response = outage_client.get(path)
        assert response.status_code == 200
        assert "Ada Example" in response.text
