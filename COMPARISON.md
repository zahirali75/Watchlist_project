# CineList: Mono-file vs Berlapis

Dua folder ini isinya sama-sama CineList. Bedanya cuma satu: bagaimana kode backend dipecah.

| | `C:\\Users\\Asus\\cinelist` (asli) | `C:\\Users\\Asus\\cinelist-refactor` (salinan) |
|---|---|---|
| Backend | `backend/main.py` — 1 file, 363 baris | `app/` — 34 file, 6 lapisan |
| Ubah 1 perilaku | buka file 363 baris, cari manual | buka 1 file ~60 baris |
| Tambah entitas baru | numpuk di main.py | bikin 4 file di folder sendiri, main.py tidak disentuh |
| Test | tidak ada | 28 test, `pytest -q` -> 28 passed |
| Validasi input | manual di tiap endpoint | 1 skema Pydantic dipakai request + response |
| Error | tiap endpoint bikin JSON sendiri | 1 error handler, bentuk respons seragam |
| Log aktivitas | tidak ada | tabel `audit_logs`, otomatis terisi |
| Auth | JWT di main.py | `app/core/security.py` + `app/api/deps.py` |

## Peta folder salinan

```
app/
  main.py            <- perakitan: pasang router + error handler (pintu masuk)
  core/              <- pondasi lintas fitur
    config.py          baca & validasi .env saat boot (SECRET_KEY < 32 char = gagal start)
    security.py        hash password, bikin/baca JWT
    exceptions.py      HttpError(409, "...") -> jadi respons HTTP
    error_handlers.py  tangkap HttpError / ValidationError / error Supabase -> 1 bentuk
    pagination.py      hitung page/limit/offset
    constants.py       USER_ROLES, WATCH_STATUS
  db/client.py       <- satu-satunya tempat Supabase dibuat
  schemas/           <- bentuk data (masuk & keluar)
  repositories/      <- HANYA bicara database
    base.py            helper tabel -> insert/select/update/delete
    movie_repository.py
    ...
  services/          <- HANYA aturan bisnis ("film ini sudah ada di watchlist" -> 409)
  api/
    deps.py          reader token JWT + penjaga role
    routers/         HANYA daftar endpoint (URL, method, siapa yang boleh)
```

## Alur satu request: POST /watchlists

```
1  watchlist_router.py   cek token & role          -> kalau gagal: 401 / 403
2  watchlist_schema.py   validasi body             -> kalau gagal: 422
3  watchlist_service.py  aturan bisnis:
                           - film ada? tidak -> 404
                           - sudah di watchlist? ya -> 409
4  watchlist_repository  query ke Supabase
5  audit_log_repository  catat siapa melakukan apa
6  common.py             bungkus respons {success, message, data}
```

Tiap lapisan cuma tahu tugasnya sendiri. Ini yang bikin fitur baru bisa ditambah tanpa
menyentuh lapisan lain.

## Bahasan jujur: ini bukan gratis

+ 34 file untuk fitur yang tadi 1 file. Untuk aplikasi sebesar CineList, ini di sisi
  "berat". Kalau backend-nya cuma 3 endpoint, mono-file lebih cepat dikerjakan.
- Tapi begitu endpoint > 10 dan dikerjakan lebih dari satu orang atau lebih dari
  sebulan, mono-file mulai makan korban: kamu lupa endpoint mana yang sudah ada,
  dan tiap perubahan berisiko merusak yang lain.

Aturan praktisnya bukan "selalu berlapis", tapi "pecah saat mulai sakit".

## Bahasan jujur: perbedaan perilaku asli vs salinan

Ini yang harus kamu tahu sebelum membandingkan, supaya tidak bingung:

| Perilaku | Asli | Salinan | Kenapa |
|---|---|---|---|
| `GET /users` | terbuka siapa saja | wajib token admin | data user tidak boleh publik |
| `POST /movies` | siapa saja | wajib token admin | supaya tidak sembarang orang menambah film |
| `POST /auth/register` | ada | ada, tetap publik | ini memang harus publik |
| Respons | campur (`{"detail": ...}` dari FastAPI) | selalu `{success, message, data}` | biar frontend cuma punya 1 cara baca |
| Hapus film | langsung | tetap langsung | belum ada aturan "hanya pemilik" |
| Duplikat watchlist | pesan error mentah Supabase | 409 + pesan Indonesia | pesan DB tidak bocor ke user |
| Jalan port | 8000/8001 | 8010 | supaya bisa jalan bareng buat bandingin |

## Cara jalanin (di folder salinan saja)

```
cd C:\\Users\\Asus\\cinelist-refactor
./run.sh                       # cek .venv, bikin kalau belum ada, lalu start di :8010
./.venv/Scripts/python.exe -m pytest -q      # 28 test
./.venv/Scripts/python.exe scripts/smoke_check.py   # tembak API sungguhan
```

Dokumentasi interaktif: http://127.0.0.1:8010/docs

## Yang TIDAK berubah

- Skema database & data Supabase: sama persis, tidak ada migrasi dijalankan.
  (File `migrations/*.sql` cuma dokumentasi skema, isinya identik dengan `schema.sql`.)
- Frontend (kalau nanti ada): kontrak endpoint lama masih kompatibel, kecuali
  dua endpoint yang sekarang minta token admin.
- `backend/main.py` versi lama tetap ada di salinan ini, jadi bisa dibandingkan
  bersebelahan tanpa buka dua folder.
