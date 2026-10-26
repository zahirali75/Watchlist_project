-- ==========================================
-- CineList - migrasi 0002: tabel audit log (FITUR BARU)
-- Audit log untuk registrasi dan perubahan katalog film.
-- created_by boleh NULL karena registrasi user juga dicatat.
-- ==========================================
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    context TEXT NOT NULL,
    type VARCHAR(50) NOT NULL,
    created_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_created_by ON audit_logs(created_by);
CREATE INDEX IF NOT EXISTS idx_audit_logs_type ON audit_logs(type);
