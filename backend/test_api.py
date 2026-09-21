import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_root():
    response = client.get("/")
    print("ROOT:", response.status_code, response.json())
    assert response.status_code == 200

def test_movies():
    response = client.get("/movies")
    print("MOVIES:", response.status_code, response.json().get("count"))
    assert response.status_code == 200

def test_invalid_watchlist_status():
    # Testing invalid status validation
    response = client.post("/watchlists", json={
        "user_id": "00000000-0000-0000-0000-000000000000",
        "movie_id": 1,
        "status": "invalid_status"
    })
    print("INVALID STATUS:", response.status_code, response.json())
    assert response.status_code == 400

if __name__ == "__main__":
    test_root()
    test_movies()
    test_invalid_watchlist_status()
    print("Semua tes FastAPI TestClient berhasil! 🚀")
