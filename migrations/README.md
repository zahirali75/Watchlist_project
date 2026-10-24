# Migrasi database CineList

Dulu: satu file `schema.sql` tanpa riwayat, dan tabel `audit_logs` hidup manual
di dashboard Supabase (tidak ada di source control).

Sekarang: tiap perubahan skema punya file bernomor, sama seperti folder
`drizzle/` di repo Pola Parking API.

| File | Isi |
|---|---|
| `0001_initial_schema.sql` | users, movies, watchlists + index (sama dengan schema.sql lama) |
| `0002_audit_logs.sql` | tabel audit_logs + index (baru) |

Cara jalanin (urutan wajib):
1. Supabase Dashboard -> SQL Editor
2. Jalankan `0001_initial_schema.sql` (kalau database masih kosong)
3. Jalankan `0002_audit_logs.sql`
4. Cek di Table Editor: harus muncul `audit_logs`

Kenapa tidak pakai Alembic saja? Karena aplikasi ini bicara ke Supabase lewat
PostgREST (kunci API), bukan lewat koneksi Postgres langsung. File SQL bernomor
ini adalah bentuk paling jujur & aman untuk alur tersebut. Alembic tetap
disediakan (`alembic.ini` + `alembic/env.py`) untuk saat kamu ingin
autogenerate dari model SQLAlchemy - lihat README bagian "Alembic".
