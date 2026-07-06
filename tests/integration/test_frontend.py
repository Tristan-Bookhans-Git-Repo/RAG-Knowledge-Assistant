from httpx import AsyncClient


async def test_index_returns_200_with_nav_bar(client: AsyncClient) -> None:
    response = await client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "navbar" in response.text
    assert 'href="/dashboard"' in response.text
    assert 'href="/login"' in response.text


async def test_static_css_is_served(client: AsyncClient) -> None:
    response = await client.get("/static/css/style.css")
    assert response.status_code == 200
    assert "text/css" in response.headers["content-type"]


async def test_static_js_is_served(client: AsyncClient) -> None:
    response = await client.get("/static/js/main.js")
    assert response.status_code == 200
