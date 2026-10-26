# CineList — ERD dan skema yang benar-benar aktif

Dokumen ERD lama sebelumnya mencampur tabel yang sudah diterapkan dengan fitur yang baru direncanakan, dan menyebut beberapa tipe ID yang tidak sesuai dengan DDL. Dokumen ini sekarang membedakan skema aktif dari ide fitur masa depan.

## ERD aktif

```text
USERS (id UUID PK)
  1 ────── N WATCHLISTS (user_id UUID FK, movie_id INTEGER FK)
                         N ────── 1 MOVIES (id SERIAL/INTEGER PK)

USERS (id UUID PK)
  1 ────── N AUDIT_LOGS (created_by UUID FK nullable)
```

`AUDIT_LOGS` baru ada setelah `migrations/0002_audit_logs.sql` diterapkan. Karena itu, `schema.sql` saja belum cukup untuk memasang seluruh skema yang dipakai aplikasi aktif.

## Tabel aktif

### `users`

| Kolom | Tipe/aturan | Kegunaan |
|---|---|---|
| `id` | UUID primary key | Identitas user |
| `name` | VARCHAR(255), NOT NULL | Nama |
| `email` | VARCHAR(255), UNIQUE, NOT NULL | Login |
| `password_hash` | VARCHAR(255), NOT NULL | Hash password; tidak dikembalikan di API publik |
| `role` | VARCHAR(50), default `user`, CHECK `user`/`admin` | Role akses |
| `created_at` | TIMESTAMP, default NOW() | Waktu pendaftaran |

Catatan: `role` saat ini belum `NOT NULL`; nilai `NULL` tidak ditolak hanya oleh `CHECK`. Tambahkan constraint melalui migrasi setelah memeriksa data existing.

### `movies`

| Kolom | Tipe/aturan | Kegunaan |
|---|---|---|
| `id` | SERIAL primary key | Identitas film |
| `title` | VARCHAR(255), NOT NULL | Judul |
| `release_year` | INTEGER nullable | Tahun rilis |
| `genre` | VARCHAR(255) nullable | Genre |
| `director` | VARCHAR(255) nullable | Sutradara |
| `overview` | TEXT nullable | Sinopsis |
| `poster_url` | TEXT nullable | URL poster |
| `rating` | DECIMAL(3,1) nullable | Rating katalog |
| `created_at` | TIMESTAMP default NOW() | Waktu record dibuat |

Skema SQL saat ini tidak menetapkan constraint rentang untuk `rating` atau `release_year`; validasi request film dilakukan oleh Pydantic, tetapi sebaiknya database juga menegakkan invariant yang kritis.

### `watchlists`

| Kolom | Tipe/aturan | Kegunaan |
|---|---|---|
| `id` | SERIAL primary key | Identitas item |
| `user_id` | UUID FK ke `users.id`, NOT NULL, ON DELETE CASCADE | Pemilik |
| `movie_id` | INTEGER FK ke `movies.id`, NOT NULL, ON DELETE CASCADE | Film |
| `status` | Default `want_to_watch`, CHECK daftar status | Status menonton |
| `notes` | TEXT nullable | Catatan user |
| `created_at` | TIMESTAMP default NOW() | Waktu dibuat |
| `updated_at` | TIMESTAMP default NOW() | Waktu perubahan terakhir |

`UNIQUE(user_id, movie_id)` mencegah satu pengguna menambahkan film yang sama dua kali. API aktif mengubah `updated_at` ketika item watchlist diperbarui. Untuk data yang dibuat/diubah di luar API, pertimbangkan trigger database; `DEFAULT NOW()` saja tidak memperbarui timestamp ketika `UPDATE`.

### `audit_logs`

| Kolom | Tipe/aturan | Kegunaan |
|---|---|---|
| `id` | SERIAL primary key | Identitas log |
| `context` | TEXT NOT NULL | Ringkasan kejadian |
| `type` | VARCHAR(50) NOT NULL | Jenis kejadian |
| `created_by` | UUID FK nullable, ON DELETE SET NULL | Pelaku |
| `created_at` | TIMESTAMPTZ default NOW() | Waktu kejadian |

## Relasi dan role

- `users` ke `watchlists`: one-to-many.
- `movies` ke `watchlists`: one-to-many. Secara konseptual `users` dan `movies` memiliki many-to-many melalui `watchlists`.
- `users` ke `audit_logs`: one-to-many opsional; log tetap tersedia jika user dihapus karena `created_by` menjadi NULL.
- Role aktif hanya `user` dan `admin`, disimpan pada `users.role`. Tidak diperlukan tabel `roles` terpisah untuk dua role sederhana.

## Fitur yang baru direncanakan

Tabel `reviews`, `favorites`, `collections`, dan `collection_movies` yang muncul pada ERD lama **belum ada dalam DDL aktif dan belum mempunyai endpoint aktif**. Tambahkan sebagai migrasi dan API terpisah hanya bila masuk kebutuhan produk.

## Rekomendasi sebelum production

1. Migrasi `role` dan `watchlists.status` menjadi `NOT NULL` setelah memeriksa/membersihkan data existing.
2. Tambahkan constraint database untuk rentang rating dan tahun rilis agar data tetap valid di luar API.
3. Samakan zona waktu timestamp (disarankan `TIMESTAMPTZ`) melalui migrasi yang aman.
4. Tambahkan indeks yang sesuai dengan pola query aktual. `idx_movies_title` B-tree tidak ideal untuk pencarian `ILIKE '%teks%'` pada katalog besar; evaluasi indeks trigram bila jumlah film meningkat.
5. Dokumentasikan prosedur pemberian role admin dan uji izin endpoint berdasarkan role serta kepemilikan data.
