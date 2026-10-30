"""Test endpoint movies (repository di-stub, tidak menyentuh database)."""
from __future__ import annotations

from app.movies import repository as movie_repository

MOVIE = {
    "id": 1,
    "title": "Inception",
    "release_year": 2010,
    "genre": "Sci-Fi",
    "director": "Christopher Nolan",
    "overview": "Mimpi di dalam mimpi",
    "poster_url": "http://example.test/inception.jpg",
    "rating": 8.8,
}


def _found(response):
    response.data = [MOVIE]
    response.count = 1
    return response


def test_list_movies_publik(client, monkeypatch):
    monkeypatch.setattr(movie_repository, "find_all", lambda **kwargs: ([MOVIE], 1))

    response = client.get("/movies")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True and body["total"] == 1
    assert body["data"][0]["title"] == "Inception"


def test_detail_movies_404(client, monkeypatch):
    monkeypatch.setattr(movie_repository, "find_by_id", lambda movie_id: None)

    response = client.get("/movies/999")

    assert response.status_code == 404
    assert response.json()["data"]["errorCode"] == "NOT_FOUND"


def test_tambah_film_tanpa_token_401(client):
    response = client.post("/movies", json=MOVIE)

    assert response.status_code == 401
    assert response.json()["success"] is False


def test_tambah_film_dengan_token_user_biasa_403(client, user_auth):
    response = client.post("/movies", json=MOVIE, headers=user_auth)

    assert response.status_code == 403
    assert response.json()["data"]["errorCode"] == "FORBIDDEN"


def test_tambah_film_dengan_admin_201_dan_tercatat_di_audit(client, admin_auth, monkeypatch):
    audit_calls = []

    monkeypatch.setattr(movie_repository, "create", lambda payload: MOVIE)
    monkeypatch.setattr(
        "app.movies.service.audit_log_service.create_audit_log",
        lambda payload, actor_id=None: audit_calls.append((payload, actor_id)),
    )

    response = client.post("/movies", json=MOVIE, headers=admin_auth)

    assert response.status_code == 201
    assert response.json()["data"]["id"] == 1
    assert len(audit_calls) == 1
    assert audit_calls[0][0].type == "MOVIE_CREATE"


def test_body_tidak_valid_422_envelope_seragam(client, admin_auth):
    response = client.post("/movies", json={"title": "Tanpa tahun"}, headers=admin_auth)

    assert response.status_code == 422
    body = response.json()
    assert body["success"] is False
    assert body["data"]["errorCode"] == "VALIDATION_ERROR"


def test_list_movies_meneruskan_parameter_sort(client, monkeypatch):
    captured = {}

    def fake_find_all(**kwargs):
        captured.update(kwargs)
        return [MOVIE], 1

    monkeypatch.setattr(movie_repository, "find_all", fake_find_all)

    assert client.get("/movies?sort=rating_desc").status_code == 200
    assert captured["sort"] == "rating_desc"
    # Tanpa parameter -> urutan lama (id).
    client.get("/movies")
    assert captured["sort"] == "id"


def test_list_movies_sort_tidak_valid_422(client):
    assert client.get("/movies?sort=DROP_TABLE").status_code == 422
