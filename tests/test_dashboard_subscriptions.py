from fastapi.testclient import TestClient

from app.main import app


def test_dashboard_create_subscription(temp_db):
    client = TestClient(app)
    client.post("/login", data={"admin_key": "dev-admin-key"}, follow_redirects=False)

    response = client.post(
        "/subscriptions",
        data={
            "url": "https://example.com/hook",
            "event_filter": "order.*",
            "secret": "top-secret",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/"

    home = client.get("/")
    assert home.status_code == 200
    assert "https://example.com/hook" in home.text
    assert "order.*" in home.text


def test_dashboard_create_subscription_invalid_url(temp_db):
    client = TestClient(app)
    client.post("/login", data={"admin_key": "dev-admin-key"}, follow_redirects=False)

    response = client.post(
        "/subscriptions",
        data={"url": "not-a-url", "event_filter": "*"},
    )
    assert response.status_code == 400
    assert "Invalid URL" in response.text


def test_dashboard_create_subscription_requires_login(temp_db):
    client = TestClient(app)
    response = client.post(
        "/subscriptions",
        data={"url": "https://example.com/hook", "event_filter": "*"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/login"
