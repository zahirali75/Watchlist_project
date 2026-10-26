"""Bulk TMDB seeder using a direct PostgreSQL connection (no Supabase SDK)."""
from __future__ import annotations

import sys
from pathlib import Path

import requests
from sqlalchemy import text

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import get_settings  # noqa: E402
from app.db.session import get_connection  # noqa: E402

TMDB_POPULAR_URL = "https://api.themoviedb.org/3/movie/popular"
POSTER_BASE_URL = "https://image.tmdb.org/t/p/w500"


def fetch_popular_movies(api_key: str, page: int = 1, limit: int = 20) -> list[dict]:
    response = requests.get(
        TMDB_POPULAR_URL,
        params={"api_key": api_key, "language": "en-US", "page": page},
        timeout=30,
    )
    response.raise_for_status()
    results = response.json().get("results", [])[:limit]
    movies = []
    for movie in results:
        release_year = (movie.get("release_date") or "")[:4]
        movies.append({
            "title": movie.get("title") or "Untitled",
            "release_year": int(release_year) if release_year.isdigit() else None,
            "genre": "",  # TMDB popular endpoint returns genre IDs, not genre names.
            "director": "",  # Requires the movie credits endpoint.
            "overview": movie.get("overview") or "",
            "poster_url": f"{POSTER_BASE_URL}{movie['poster_path']}" if movie.get("poster_path") else "",
            "rating": round(float(movie.get("vote_average") or 0), 1),
        })
    return movies


def seed(page: int = 1, limit: int = 20) -> int:
    settings = get_settings()
    if not settings.TMDB_API_KEY:
        raise RuntimeError("TMDB_API_KEY belum diisi di .env")
    movies = fetch_popular_movies(settings.TMDB_API_KEY, page=page, limit=limit)
    if not movies:
        print("Tidak ada film yang diterima dari TMDB.")
        return 0

    with get_connection(write=True) as connection:
        connection.execute(
            text("""INSERT INTO movies
                (title, release_year, genre, director, overview, poster_url, rating)
                VALUES (:title, :release_year, :genre, :director, :overview, :poster_url, :rating)"""),
            movies,
        )
    inserted = len(movies)
    print(f"{inserted} film berhasil dimasukkan ke PostgreSQL.")
    return inserted


if __name__ == "__main__":
    seed()
