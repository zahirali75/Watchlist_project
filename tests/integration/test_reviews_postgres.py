"""Alur reviews + media_type end-to-end ke PostgreSQL asli (tanpa mock).

Yang dibuktikan di sini (tidak bisa dibuktikan oleh tes dengan repository
di-stub):
- unique index `(user_id, movie_id)` benar-benar menolak ulasan ganda;
- `media_type` tersimpan apa adanya dan penyaringan `?media_type=` bekerja;
- moderasi admin menyembunyikan ulasan dari daftar publik, tetapi pemiliknya
  masih melihatnya di /reviews/me;
- menghapus film ikut membersihkan ulasannya (ON DELETE CASCADE).
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.core.rate_limit import login_throttle
from app.main import app

MOVIE = {
    "title": "Inception",
    "release_year": 2010,
    "genre": "Sci-Fi",
    "director": "Christopher Nolan",
    "overview": "Mimpi di dalam mimpi",
    "poster_url": "",
    "rating": 8.8,
    "media_type": "movie",
}


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


def _admin(api, email="adm@x.com"):
    uid, auth = _register(api, email)
    return uid, auth


def _make_admin(api, sql, uid):
    sql.execute("UPDATE users SET role='admin' WHERE id=%s", (uid,))


def _seed_movie(api, auth, **overrides):
    payload = {**MOVIE, **overrides}
    r = api.post("/movies", json=payload, headers=auth)
    assert r.status_code == 201, r.text
    return r.json()["data"]["id"]


def test_media_type_tersimpan_dan_menyaring(api, sql):
    uid, auth = _admin(api)
    _make_admin(api, sql, uid)
    mid = _seed_movie(api, auth, media_type="movie")
    _seed_movie(api, auth, title="Breaking Bad", media_type="series")

    assert api.get(f"/movies/{mid}").json()["data"]["media_type"] == "movie"
    assert api.get("/movies", params={"media_type": "movie"}).json()["total"] == 1
    assert api.get("/movies", params={"media_type": "series"}).json()["total"] == 1
    # nilai di luar enum ditolak, bukan diabaikan diam-diam
    assert api.get("/movies", params={"media_type": "anime"}).status_code == 422
    # parameter lama (tanpa media_type) tetap mengembalikan semuanya
    assert api.get("/movies").json()["total"] == 2


def test_media_type_default_movie_untuk_data_lama(api, sql):
    uid, auth = _admin(api)
    _make_admin(api, sql, uid)
    sql.execute(
        "INSERT INTO movies (title, release_year, genre, director, overview, poster_url, rating) "
        "VALUES ('Film Lama', 2001, 'Drama', 'X', 'o', '', 7.0)"
    )
    row = sql.execute("SELECT media_type FROM movies WHERE title='Film Lama'").fetchone()

    assert row[0] == "movie"


def test_alur_ulasan_lengkap(api, sql):
    uid, auth = _admin(api)
    _make_admin(api, sql, uid)
    mid = _seed_movie(api, auth)

    created = api.post("/reviews", json={"movie_id": mid, "rating": 9.0, "content": "Keren"}, headers=auth)
    assert created.status_code == 201, created.text
    rid = created.json()["data"]["id"]
    assert created.json()["data"]["user_name"] == "adm"  # nama penulis ikut (JOIN users)

    # satu ulasan per film per pengguna: percobaan kedua ditolak
    assert api.post("/reviews", json={"movie_id": mid, "rating": 5, "content": "lagi"}, headers=auth).status_code == 409

    listed = api.get(f"/reviews/movie/{mid}", headers=auth).json()
    assert listed["total"] == 1 and listed["data"][0]["movie_title"] == "Inception"

    assert api.get("/reviews/me", headers=auth).json()["total"] == 1
    assert api.get(f"/reviews/{rid}", headers=auth).json()["data"]["content"] == "Keren"

    updated = api.put(f"/reviews/{rid}", json={"rating": 6.5}, headers=auth)
    assert updated.status_code == 200
    assert updated.json()["data"]["rating"] == 6.5
    assert updated.json()["data"]["content"] == "Keren"  # tidak tertimpa

    assert api.delete(f"/reviews/{rid}", headers=auth).status_code == 200
    assert api.get(f"/reviews/{rid}", headers=auth).status_code == 404


def test_ulasan_antar_pengguna_terisolasi(api, sql):
    uid, auth = _admin(api)
    _make_admin(api, sql, uid)
    mid = _seed_movie(api, auth)
    _, other = _register(api, "b@x.com")

    rid = api.post("/reviews", json={"movie_id": mid, "rating": 7, "content": "punyaku"}, headers=auth).json()["data"]["id"]

    assert api.get("/reviews/me", headers=other).json()["total"] == 0
    assert api.put(f"/reviews/{rid}", json={"rating": 1}, headers=other).status_code == 403
    assert api.delete(f"/reviews/{rid}", headers=other).status_code == 403


def test_moderasi_admin_menyembunyikan_dari_publik(api, sql):
    uid, auth = _admin(api)
    _make_admin(api, sql, uid)
    mid = _seed_movie(api, auth)
    _, viewer = _register(api, "b@x.com")
    rid = api.post("/reviews", json={"movie_id": mid, "rating": 7, "content": "isi"}, headers=auth).json()["data"]["id"]

    assert api.get("/reviews/moderation", headers=auth).json()["total"] == 1
    assert api.get("/reviews/moderation", headers=viewer).status_code == 403  # user biasa

    hidden = api.patch(f"/reviews/{rid}/moderation", json={"is_hidden": True}, headers=auth)
    assert hidden.status_code == 200 and hidden.json()["data"]["is_hidden"] is True

    assert api.get(f"/reviews/movie/{mid}", headers=viewer).json()["total"] == 0  # hilang dari publik
    assert api.get("/reviews/me", headers=auth).json()["total"] == 1  # pemilik masih melihat miliknya
    assert api.get("/reviews/moderation", headers=auth).json()["data"][0]["is_hidden"] is True


def test_hapus_film_ikut_menghapus_ulasan(api, sql):
    uid, auth = _admin(api)
    _make_admin(api, sql, uid)
    mid = _seed_movie(api, auth)
    api.post("/reviews", json={"movie_id": mid, "rating": 7, "content": "isi"}, headers=auth)
    assert api.get(f"/reviews/movie/{mid}", headers=auth).json()["total"] == 1

    assert api.delete(f"/movies/{mid}", headers=auth).status_code == 200
    assert sql.execute("SELECT count(*) FROM reviews").fetchone()[0] == 0


def test_ulasan_di_film_tidak_ada_404(api, sql):
    uid, auth = _admin(api)
    _make_admin(api, sql, uid)

    assert api.get("/reviews/movie/99999", headers=auth).status_code == 404
    assert api.post("/reviews", json={"movie_id": 99999, "rating": 8, "content": "x"}, headers=auth).status_code == 404
