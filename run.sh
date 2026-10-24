#!/usr/bin/env bash
# Jalankan server CineList API (versi refactor).
set -e
cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
  echo "[setup] membuat virtualenv..."
  python -m venv .venv
  ./.venv/Scripts/python.exe -m pip install --upgrade pip -q
  ./.venv/Scripts/python.exe -m pip install -r requirements.txt -q
fi

echo "[run] uvicorn app.main:app --reload --port 8000"
./.venv/Scripts/python.exe -m uvicorn app.main:app --reload --port 8000
