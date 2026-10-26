"""Pembungkus kompatibilitas: implementasi tunggal ada di scripts/seed_movies.py.

Perintah lama `python seed_movies.py` tetap bekerja.
"""
from scripts.seed_movies import seed

if __name__ == "__main__":
    seed(page=4, limit=20)  # default lama skrip ini
