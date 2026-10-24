# CineList Database Schema & ERD

## 📊 ERD Overview

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   USERS     │────1:N──│  WATCHLISTS  │──N:1────│   MOVIES    │
│             │         │              │         │             │
│ - id        │         │ - id         │         │ - id        │
│ - email     │         │ - user_id    │         │ - title     │
│ - name      │         │ - movie_id   │         │ - genre     │
│ - role      │         │ - status     │         │ - rating    │
│ - bio       │ NEW     │ - notes      │         │             │
│ - avatar_url│ NEW     │              │         │             │
└─────────────┘         └──────────────┘         └─────────────┘
       │                                                 │
       │                                                 │
       │1:N                                            N:1
       │                                                 │
       ▼                                                 ▼
┌─────────────┐                                  ┌─────────────┐
│   REVIEWS   │──────────────────────────────────│   MOVIES    │
│             │                    N:1            │  (same)     │
│ - id        │ NEW TABLE                         └─────────────┘
│ - user_id   │
│ - movie_id  │
│ - rating    │ (1-10)
│ - review    │ (text)
│ - created_at│
└─────────────┘
       │
       │ (user_id references users)
       │
┌─────────────┐
│   USERS     │
│  (same)     │
└─────────────┘
       │
       │1:N
       │
       ▼
┌─────────────┐                                  ┌─────────────┐
│  FAVORITES  │──────────────────────────────────│   MOVIES    │
│             │                    N:1            │  (same)     │
│ - id        │ NEW TABLE                         └─────────────┘
│ - user_id   │
│ - movie_id  │
│ - created_at│
└─────────────┘


┌─────────────┐         ┌──────────────────┐         ┌─────────────┐
│   USERS     │────1:N──│   COLLECTIONS    │──1:N────│ COLLECTION_ │
│             │         │                  │         │   MOVIES    │
│             │         │ - id             │         │             │
│             │         │ - user_id        │         │ - id        │
│             │         │ - name           │         │ - collection│
│             │         │ - description    │   ┌─────│   _id       │
│             │         │ - is_public      │   │     │ - movie_id  │
└─────────────┘         │ - created_at     │   │     │ - order     │
                        └──────────────────┘   │     └─────────────┘
                                               │            │
                                               │            │N:1
                                               │            ▼
                                               │     ┌─────────────┐
                                               │     │   MOVIES    │
                                               │     │  (same)     │
                                               │     └─────────────┘
                                               │
                        ┌──────────────────────┘
                        │ Many-to-Many Relationship
                        │ (Junction Table)
```

---

## 🗂️ Tabel Existing (Sudah Ada)

### 1. **users**
| Column         | Type         | Constraint           | Description                    |
|----------------|--------------|----------------------|--------------------------------|
| id             | SERIAL       | PRIMARY KEY          | User ID (auto-increment)       |
| email          | VARCHAR(255) | UNIQUE, NOT NULL     | Email untuk login              |
| password_hash  | TEXT         | NOT NULL             | Password (hashed dengan bcrypt)|
| name           | VARCHAR(255) | NULL                 | Nama lengkap user              |
| role           | VARCHAR(50)  | DEFAULT 'user'       | Role: 'user' atau 'admin'      |
| created_at     | TIMESTAMP    | DEFAULT NOW()        | Kapan user register            |

**⚠️ Perlu ditambahkan ke tabel existing:**
```sql
ALTER TABLE users ADD COLUMN bio TEXT;
ALTER TABLE users ADD COLUMN avatar_url TEXT;
```

---

### 2. **movies**
| Column        | Type         | Constraint           | Description                      |
|---------------|--------------|----------------------|----------------------------------|
| id            | SERIAL       | PRIMARY KEY          | Movie ID (auto-increment)        |
| title         | VARCHAR(255) | NOT NULL             | Judul film                       |
| release_year  | INTEGER      | NOT NULL             | Tahun rilis                      |
| genre         | VARCHAR(255) | NULL                 | Genre (bisa multi: "Action, Sci-Fi") |
| director      | VARCHAR(255) | NULL                 | Nama sutradara                   |
| overview      | TEXT         | NULL                 | Sinopsis/deskripsi film          |
| poster_url    | TEXT         | NULL                 | URL poster (TMDB)                |
| rating        | FLOAT        | DEFAULT 0.0          | Rating TMDB (0-10)               |
| created_at    | TIMESTAMP    | DEFAULT NOW()        | Kapan film ditambahkan ke DB     |

---

### 3. **watchlists**
| Column      | Type         | Constraint                          | Description                           |
|-------------|--------------|-------------------------------------|---------------------------------------|
| id          | SERIAL       | PRIMARY KEY                         | Watchlist entry ID                    |
| user_id     | INTEGER      | FOREIGN KEY → users(id) ON DELETE CASCADE | Pemilik watchlist                |
| movie_id    | INTEGER      | FOREIGN KEY → movies(id) ON DELETE CASCADE | Film yang ditambahkan            |
| status      | VARCHAR(50)  | DEFAULT 'want_to_watch'             | Status: want_to_watch, watching, watched |
| notes       | TEXT         | NULL                                | Catatan pribadi (reminder)            |
| created_at  | TIMESTAMP    | DEFAULT NOW()                       | Kapan ditambahkan                     |
| updated_at  | TIMESTAMP    | DEFAULT NOW()                       | Kapan terakhir diupdate               |

**Constraint:**
- UNIQUE(user_id, movie_id) → satu user tidak bisa tambah film yang sama 2x

---

## 🆕 Tabel Baru (Akan Dibuat)

### 4. **reviews** 🌟
**Purpose:** User memberikan rating + review mendalam untuk film yang sudah ditonton.

| Column      | Type         | Constraint                              | Description                           |
|-------------|--------------|-----------------------------------------|---------------------------------------|
| id          | SERIAL       | PRIMARY KEY                             | Review ID                             |
| user_id     | INTEGER      | FOREIGN KEY → users(id) ON DELETE CASCADE | Pembuat review                        |
| movie_id    | INTEGER      | FOREIGN KEY → movies(id) ON DELETE CASCADE | Film yang direview                    |
| rating      | FLOAT        | CHECK (rating >= 1 AND rating <= 10)    | Rating personal user (1-10)           |
| review      | TEXT         | NULL                                    | Teks review (bisa kosong, rating only)|
| created_at  | TIMESTAMP    | DEFAULT NOW()                           | Kapan review dibuat                   |
| updated_at  | TIMESTAMP    | DEFAULT NOW()                           | Kapan terakhir diedit                 |

**Constraint:**
- UNIQUE(user_id, movie_id) → satu user hanya bisa review satu film sekali
- INDEX on (movie_id) → untuk query "semua review film X"
- INDEX on (user_id) → untuk query "semua review dari user Y"

**SQL:**
```sql
CREATE TABLE reviews (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    movie_id INTEGER NOT NULL REFERENCES movies(id) ON DELETE CASCADE,
    rating FLOAT CHECK (rating >= 1 AND rating <= 10),
    review TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, movie_id)
);

CREATE INDEX idx_reviews_movie_id ON reviews(movie_id);
CREATE INDEX idx_reviews_user_id ON reviews(user_id);
```

---

### 5. **favorites** ⭐
**Purpose:** User menandai film sebagai "favorit sepanjang masa" (showcase di profile).

| Column      | Type         | Constraint                              | Description                           |
|-------------|--------------|-----------------------------------------|---------------------------------------|
| id          | SERIAL       | PRIMARY KEY                             | Favorite ID                           |
| user_id     | INTEGER      | FOREIGN KEY → users(id) ON DELETE CASCADE | Pemilik favorite                      |
| movie_id    | INTEGER      | FOREIGN KEY → movies(id) ON DELETE CASCADE | Film yang difavoritkan                |
| created_at  | TIMESTAMP    | DEFAULT NOW()                           | Kapan difavoritkan                    |

**Constraint:**
- UNIQUE(user_id, movie_id) → satu user tidak bisa favorite film yang sama 2x
- INDEX on (user_id) → untuk query "favorites milik user X"

**SQL:**
```sql
CREATE TABLE favorites (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    movie_id INTEGER NOT NULL REFERENCES movies(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, movie_id)
);

CREATE INDEX idx_favorites_user_id ON favorites(user_id);
```

---

### 6. **collections** 📂
**Purpose:** User membuat list custom untuk organize film (e.g., "Best Nolan Films", "Horror 2024").

| Column       | Type         | Constraint                              | Description                           |
|--------------|--------------|-----------------------------------------|---------------------------------------|
| id           | SERIAL       | PRIMARY KEY                             | Collection ID                         |
| user_id      | INTEGER      | FOREIGN KEY → users(id) ON DELETE CASCADE | Pembuat collection                    |
| name         | VARCHAR(255) | NOT NULL                                | Nama collection                       |
| description  | TEXT         | NULL                                    | Deskripsi collection                  |
| is_public    | BOOLEAN      | DEFAULT FALSE                           | Apakah publik (bisa diliat user lain) |
| created_at   | TIMESTAMP    | DEFAULT NOW()                           | Kapan dibuat                          |
| updated_at   | TIMESTAMP    | DEFAULT NOW()                           | Kapan terakhir diupdate               |

**SQL:**
```sql
CREATE TABLE collections (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    is_public BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_collections_user_id ON collections(user_id);
CREATE INDEX idx_collections_public ON collections(is_public) WHERE is_public = TRUE;
```

---

### 7. **collection_movies** 🎬
**Purpose:** Junction table untuk relationship many-to-many antara collections dan movies.

| Column        | Type         | Constraint                                   | Description                           |
|---------------|--------------|----------------------------------------------|---------------------------------------|
| id            | SERIAL       | PRIMARY KEY                                  | Entry ID                              |
| collection_id | INTEGER      | FOREIGN KEY → collections(id) ON DELETE CASCADE | Collection parent                     |
| movie_id      | INTEGER      | FOREIGN KEY → movies(id) ON DELETE CASCADE   | Film yang ditambahkan                 |
| order         | INTEGER      | DEFAULT 0                                    | Urutan film dalam collection          |
| created_at    | TIMESTAMP    | DEFAULT NOW()                                | Kapan ditambahkan                     |

**Constraint:**
- UNIQUE(collection_id, movie_id) → satu film tidak bisa ditambah 2x dalam collection yang sama
- INDEX on (collection_id) → untuk query "film apa saja di collection X"

**SQL:**
```sql
CREATE TABLE collection_movies (
    id SERIAL PRIMARY KEY,
    collection_id INTEGER NOT NULL REFERENCES collections(id) ON DELETE CASCADE,
    movie_id INTEGER NOT NULL REFERENCES movies(id) ON DELETE CASCADE,
    "order" INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(collection_id, movie_id)
);

CREATE INDEX idx_collection_movies_collection_id ON collection_movies(collection_id);
```

---

## 🔗 Relationships Summary

| From Table         | To Table    | Type  | Description                                    |
|--------------------|-------------|-------|------------------------------------------------|
| watchlists.user_id | users.id    | N:1   | Setiap watchlist entry milik 1 user            |
| watchlists.movie_id| movies.id   | N:1   | Setiap watchlist entry referensi 1 film        |
| reviews.user_id    | users.id    | N:1   | Setiap review dibuat oleh 1 user               |
| reviews.movie_id   | movies.id   | N:1   | Setiap review untuk 1 film                     |
| favorites.user_id  | users.id    | N:1   | Setiap favorite milik 1 user                   |
| favorites.movie_id | movies.id   | N:1   | Setiap favorite referensi 1 film               |
| collections.user_id| users.id    | N:1   | Setiap collection dibuat oleh 1 user           |
| collection_movies  | collections | N:1   | Setiap entry dalam junction table → 1 collection |
| collection_movies  | movies      | N:1   | Setiap entry referensi 1 film                  |

**Note:**
- Collections ↔ Movies adalah **many-to-many** via `collection_movies` junction table
- 1 collection bisa punya banyak film
- 1 film bisa masuk ke banyak collection

---

## 🛠️ Migration Script (Supabase SQL Editor)

Copy-paste script ini ke Supabase SQL Editor untuk setup semua tabel baru:

```sql
-- =====================================================
-- CineList Database Schema Migration
-- =====================================================

-- 1. Tambahkan kolom baru ke tabel users
ALTER TABLE users 
ADD COLUMN IF NOT EXISTS bio TEXT,
ADD COLUMN IF NOT EXISTS avatar_url TEXT;

-- 2. Buat tabel reviews
CREATE TABLE IF NOT EXISTS reviews (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    movie_id INTEGER NOT NULL REFERENCES movies(id) ON DELETE CASCADE,
    rating FLOAT CHECK (rating >= 1 AND rating <= 10),
    review TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, movie_id)
);

CREATE INDEX IF NOT EXISTS idx_reviews_movie_id ON reviews(movie_id);
CREATE INDEX IF NOT EXISTS idx_reviews_user_id ON reviews(user_id);

-- 3. Buat tabel favorites
CREATE TABLE IF NOT EXISTS favorites (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    movie_id INTEGER NOT NULL REFERENCES movies(id) ON DELETE CASCADE,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, movie_id)
);

CREATE INDEX IF NOT EXISTS idx_favorites_user_id ON favorites(user_id);

-- 4. Buat tabel collections
CREATE TABLE IF NOT EXISTS collections (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    is_public BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_collections_user_id ON collections(user_id);
CREATE INDEX IF NOT EXISTS idx_collections_public ON collections(is_public) WHERE is_public = TRUE;

-- 5. Buat tabel collection_movies (junction table)
CREATE TABLE IF NOT EXISTS collection_movies (
    id SERIAL PRIMARY KEY,
    collection_id INTEGER NOT NULL REFERENCES collections(id) ON DELETE CASCADE,
    movie_id INTEGER NOT NULL REFERENCES movies(id) ON DELETE CASCADE,
    "order" INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(collection_id, movie_id)
);

CREATE INDEX IF NOT EXISTS idx_collection_movies_collection_id ON collection_movies(collection_id);

-- 6. Buat function untuk auto-update updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 7. Tambahkan trigger untuk auto-update updated_at
DROP TRIGGER IF EXISTS update_reviews_updated_at ON reviews;
CREATE TRIGGER update_reviews_updated_at
    BEFORE UPDATE ON reviews
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_collections_updated_at ON collections;
CREATE TRIGGER update_collections_updated_at
    BEFORE UPDATE ON collections
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- Migration Complete! ✅
-- =====================================================
```

---

## 📝 Contoh Data & Query

### Insert Review
```sql
INSERT INTO reviews (user_id, movie_id, rating, review)
VALUES (1, 5, 9.5, 'Masterpiece! Nolan at his best.');
```

### Query: Semua review untuk film tertentu
```sql
SELECT r.*, u.name as reviewer_name, u.avatar_url
FROM reviews r
JOIN users u ON r.user_id = u.id
WHERE r.movie_id = 5
ORDER BY r.created_at DESC;
```

### Query: Average rating film dari user reviews
```sql
SELECT movie_id, AVG(rating) as avg_user_rating, COUNT(*) as review_count
FROM reviews
WHERE movie_id = 5
GROUP BY movie_id;
```

### Query: Favorites user dengan movie details
```sql
SELECT f.*, m.*
FROM favorites f
JOIN movies m ON f.movie_id = m.id
WHERE f.user_id = 1
ORDER BY f.created_at DESC;
```

### Query: Films dalam collection (dengan urutan)
```sql
SELECT cm.order, m.*
FROM collection_movies cm
JOIN movies m ON cm.movie_id = m.id
WHERE cm.collection_id = 3
ORDER BY cm.order ASC;
```

---

## 🎯 Next Steps

1. **Jalankan migration script** di Supabase SQL Editor
2. **Verifikasi tabel** sudah terbuat dengan query:
   ```sql
   SELECT table_name 
   FROM information_schema.tables 
   WHERE table_schema = 'public'
   ORDER BY table_name;
   ```
3. **Test insert dummy data** untuk setiap tabel
4. **Lanjut ke implementasi endpoint** FastAPI

---

**Created:** 2026-10-19  
**Version:** 1.0  
**Author:** Hermes Agent
