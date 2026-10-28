"""Test endpoint reviews: otorisasi, kepemilikan, validasi, moderasi.

Repository di-stub, jadi tes ini tidak menyentuh database.
"""
from __future__ import annotations

from app.reviews import repository as review_repository

OWNER_ID = "11111111-1111-1111-1111-111111111111"  # user_auth
ADMIN_ID = "22222222-2222-2222-2222-222222222222"  # admin_auth
OTHER_ID = "33333333-3333-3333-3333-333333333333"  # user lain

MOVIE = {
    "id": 1,
    "title": "Inception",
    "release_year": 2010,
    "genre": "Sci-Fi",
    "director": "Christopher Nolan",
    "overview": "Mimpi di dalam mimpi",
    "poster_url": "",
    "rating": 8.8,
    "media_type": "movie",
}

REVIEW = {
    "id": 7,
    "user_id": OWNER_ID,
    "movie_id": 1,
    "rating": 9.5,
    "content": "Sangat bagus",
    "is_hidden": False,
    "created_at": "2026-10-28T10:00:00",
    "updated_at": "2026-10-28T10:00:00",
    "user_name": "Zahir",
    "movie_title": "Inception",
}


def test_daftar_ulasan_tanpa_token_401(client):
    assert client.get("/reviews/movie/1").status_code == 401
    assert client.post("/reviews", json={"movie_id": 1, "rating": 8, "content": "x"}).status_code == 401


def test_daftar_ulasan_film_ok(client, user_auth, monkeypatch):
    monkeypatch.setattr("app.movies.repository.find_by_id", lambda i: MOVIE)
    monkeypatch.setattr(review_repository, "find_by_movie", lambda movie_id, pagination=None: ([REVIEW], 1))

    response = client.get("/reviews/movie/1", headers=user_auth)

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1 and body["data"][0]["user_name"] == "Zahir"


def test_daftar_ulasan_film_tidak_ada_404(client, user_auth, monkeypatch):
    monkeypatch.setattr("app.movies.repository.find_by_id", lambda i: None)

    response = client.get("/reviews/movie/999", headers=user_auth)

    assert response.status_code == 404
    assert response.json()["data"]["errorCode"] == "NOT_FOUND"


def test_tambah_ulasan_201(client, user_auth, monkeypatch):
    monkeypatch.setattr("app.movies.repository.find_by_id", lambda i: MOVIE)
    monkeypatch.setattr(review_repository, "find_by_user_and_movie", lambda u, m: None)
    monkeypatch.setattr(review_repository, "create", lambda payload: {"id": 7})
    monkeypatch.setattr(review_repository, "find_by_id", lambda review_id: REVIEW)

    response = client.post("/reviews", json={"movie_id": 1, "rating": 9.5, "content": "Bagus"}, headers=user_auth)

    assert response.status_code == 201
    assert response.json()["data"]["id"] == 7


def test_ulasan_ganda_409(client, user_auth, monkeypatch):
    monkeypatch.setattr("app.movies.repository.find_by_id", lambda i: MOVIE)
    monkeypatch.setattr(review_repository, "find_by_user_and_movie", lambda u, m: REVIEW)

    response = client.post("/reviews", json={"movie_id": 1, "rating": 9.5, "content": "Lagi"}, headers=user_auth)

    assert response.status_code == 409
    assert response.json()["data"]["errorCode"] == "CONFLICT"


def test_rating_di_luar_rentang_422(client, user_auth):
    for invalid in (11, -1):
        response = client.post(
            "/reviews", json={"movie_id": 1, "rating": invalid, "content": "x"}, headers=user_auth
        )
        assert response.status_code == 422, invalid


def test_isi_ulasan_kosong_422(client, user_auth):
    response = client.post("/reviews", json={"movie_id": 1, "rating": 8, "content": ""}, headers=user_auth)

    assert response.status_code == 422
    assert response.json()["data"]["errorCode"] == "VALIDATION_ERROR"


def test_ubah_ulasan_orang_lain_403(client, user_auth, monkeypatch):
    monkeypatch.setattr(review_repository, "find_by_id", lambda review_id: {**REVIEW, "user_id": OTHER_ID})

    response = client.put("/reviews/7", json={"rating": 1}, headers=user_auth)

    assert response.status_code == 403
    assert response.json()["data"]["errorCode"] == "FORBIDDEN"


def test_ubah_ulasan_sendiri_200_dan_hanya_field_terkirim(client, user_auth, monkeypatch):
    captured = {}

    monkeypatch.setattr(review_repository, "find_by_id", lambda review_id: REVIEW)

    def fake_update(review_id, payload):
        captured.update(payload)
        return {"id": review_id}

    monkeypatch.setattr(review_repository, "update", fake_update)

    response = client.put("/reviews/7", json={"rating": 6.5}, headers=user_auth)

    assert response.status_code == 200
    assert captured == {"rating": 6.5}  # `content` tidak ikut terkirim -> tidak tertimpa None


def test_ubah_tanpa_field_400(client, user_auth, monkeypatch):
    monkeypatch.setattr(review_repository, "find_by_id", lambda review_id: REVIEW)

    response = client.put("/reviews/7", json={}, headers=user_auth)

    assert response.status_code == 400


def test_hapus_ulasan_sendiri_200(client, user_auth, monkeypatch):
    deleted = []

    monkeypatch.setattr(review_repository, "find_by_id", lambda review_id: REVIEW)
    monkeypatch.setattr(review_repository, "delete", lambda review_id: deleted.append(review_id) or {"id": review_id})

    response = client.delete("/reviews/7", headers=user_auth)

    assert response.status_code == 200
    assert deleted == [7]


def test_ulasan_tidak_ada_404(client, user_auth, monkeypatch):
    monkeypatch.setattr(review_repository, "find_by_id", lambda review_id: None)

    assert client.delete("/reviews/999", headers=user_auth).status_code == 404


def test_ulasan_saya_khusus_pemilik(client, user_auth, monkeypatch):
    captured = {}

    def fake_find_all_by_user(user_id, pagination=None):
        captured["user_id"] = user_id
        return ([REVIEW], 1)

    monkeypatch.setattr(review_repository, "find_all_by_user", fake_find_all_by_user)

    response = client.get("/reviews/me", headers=user_auth)

    assert response.status_code == 200
    assert captured["user_id"] == OWNER_ID  # mengambil dari token, bukan dari query


def test_moderasi_hanya_admin(client, user_auth):
    assert client.get("/reviews/moderation", headers=user_auth).status_code == 403
    assert client.patch("/reviews/7/moderation", json={"is_hidden": True}, headers=user_auth).status_code == 403


def test_moderasi_menyembunyikan_ulasan(client, admin_auth, monkeypatch):
    state = {}

    monkeypatch.setattr(review_repository, "find_by_id", lambda review_id: {**REVIEW, **state})

    def fake_set_hidden(review_id, is_hidden):
        state["is_hidden"] = is_hidden
        return {"id": review_id}

    monkeypatch.setattr(review_repository, "set_hidden", fake_set_hidden)

    response = client.patch("/reviews/7/moderation", json={"is_hidden": True}, headers=admin_auth)

    assert response.status_code == 200
    assert state["is_hidden"] is True
    assert response.json()["data"]["is_hidden"] is True


def test_daftar_moderasi_admin_ok(client, admin_auth, monkeypatch):
    monkeypatch.setattr(review_repository, "find_all_for_moderation", lambda pagination=None: ([REVIEW], 1))

    response = client.get("/reviews/moderation", headers=admin_auth)

    assert response.status_code == 200
    assert response.json()["total"] == 1
