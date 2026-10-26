"""Pembatas login."""
from __future__ import annotations

import pytest

from app.core.exceptions import TooManyRequestsError
from app.core.rate_limit import LoginThrottle


def test_diblokir_setelah_batas_gagal_dan_reset_saat_sukses():
    t = LoginThrottle()
    key = t.key("1.1.1.1", "A@x.com")
    for _ in range(3):
        t.check(key, 3, 60)
        t.record_failure(key)
    with pytest.raises(TooManyRequestsError) as err:
        t.check(key, 3, 60)
    assert err.value.status_code == 429 and err.value.meta["retryAfterSeconds"] >= 1
    t.reset(key)
    t.check(key, 3, 60)


def test_key_tidak_peka_huruf_besar_dan_terpisah_per_ip():
    assert LoginThrottle.key("1.1.1.1", " A@x.com ") == LoginThrottle.key("1.1.1.1", "a@x.com")
    assert LoginThrottle.key("1.1.1.1", "a@x.com") != LoginThrottle.key("2.2.2.2", "a@x.com")


def test_ip_key_terpisah_dari_key_per_email_dan_menahan_spraying():
    t = LoginThrottle()
    ip = "9.9.9.9"
    ip_key = t.ip_key(ip)
    assert ip_key != t.key(ip, "a@x.com")
    # Gagal di banyak email berbeda tetap menghitung ke satu bucket IP.
    for i in range(3):
        t.record_failure(t.key(ip, f"user{i}@x.com"))
        t.record_failure(ip_key)
    with pytest.raises(TooManyRequestsError):
        t.check(ip_key, 3, 60)
    # Bucket per-email yang tidak pernah gagal tidak ikut terblokir.
    t.check(t.key(ip, "fresh@x.com"), 3, 60)


def test_bucket_kosong_dibuang_setelah_jendela_habis():
    t = LoginThrottle()
    key = t.key("1.1.1.1", "gone@x.com")
    t.record_failure(key)
    t.check(key, 5, 0)  # jendela 0 detik: kegagalan langsung kedaluwarsa
    assert key not in t._failures
