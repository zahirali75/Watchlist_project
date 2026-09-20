-- ==========================================
-- CineList Database DDL Schema (PostgreSQL / Supabase)
-- ==========================================

-- 1. Table Users (Menyimpan data akun pengguna)
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- 2. Table Movies (Menyimpan katalog film)
CREATE TABLE IF NOT EXISTS movies (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    release_year INTEGER,
    genre VARCHAR(255),
    director VARCHAR(255),
    overview TEXT,
    poster_url TEXT,
    rating DECIMAL(3, 1),
    created_at TIMESTAMP DEFAULT NOW()
);

-- 3. Table Watchlists (Junction Table Relasi Many-to-Many Users & Movies)
CREATE TABLE IF NOT EXISTS watchlists (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    movie_id INTEGER NOT NULL REFERENCES movies(id) ON DELETE CASCADE,
    status VARCHAR(50) DEFAULT 'want_to_watch' 
        CHECK (status IN ('want_to_watch', 'watching', 'watched')),
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, movie_id)
);

-- 4. Query Performance Indexes
CREATE INDEX IF NOT EXISTS idx_watchlists_user_id ON watchlists(user_id);
CREATE INDEX IF NOT EXISTS idx_watchlists_movie_id ON watchlists(movie_id);
CREATE INDEX IF NOT EXISTS idx_movies_title ON movies(title);
