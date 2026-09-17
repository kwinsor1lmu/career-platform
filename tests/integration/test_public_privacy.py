def test_private_source_content_is_absent_from_html_and_fallback(app_client):
    fallback_path = app_client.app.state.settings.fallback_path

    for path in ("/", "/resume"):
        response = app_client.get(path)
        assert response.status_code == 200
        assert "private fixture text" not in response.text

    assert "private fixture text" not in fallback_path.read_text(encoding="utf-8")
