# Database

Skema aktual per revision Alembic **0006 (head)**. Sumber kebenaran: `migrations/versions/` (model referensi: `app/db/models/`). Diverifikasi: `alembic check` tanpa selisih terhadap database hasil `upgrade head`.

## Tabel
### `users`
| Kolom | Tipe | Aturan |
|---|---|---|
| id | UUID | PK, default `gen_random_uuid()` |
| name | VARCHAR(255) | NOT NULL |
| email | VARCHAR(255) | NOT NULL, UNIQUE; **+ UNIQUE INDEX `lower(email)`** (0003) |
| password_hash | VARCHAR(255) | NOT NULL; tidak pernah dikirim ke API |
| role | VARCHAR(50) | default `'user'`, CHECK `user`/`admin`; NOT NULL (0003) |
| created_at | TIMESTAMP | default NOW() |

### `movies`
| Kolom | Tipe | Aturan |
|---|---|---|
| id | SERIAL | PK |
| title | VARCHAR(255) | NOT NULL; index `idx_movies_title` |
| release_year | INTEGER | nullable; CHECK 1888–2100 (0003, tervalidasi) |
| genre, director | VARCHAR(255) | nullable |
| overview, poster_url | TEXT | nullable |
| rating | DECIMAL(3,1) | nullable; CHECK 0–10 (0003, tervalidasi) |
| created_at | TIMESTAMP | default NOW() |

### `watchlists` (tabel penghubung many-to-many users ↔ movies)
| Kolom | Tipe | Aturan |
|---|---|---|
| id | SERIAL | PK |
| user_id | UUID | NOT NULL, FK → users(id) **ON DELETE CASCADE**; index |
| movie_id | INTEGER | NOT NULL, FK → movies(id) **ON DELETE CASCADE**; index |
| status | VARCHAR(50) | default `'want_to_watch'`, CHECK `want_to_watch`/`watching`/`watched`; NOT NULL (0003) |
| notes | TEXT | nullable |
| created_at, updated_at | TIMESTAMP | default NOW() (`updated_at` diperbarui oleh API saat update) |
| | | UNIQUE (user_id, movie_id) |

### `audit_logs`
| Kolom | Tipe | Aturan |
|---|---|---|
| id | SERIAL | PK |
| context | TEXT | NOT NULL |
| type | VARCHAR(50) | NOT NULL; index. Nilai yang ditulis aplikasi: `USER_REGISTER`, `MOVIE_CREATE`, `MOVIE_UPDATE`, `MOVIE_DELETE` |
| created_by | UUID | nullable, FK → users(id) **ON DELETE SET NULL**; index |
| created_at | TIMESTAMPTZ | NOT NULL, default NOW() |

### `refresh_tokens` (migrasi 0005)
| Kolom | Tipe | Aturan |
|---|---|---|
| id | UUID | PK, default `gen_random_uuid()` |
| user_id | UUID | NOT NULL, FK → users(id) **ON DELETE CASCADE**; index |
| token_hash | VARCHAR(64) | NOT NULL; UNIQUE (unique index) |
| expires_at | TIMESTAMPTZ | NOT NULL (default 14 hari) |
| revoked_at | TIMESTAMPTZ | nullable — diisi saat logout/ganti password |
| created_at | TIMESTAMPTZ | NOT NULL, default NOW() |

Menyimpan sesi login yang bisa diperpanjang tanpa mengetik password lagi. **Hanya hash SHA-256** token yang disimpan. Setiap token dirotasi saat dipakai.

### `password_resets` (migrasi 0006)
| Kolom | Tipe | Aturan |
|---|---|---|
| id | UUID | PK, default `gen_random_uuid()` |
| user_id | UUID | NOT NULL, FK → users(id) **ON DELETE CASCADE**; index |
| token_hash | VARCHAR(64) | NOT NULL; UNIQUE (unique index) |
| expires_at | TIMESTAMPTZ | NOT NULL (default 30 menit) |
| used_at | TIMESTAMPTZ | nullable — diisi saat token dipakai (sekali pakai) |
| created_at | TIMESTAMPTZ | NOT NULL, default NOW() |

Token sekali pakai untuk lupa password; juga hanya hash SHA-256 yang disimpan.

## Migrasi (Alembic = satu sumber kebenaran)
| Revision | Isi | Status |
|---|---|---|
| 0001 | users, movies, watchlists + index | Identik dengan `legacy_sql/0001` (diverifikasi) |
| 0002 | audit_logs | Identik dengan `legacy_sql/0002` (diverifikasi: 49 objek skema sama) |
| 0003 | NOT NULL (role, status), CHECK rating/tahun, unique `lower(email)` | **Sudah dijalankan di Supabase 26 Okt 2026**; CHECK diangkat ke VALID setelah data diperiksa |
| 0004 | RLS aktif di keempat tabel; grant `anon`/`authenticated` dicabut beserta default privilege | **Sudah dijalankan di Supabase 26 Okt 2026** (grant memang sudah kosong; 0004 jadi lapis penegas) |
| 0005 | refresh_tokens (+ RLS aktif, grant dicabut) | **Sudah dijalankan di Supabase 27 Okt 2026** (setelah cadangan data) |
| 0006 | password_resets (+ RLS aktif, grant dicabut) | **Sudah dijalankan di Supabase 27 Okt 2026** |

Catatan konsistensi model: `token_hash` di kedua tabel dibuat unik lewat **unique index** (bukan UNIQUE constraint). Model SQLAlchemy harus mengikuti bentuk yang sama, kalau tidak `alembic check` akan melaporkan drift (pernah terjadi saat penambahan 0005/0006).

Perintah: lihat README. `schema.sql` dan `0001/0002 *.sql` dipindah ke `migrations/legacy_sql/` sebagai arsip (jangan dijalankan bersama Alembic).

### Transisi untuk database yang sudah ada (dibuat dari SQL lama)
1. **Cadangkan** database.
2. `alembic stamp 0002` — menandai skema saat ini = 0002 (tidak mengubah data).

   > **PERINGATAN: `stamp` tidak membuat tabel apa pun.** Ia hanya menandai revisi sebagai sudah
   > dijalankan. Jalankan hanya setelah memastikan tabel `audit_logs` **benar-benar ada**, karena
   > itulah isi revisi `0002`. Bila tabelnya belum ada saat `stamp 0002` dijalankan, revisi 0002
   > dianggap selesai dan `audit_logs` tidak akan pernah terbuat — ini pernah terjadi di Supabase
   > (26 Okt 2026). Bila belum ada, jalankan dulu `migrations/legacy_sql/0002_audit_logs.sql`.
3. Periksa data: email kembar beda kapitalisasi (0003 akan berhenti dengan pesan jelas), `rating` di luar 0–10, `release_year` di luar 1888–2100.
4. `alembic upgrade head`.
5. Setelah data lama bersih: `ALTER TABLE movies VALIDATE CONSTRAINT movies_rating_range;` dan `movies_release_year_range`. **Sudah dijalankan 26 Okt 2026** (pemeriksaan data: 0 baris melanggar; kedua constraint kini berstatus VALID).

Downgrade 0003 melepas semua perubahan di atas dan aman dijalankan.

## Yang sengaja belum diubah
- `TIMESTAMP` (tanpa zona) pada users/movies/watchlists vs `TIMESTAMPTZ` pada audit_logs: konversi data lama butuh keputusan zona waktu; aman diselesaikan nanti dalam revision tersendiri.
- Index trigram untuk `ILIKE '%teks%'` pada judul film: tunda sampai data besar.
- Trigger `updated_at`: saat ini hanya API yang memperbarui kolom ini.

## Database tes
Tes integrasi memakai database terpisah (`TEST_DATABASE_URL`, nama wajib mengandung `test`). Tes menjalankan `alembic upgrade head` dari database kosong dan menguji constraint, cascade, alur API, dan migrasi bolak-balik.

## Supabase sebagai server database
Boleh dipakai sebagai hosting PostgreSQL biasa: isi `DATABASE_URL` dengan connection string Postgres (Session pooler bila IPv6 tidak tersedia). Koneksi langsung **melewati Row Level Security**; otorisasi sepenuhnya dijaga kode aplikasi (filter `user_id`, ownership di service).
