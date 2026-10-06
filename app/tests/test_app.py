import pytest

from app import create_app


@pytest.fixture
def client(tmp_path):
    app = create_app(str(tmp_path / "test.db"))
    return app.test_client()


def test_health(client):
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.get_json()["status"] == "ok"


def test_shorten_and_redirect(client):
    r = client.post("/api/shorten", json={"url": "https://example.com"})
    assert r.status_code == 201
    code = r.get_json()["code"]
    r = client.get(f"/{code}")
    assert r.status_code == 302
    assert r.headers["Location"] == "https://example.com"
    assert client.get(f"/api/stats/{code}").get_json()["hits"] == 1


def test_invalid_url(client):
    r = client.post("/api/shorten", json={"url": "not-a-url"})
    assert r.status_code == 400


def test_unknown_code(client):
    assert client.get("/nope123").status_code == 404
