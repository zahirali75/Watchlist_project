"""Seeder TMDB -> Supabase.

Dipindah dari root ke scripts/. Perubahan: baca kredensial lewat app.core.config
yang tervalidasi, dan insert-nya lewat repository (bukan query mentah tersebar).
"""
from __future__ import annotations

import sys
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import get_settings  # noqa: E402
from app.db.client import get_supabase  # noqa: E402
from app.core.constants import Tables  # noqa: E402

TMDB_POPULAR_URL = "https://api.themoviedb.org/3/movie/popular"
POSTER_BASE_URL = "https://image.tmdb.org/t/p/w500"


def fetch_popular_movies(api_key: str, page: int = 1, limit: int = 20) -> list[dict]:
    response = requests.get(
        TMDB_POPULAR_URL,
        params={"api_key": api_key, "language": "en-US", "page": page},
        timeout=30,
    )
    if response.status_code != 200:
        print(f"Gagal memanggil TMDB API: {response.status_code}")
        return []

    results = response.json().get("results", [])[:limit]
    return [
        {
            "title": m.get("title"),
            "release_year": int((m.get("release_date") or "0000")[:4] or 0) or None,
            "genre": "",  # butuh /genre/movie/list untuk nama genre
            "director": "",  # butuh /movie/{id}/credits
            "overview": m.get("overview"),
            "poster_url": f"{POSTER_BASE_URL}{m.get('poster_path')}" if m.get("poster_path") else "",
            "rating": m.get("vote_average"),
        }
        for m in results
    ]


def seed(page: int = 1, limit: int = 20) -> int:
    settings = get_settings()
    if not settings.TMDB_API_KEY:
        print("TMDB_API_KEY belum diisi di .env")
        return 0

    movies = fetch_popular_movies(settings.TMDB_API_KEY, page=page, limit=limit)
    if not movies:
        return 0

    response = get_supabase().table(Tables.MOVIES).insert(movies).execute()
    inserted = len(response.data or [])
    print(f"{inserted} film berhasil dimasukkan ke Supabase")
    return inserted


if __name__ == "__main__":
    seed()
