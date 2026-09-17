def test_resume_page_has_semantic_structure_metadata_and_links(app_client):
    response = app_client.get("/")
    html = response.text

    assert response.status_code == 200
    assert "<main" in html
    assert "Skip to main content" in html
    assert "<h1" in html
    assert html.count("<h2") >= 4
    assert 'name="description"' in html
    assert "<title>" in html and "Ada Example" in html
    assert 'href="#main-content"' in html
    assert 'https://example.com' in html
    assert 'rel="me"' in html

    css = app_client.get("/static/styles.css").text
    assert "a:focus-visible" in css
    assert "outline: 3px solid" in css
