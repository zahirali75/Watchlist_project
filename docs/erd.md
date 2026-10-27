# ERD (skema aktual, head 0006)

```mermaid
erDiagram
    USERS ||--o{ WATCHLISTS : "memiliki"
    MOVIES ||--o{ WATCHLISTS : "ada di"
    USERS ||--o{ AUDIT_LOGS : "mencatat (nullable)"
    USERS ||--o{ REFRESH_TOKENS : "punya sesi"
    USERS ||--o{ PASSWORD_RESETS : "minta reset"

    USERS {
        uuid id PK
        varchar name
        varchar email UK "unik + unik lower(email)"
        varchar password_hash
        varchar role "user | admin"
        timestamp created_at
    }
    MOVIES {
        int id PK
        varchar title
        int release_year "1888-2100"
        varchar genre
        varchar director
        text overview
        text poster_url
        decimal rating "0-10"
        timestamp created_at
    }
    WATCHLISTS {
        int id PK
        uuid user_id FK "CASCADE"
        int movie_id FK "CASCADE"
        varchar status "want_to_watch | watching | watched"
        text notes
        timestamp created_at
        timestamp updated_at
    }
    AUDIT_LOGS {
        int id PK
        text context
        varchar type
        uuid created_by FK "SET NULL"
        timestamptz created_at
    }
    REFRESH_TOKENS {
        uuid id PK
        uuid user_id FK "CASCADE"
        varchar token_hash UK "hash SHA-256; token asli tidak disimpan"
        timestamptz expires_at "14 hari"
        timestamptz revoked_at "nullable"
        timestamptz created_at
    }
    PASSWORD_RESETS {
        uuid id PK
        uuid user_id FK "CASCADE"
        varchar token_hash UK "hash SHA-256; sekali pakai"
        timestamptz expires_at "30 menit"
        timestamptz used_at "nullable"
        timestamptz created_at
    }
```

Catatan:
- `WATCHLISTS` punya `UNIQUE (user_id, movie_id)` sehingga hubungan user–movie bersifat many-to-many tanpa duplikat.
- `REFRESH_TOKENS` dan `PASSWORD_RESETS` menyimpan **hanya hash SHA-256**, bukan token aslinya. Keduanya ditambahkan di migrasi 0005/0006 (27 Oktober 2026) untuk fitur perpanjangan sesi dan lupa password.
- Tabel `reviews`, `favorites`, `collections` pada dokumen lama **tidak ada** di skema aktif (lihat `docs/archive/`).
