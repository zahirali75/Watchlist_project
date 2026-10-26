#!/usr/bin/env bash
# Jalankan server CineList API. Dapat dipakai di Linux, macOS, dan Windows (Git Bash).
set -euo pipefail
cd "$(dirname "$0")"

# Penjaga 1: kalau file ini sampai tersimpan dengan akhir baris Windows (CRLF),
# bash membaca "\r" sebagai bagian dari perintah dan gagal dengan pesan
# "set: pipefail\r: invalid option name". Diperiksa lebih dulu supaya pesannya jelas.
if head -1 "$0" | grep -q $'\r'; then
  echo "[error] run.sh memakai akhir baris Windows (CRLF), bukan LF." >&2
  echo "        Perbaiki dengan salah satu cara:" >&2
  echo "          dos2unix run.sh" >&2
  echo "          git rm --cached run.sh && git checkout -- run.sh" >&2
  exit 1
fi

# Penjaga 2: di Windows ada dua bash. Git Bash (MSYS) mengenali path ".venv/Scripts/python.exe",
# bash WSL tidak. Kalau dijalankan dari WSL, arahkan memakai path /mnt/c/... atau pakai Git Bash.
if [ ! -d ".venv/Scripts" ] && [ -d "/mnt/c" ] && [ ! -x ".venv/bin/python" ]; then
  echo "[error] Sepertinya kamu menjalankan run.sh lewat bash WSL." >&2
  echo "        Dari WSL, jalankan:  bash /mnt/c/Users/Asus/cinelist/run.sh" >&2
  echo "        Supaya cukup 'bash run.sh' di CMD, pakai Git Bash:" >&2
  echo '          set PATH=C:\Program Files\Git\bin;%PATH%   lalu ulangi bash run.sh' >&2
  exit 1
fi

# Pilih interpreter virtualenv sesuai OS (Windows: Scripts/, Linux/macOS: bin/).
if [ -x ".venv/bin/python" ]; then
  PY=".venv/bin/python"
elif [ -x ".venv/Scripts/python.exe" ]; then
  PY=".venv/Scripts/python.exe"
else
  echo "[setup] membuat virtualenv .venv ..."
  python3 -m venv .venv 2>/dev/null || python -m venv .venv
  if [ -x ".venv/bin/python" ]; then PY=".venv/bin/python"; else PY=".venv/Scripts/python.exe"; fi
  "$PY" -m pip install --upgrade pip -q
  "$PY" -m pip install -r requirements.txt -q
fi

if [ ! -f ".env" ]; then
  echo "[error] File .env belum ada. Salin dulu: cp .env.example .env lalu isi DATABASE_URL dan SECRET_KEY." >&2
  exit 1
fi

PORT="${APP_PORT:-8000}"
echo "[run] uvicorn app.main:app --reload --port ${PORT}"
exec "$PY" -m uvicorn app.main:app --reload --port "${PORT}"
