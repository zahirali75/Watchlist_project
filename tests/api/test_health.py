from __future__ import annotations


def test_health_check(client):
    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["app"]


def test_root_redirect_ke_docs(client):
    response = client.get("/", follow_redirects=False)
    assert response.status_code in (307, 308)
    assert response.headers["location"] == "/docs"


def test_readiness_db_ok(client, monkeypatch):
    from app.health import repository

    monkeypatch.setattr(repository, "ping", lambda: True)
    assert client.get("/health/db").json()["data"]["database"] == "ok"


def test_readiness_db_gagal_502(client, monkeypatch):
    from app.health import repository

    monkeypatch.setattr(repository, "ping", lambda: False)
    assert client.get("/health/db").status_code == 502
