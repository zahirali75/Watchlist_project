import os
import requests
from dotenv import load_dotenv
from supabase import create_client

# Membaca konfigurasi dari file .env lokal (aman, tidak di-push ke git)
load_dotenv()

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not all([TMDB_API_KEY, SUPABASE_URL, SUPABASE_KEY]):
    raise ValueError("Pastikan TMDB_API_KEY, SUPABASE_URL, dan SUPABASE_KEY sudah diisi di file .env!")

# Inisialisasi client Supabase
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def seed_movies(page=1, limit=20):
    """
    Mengambil data film populer dari TMDB API dan menyimpannya ke database Supabase.
    """
    url = f"https://api.themoviedb.org/3/movie/popular?api_key={TMDB_API_KEY}&language=en-US&page={page}"
    response = requests.get(url)
    
    if response.status_code != 200:
        print(f"Gagal memanggil TMDB API: {response.status_code}")
        return

    movies = response.json().get('results', [])[:limit]
    print(f"--- Mulai Seeding {len(movies)} Film dari Halaman {page} ---")

    for movie in movies:
        data = {
            "title": movie.get('title'),
            "release_year": int(movie['release_date'][:4]) if movie.get('release_date') else None,
            "genre": "General",
            "director": "Unknown",
            "overview": movie.get('overview'),
            "poster_url": f"https://image.tmdb.org/t/p/w500{movie.get('poster_path')}" if movie.get('poster_path') else None,
            "rating": round(float(movie.get('vote_average', 0.0)), 1)
        }
        
        try:
            supabase.table("movies").insert(data).execute()
            print(f"✅ Berhasil menambahkan: {data['title']}")
        except Exception as e:
            print(f"⚠️ Gagal menambahkan {data['title']}: {e}")

    print("--- Selesai Seeding Data ---")

if __name__ == "__main__":
    # Default: Ambil 20 film dari halaman 1
    seed_movies(page=1, limit=20)
