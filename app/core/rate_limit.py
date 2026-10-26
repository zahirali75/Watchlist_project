"""Pembatas percobaan login (in-memory, sederhana).

Cukup untuk satu proses server (MVP / tugas kuliah). Jika backend dijalankan
dengan beberapa worker atau instance, ganti penyimpanannya dengan Redis atau
rate limit di reverse proxy; antarmuka kelas ini bisa dipertahankan.
"""
from __future__ import annotations

import time
from collections import defaultdict, deque
from threading import Lock

from app.core.exceptions import TooManyRequestsError


class LoginThrottle:
    def __init__(self) -> None:
        self._failures: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    @staticmethod
    def key(ip: str | None, email: str) -> str:
        """Kunci per (IP + email): membatasi tebak-tebakan password satu akun."""
        return f"{ip or '-'}|{email.strip().lower()}"

    @staticmethod
    def ip_key(ip: str | None) -> str:
        """Kunci per IP saja (semua email): membatasi password spraying lintas akun.
        Awalan '*|' tidak mungkin bertabrakan dengan key(), karena key() selalu diawali IP."""
        return f"*|{ip or '-'}"

    def _prune(self, bucket: deque[float], window: int, now: float) -> None:
        while bucket and now - bucket[0] > window:
            bucket.popleft()

    def check(self, key: str, max_attempts: int, window: int) -> None:
        """Lempar 429 bila kegagalan dalam jendela waktu sudah mencapai batas."""
        now = time.monotonic()
        with self._lock:
            bucket = self._failures.get(key)
            if bucket is None:
                return
            self._prune(bucket, window, now)
            if not bucket:
                # Bucket kosong dibuang agar memori tidak tumbuh tanpa batas.
                self._failures.pop(key, None)
                return
            if len(bucket) >= max_attempts:
                retry_after = max(1, int(window - (now - bucket[0])))
                raise TooManyRequestsError(
                    "Terlalu banyak percobaan login gagal. Coba lagi nanti.",
                    meta={"retryAfterSeconds": retry_after},
                )

    def record_failure(self, key: str, at: float | None = None) -> None:
        """Catat satu kegagalan. `at` hanya dipakai tes untuk memundurkan waktu."""
        with self._lock:
            self._failures[key].append(time.monotonic() if at is None else at)

    def reset(self, key: str) -> None:
        with self._lock:
            self._failures.pop(key, None)

    def clear_all(self) -> None:
        with self._lock:
            self._failures.clear()


login_throttle = LoginThrottle()
