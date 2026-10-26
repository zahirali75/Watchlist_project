"""Menjaga batas antar-fitur dan larangan memakai Supabase (aturan dosen)."""
from __future__ import annotations

import ast
from pathlib import Path

APP = Path(__file__).resolve().parents[2] / "app"
SHARED = {"core", "db"}
FEATURES = sorted(p.name for p in APP.iterdir() if p.is_dir() and p.name not in SHARED and not p.name.startswith("__"))
# Modul fitur lain yang BOLEH diimpor: service (logika), schemas (kontrak), dependencies (auth).
ALLOWED_CROSS = {"service", "schemas", "dependencies"}


def _py_files(root: Path):
    return [p for p in root.rglob("*.py") if "__pycache__" not in p.parts]


def _app_imports(path: Path) -> list[tuple[str, str]]:
    """Daftar (fitur_tujuan, modul) dari import `app.*`, termasuk `from app.x import service`."""
    found: list[tuple[str, str]] = []
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.ImportFrom) and node.module and node.module.split(".")[0] == "app":
            parts = node.module.split(".")
            if len(parts) >= 3:
                found.append((parts[1], parts[2]))
            elif len(parts) == 2:
                found.extend((parts[1], alias.name) for alias in node.names)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                parts = alias.name.split(".")
                if parts[0] == "app" and len(parts) >= 3:
                    found.append((parts[1], parts[2]))
    return found


def test_fitur_terdeteksi():
    # Jaga agar tes ini tidak diam-diam kosong bila folder diganti nama.
    assert {"auth", "users", "movies", "watchlists", "audit_logs"} <= set(FEATURES)


def test_tidak_ada_supabase_di_source():
    root = APP.parent
    for folder in ("app", "backend", "scripts", "tests"):
        for path in _py_files(root / folder):
            if path.name == "test_architecture.py":
                continue
            for line in path.read_text(encoding="utf-8").splitlines():
                stripped = line.strip().lower()
                if stripped.startswith(("import ", "from ")):
                    assert "supabase" not in stripped and "postgrest" not in stripped, f"{path}: {line}"


def test_fitur_hanya_mengimpor_modul_publik_fitur_lain():
    for feature in FEATURES:
        for path in _py_files(APP / feature):
            for target, module in _app_imports(path):
                if target in FEATURES and target != feature:
                    assert module in ALLOWED_CROSS, f"{path} mengimpor app.{target}.{module}"


def test_sql_dan_driver_hanya_di_repository():
    for feature in FEATURES:
        for path in _py_files(APP / feature):
            if path.name == "repository.py":
                continue
            text = path.read_text(encoding="utf-8")
            assert "from sqlalchemy" not in text and "app.db.executor" not in text, path


def test_router_tidak_mengimpor_repository():
    for feature in FEATURES:
        router = APP / feature / "router.py"
        if router.exists():
            assert "repository" not in router.read_text(encoding="utf-8"), router
