#!/usr/bin/env bash
# Jalankan server CineList API. Dapat dipakai di Linux, macOS, dan Windows (Git Bash).
set -euo pipefail
cd "$(dirname "$0")"

# Pilih interpreter virtualenv sesuai OS (Windows: Scripts/, Linux/macOS: bin/).
if [ -x ".venv/bin/python" ]; then
  PY=".venv/bin/python"
elif [ -x ".venv/Scripts/python.exe" ]; then
  PY=".venv/Scripts/python.exe"git
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
