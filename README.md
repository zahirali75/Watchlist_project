# 🎬 CineList - Movie Watchlist Web Application

> Proyek Mata Kuliah: **Web Application Development**  
> Tech Stack: **React.js** (Frontend), **FastAPI** (Backend), **Supabase PostgreSQL** (Database).

---

## 📋 Ringkasan Proyek

**CineList** adalah aplikasi web untuk mengelola daftar tontonan film (*watchlist*) pribadi. Pengguna dapat mencari katalog film, melihat detail, menambahkan film ke watchlist dengan status tertentu (*Want to Watch*, *Watching*, *Watched*), serta melihat statistik watchlist.

---

## 🗄️ Database Architecture

Aplikasi ini menggunakan skema ternormalisasi pada PostgreSQL (Supabase):

1. **`users`**: Menyimpan akun pengguna (menggunakan `UUID` untuk keamanan ID).
2. **`movies`**: Menyimpan katalog film (`SERIAL` auto-increment ID).
3. **`watchlists`**: Tabel relasi Many-to-Many antara pengguna dan film, dilengkapi batasan `UNIQUE(user_id, movie_id)` dan `CHECK status`.

File skema lengkap tersedia di: [`schema.sql`](schema.sql).

---

## 🚀 Setup & Data Seeding

### 1. Prasyarat
* Python 3.10+
* Akun [Supabase](https://supabase.com)
* API Key gratis dari [TMDB](https://www.themoviedb.org/settings/api)

### 2. Instalasi Dependencies
```bash
pip install -r requirements.txt
```

### 3. Konfigurasi Environment Variables
Salin file `.env.example` menjadi `.env`:
```bash
cp .env.example .env
```
Isi nilai variabel berikut di `.env`:
* `TMDB_API_KEY`: API Key TMDB kamu.
* `SUPABASE_URL`: URL Project Supabase.
* `SUPABASE_KEY`: Secret / Service Role Key Supabase.

### 4. Eksekusi Seeding Data
Jalankan script Python seeder untuk menarik film populer secara otomatis ke database Supabase:
```bash
python seed_movies.py
```

---

## 📁 Struktur Repositori

```text
cinelist/
├── .env.example        # Template konfigurasi environment (aman di-commit)
├── .gitignore          # File penyaring git (mencegah .env bocor ke publik)
├── requirements.txt    # Pustaka Python yang dibutuhkan
├── schema.sql          # DDL Schema database PostgreSQL / Supabase
├── seed_movies.py      # Script otomatisasi seeding data film dari TMDB
└── README.md           # Dokumentasi proyek
```
