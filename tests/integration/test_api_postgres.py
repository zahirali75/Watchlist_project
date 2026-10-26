"""Alur API end-to-end ke PostgreSQL asli (tanpa mock repository)."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core.rate_limit import login_throttle
from app.main import app


@pytest.fixture
def api(clean_tables):
    login_throttle.clear_all()
    with TestClient(app) as c:
        yield c


def _register(api, email, password="rahasia123"):
    r = api.post("/auth/register", json={"email": email, "password": password, "name": email.split("@")[0]})
    assert r.status_code == 201, r.text
    body = r.json()
    return body["userId"], {"Authorization": f"Bearer {body['accessToken']}"}


MOVIE = {"title": "Inception", "release_year": 2010, "genre": "Sci-Fi", "director": "N", "overview": "o", "poster_url": "", "rating": 8.8}


def test_readiness_db(api):
    assert api.get("/health/db").status_code == 200


def test_auth_alur_lengkap(api):
    _register(api, "Budi@x.com")
    assert api.post("/auth/register", json={"email": "budi@x.com", "password": "rahasia123"}).status_code == 409
    assert api.post("/auth/login", json={"email": "BUDI@x.com", "password": "rahasia123"}).status_code == 200
    assert api.post("/auth/login", json={"email": "budi@x.com", "password": "salahsalah"}).status_code == 401


def test_rbac_dan_role_dicabut_langsung_berlaku(api, sql):
    uid, auth = _register(api, "adm@x.com")
    assert api.get("/users", headers=auth).status_code == 403
    sql.execute("UPDATE users SET role='admin' WHERE id=%s", (uid,))
    assert api.get("/users", headers=auth).status_code == 200  # token LAMA langsung dapat role baru dari DB
    sql.execute("UPDATE users SET role='user' WHERE id=%s", (uid,))
    assert api.get("/users", headers=auth).status_code == 403  # dicabut -> token lama ikut kehilangan hak
    sql.execute("DELETE FROM users WHERE id=%s", (uid,))
    assert api.get("/watchlists/me", headers=auth).status_code == 401  # user dihapus -> token mati


def test_crud_film_pagination_filter_dan_audit(api, sql):
    uid, auth = _register(api, "adm@x.com")
    sql.execute("UPDATE users SET role='admin' WHERE id=%s", (uid,))
    created = api.post("/movies", json=MOVIE, headers=auth)
    assert created.status_code == 201
    mid = created.json()["data"]["id"]
    api.post("/movies", json={**MOVIE, "title": "Up", "genre": "Animation"}, headers=auth)
    assert api.get("/movies", params={"search": "incep"}).json()["total"] == 1
    page = api.get("/movies", params={"limit": 1, "page": 2}).json()
    assert page["count"] == 1 and page["total"] == 2
    assert api.put(f"/movies/{mid}", json={**MOVIE, "rating": 9.0}, headers=auth).status_code == 200
    assert api.post("/movies", json={**MOVIE, "rating": 11}, headers=auth).status_code == 422
    assert api.delete(f"/movies/{mid}", headers=auth).status_code == 200
    assert api.get(f"/movies/{mid}").status_code == 404
    types = {l["type"] for l in api.get("/audit-logs", headers=auth).json()["data"]}
    assert {"USER_REGISTER", "MOVIE_CREATE", "MOVIE_UPDATE", "MOVIE_DELETE"} <= types


def test_watchlist_ownership_duplikat_stats_dan_join(api, sql):
    admin_id, admin = _register(api, "adm@x.com")
    sql.execute("UPDATE users SET role='admin' WHERE id=%s", (admin_id,))
    mid = api.post("/movies", json=MOVIE, headers=admin).json()["data"]["id"]
    a_id, a = _register(api, "a@x.com")
    _, b = _register(api, "b@x.com")

    item = api.post("/watchlists", json={"movie_id": mid, "status": "watching", "notes": "n"}, headers=a)
    assert item.status_code == 201
    wid = item.json()["data"]["id"]
    assert api.post("/watchlists", json={"movie_id": mid}, headers=a).status_code == 409
    assert api.post("/watchlists", json={"movie_id": 99999}, headers=a).status_code == 404

    mine = api.get("/watchlists/me", headers=a).json()
    assert mine["total"] == 1 and mine["data"][0]["movies"]["title"] == "Inception"
    assert api.get("/watchlists/me", headers=b).json()["total"] == 0

    # user B tidak boleh menyentuh item milik A
    assert api.put(f"/watchlists/{wid}", json={"status": "watched"}, headers=b).status_code == 403
    assert api.delete(f"/watchlists/{wid}", headers=b).status_code == 403
    assert api.get(f"/watchlists/{a_id}", headers=b).status_code == 403

    assert api.put(f"/watchlists/{wid}", json={"status": "watched"}, headers=a).status_code == 200
    assert api.put(f"/watchlists/{wid}", json={"notes": None}, headers=a).json()["data"]["notes"] is None
    stats = api.get("/watchlists/me/stats", headers=a).json()  # bentuk datar: success + field statistik
    assert stats == {"success": True, "total": 1, "watched": 1, "watching": 0, "wantToWatch": 0}
    assert api.delete(f"/watchlists/{wid}", headers=a).status_code == 200


def test_error_database_tidak_bocor_ke_klien(api, sql):
    uid, auth = _register(api, "adm@x.com")
    sql.execute("UPDATE users SET role='admin' WHERE id=%s", (uid,))
    r = api.get("/users/bukan-uuid", headers=auth)  # Postgres menolak sintaks UUID
    assert r.status_code in (400, 404, 502)
    text = r.text.lower()
    assert "invalid input syntax" not in text and "psycopg" not in text and "select " not in text
    assert api.get("/users/44444444-4444-4444-4444-444444444444/stats", headers=auth).status_code == 404
