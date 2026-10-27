def test_privacy_page_renders_without_the_database(app_client):
    response = app_client.get("/privacy")
    html = response.text

    assert response.status_code == 200
    assert "<title>Privacy | Ada Example</title>" in html
    assert "<h1" in html and "Privacy" in html
    assert 'href="#main-content"' in html
    assert 'rel="canonical" href="http://testserver/privacy"' in html
    assert '"@type": "Person"' not in html


def test_privacy_page_names_what_analytics_collects_and_the_real_choices(app_client):
    html = app_client.get("/privacy").text

    assert "Google Analytics" in html
    assert "_ga" in html
    assert "Global Privacy Control" in html
    assert "tools.google.com/dlpage/gaoptout" in html


def test_footer_links_to_privacy_page_from_every_page(app_client):
    for path in ("/", "/resume", "/privacy"):
        html = app_client.get(path).text
        assert '<footer class="site-footer">' in html
        assert 'href="http://testserver/privacy"' in html


def test_privacy_page_names_the_current_host_and_cloudflare_redirect(app_client):
    html = app_client.get("/privacy").text

    assert "<strong>Railway</strong> hosts the site" in html
    assert "Microsoft Azure" not in html
    assert "www.kenwinsor.xyz" in html
