"""Constraint database benar-benar ditegakkan (bukan hanya validasi API)."""
from __future__ import annotations

import psycopg
import pytest


def _user(sql, email="a@x.com", role="user"):
    return sql.execute("INSERT INTO users (name,email,password_hash,role) VALUES ('A',%s,'h',%s) RETURNING id", (email, role)).fetchone()[0]


def test_email_unik_tanpa_peduli_huruf_besar(sql):
    _user(sql, "Budi@x.com")
    with pytest.raises(psycopg.errors.UniqueViolation):
        _user(sql, "budi@x.com")


def test_role_dan_status_tidak_boleh_null_atau_di_luar_daftar(sql):
    with pytest.raises(psycopg.errors.NotNullViolation):
        sql.execute("INSERT INTO users (name,email,password_hash,role) VALUES ('A','n@x.com','h',NULL)")
    with pytest.raises(psycopg.errors.CheckViolation):
        _user(sql, "r@x.com", role="superadmin")


def test_rating_dan_tahun_dibatasi(sql):
    with pytest.raises(psycopg.errors.CheckViolation):
        sql.execute("INSERT INTO movies (title, rating) VALUES ('X', 10.5)")
    with pytest.raises(psycopg.errors.CheckViolation):
        sql.execute("INSERT INTO movies (title, release_year) VALUES ('X', 1500)")
    sql.execute("INSERT INTO movies (title, rating, release_year) VALUES ('Ok', 10, 2010)")


def test_cascade_hapus_user_dan_film_membersihkan_watchlist_audit_set_null(sql):
    uid = _user(sql)
    mid = sql.execute("INSERT INTO movies (title) VALUES ('M') RETURNING id").fetchone()[0]
    sql.execute("INSERT INTO watchlists (user_id, movie_id) VALUES (%s,%s)", (uid, mid))
    sql.execute("INSERT INTO audit_logs (context,type,created_by) VALUES ('c','T',%s)", (uid,))
    with pytest.raises(psycopg.errors.UniqueViolation):
        sql.execute("INSERT INTO watchlists (user_id, movie_id) VALUES (%s,%s)", (uid, mid))
    sql.execute("DELETE FROM users WHERE id=%s", (uid,))
    assert sql.execute("SELECT COUNT(*) FROM watchlists").fetchone()[0] == 0
    assert sql.execute("SELECT created_by FROM audit_logs").fetchone()[0] is None
