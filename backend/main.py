from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from backend.database import supabase

app = FastAPI(
    title="CineList API",
    description="Backend REST API untuk aplikasi Movie Watchlist CineList (Mata Kuliah Web Application Development)",
    version="1.0.0"
)

# Konfigurasi CORS agar Frontend React dapat mengakses API dengan lancar
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class WatchlistCreate(BaseModel):
    user_id: str
    movie_id: int
    status: Optional[str] = "want_to_watch"
    notes: Optional[str] = None

class WatchlistUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None

class UserCreate(BaseModel):
    name: str
    email: str
    password: str

@app.post("/users", tags=["Auth"])
def register_user(user: UserCreate):
    """Mendaftarkan user baru. Password di‑hash dengan SHA‑256 sebelum disimpan."""
    try:
        # Hash password (simple SHA‑256, production sebaiknya gunakan argon2/bcrypt)
        import hashlib
        password_hash = hashlib.sha256(user.password.encode()).hexdigest()
        payload = {
            "name": user.name,
            "email": user.email,
            "password_hash": password_hash,
        }
        # Insert dan kembalikan data user yang baru dibuat (tanpa password)
        response = supabase.table("users").insert(payload).execute()
        if response.error:
            # Jika email sudah ada, Supabase mengembalikan error unik
            raise HTTPException(status_code=400, detail=response.error.message)
        created = response.data[0]
        # Jangan mengirim password_hash kembali ke client
        created.pop("password_hash", None)
        return {"success": True, "data": created}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/movies", tags=["Movies Catalog"])
def get_movies(
    search: Optional[str] = Query(None, description="Cari film berdasarkan judul"),
    genre: Optional[str] = Query(None, description="Filter berdasarkan genre")
):
    """Mengambil daftar film dari katalog Supabase dengan opsi pencarian & filter."""
    try:
        query = supabase.table("movies").select("*")
        
        if search:
            query = query.ilike("title", f"%{search}%")
        if genre:
            query = query.ilike("genre", f"%{genre}%")
            
        response = query.execute()
        return {
            "success": True,
            "count": len(response.data),
            "data": response.data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/movies/{movie_id}", tags=["Movies Catalog"])
def get_movie_by_id(movie_id: int):
    """Mengambil detail satu film berdasarkan ID."""
    try:
        response = supabase.table("movies").select("*").eq("id", movie_id).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Film tidak ditemukan")
        return {"success": True, "data": response.data[0]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/watchlists/{user_id}", tags=["Watchlist"])
def get_watchlist(user_id: str):
    """Mengambil daftar watchlist milik user tertentu beserta detail filmnya."""
    try:
        response = supabase.table("watchlists").select("*, movies(*)").eq("user_id", user_id).execute()
        return {
            "success": True,
            "count": len(response.data),
            "data": response.data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/watchlists", tags=["Watchlist"])
def add_to_watchlist(item: WatchlistCreate):
    """Menambahkan film ke watchlist user dengan status tertentu."""
    try:
        if item.status and item.status not in ["want_to_watch", "watching", "watched"]:
            raise HTTPException(
                status_code=400,
                detail="Status tidak valid. Harus salah satu dari: want_to_watch, watching, watched"
            )
        data = {
            "user_id": item.user_id,
            "movie_id": item.movie_id,
            "status": item.status,
            "notes": item.notes
        }
        response = supabase.table("watchlists").insert(data).execute()
        return {
            "success": True,
            "message": "Film berhasil ditambahkan ke watchlist!",
            "data": response.data
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/watchlists/{watchlist_id}", tags=["Watchlist"])
def update_watchlist(watchlist_id: int, item: WatchlistUpdate):
    """Memperbarui status atau catatan film dalam watchlist."""
    try:
        update_data = {}
        if item.status is not None:
            if item.status not in ["want_to_watch", "watching", "watched"]:
                raise HTTPException(
                    status_code=400,
                    detail="Status tidak valid. Harus salah satu dari: want_to_watch, watching, watched"
                )
            update_data["status"] = item.status
        if item.notes is not None:
            update_data["notes"] = item.notes
            
        if not update_data:
            raise HTTPException(status_code=400, detail="Tidak ada data yang diperbarui")
            
        response = supabase.table("watchlists").update(update_data).eq("id", watchlist_id).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Item watchlist tidak ditemukan")
            
        return {
            "success": True,
            "message": "Watchlist berhasil diperbarui!",
            "data": response.data[0]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/watchlists/{watchlist_id}", tags=["Watchlist"])
def delete_from_watchlist(watchlist_id: int):
    """Menghapus film dari watchlist berdasarkan ID watchlist."""
    try:
        response = supabase.table("watchlists").delete().eq("id", watchlist_id).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Item watchlist tidak ditemukan")
        return {
            "success": True,
            "message": "Film berhasil dihapus dari watchlist!",
            "data": response.data[0]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/users/{user_id}/stats", tags=["Stats"])
def get_user_stats(user_id: str):
    """Mengambil ringkasan statistik watchlist user (total, watched, watching, want_to_watch)."""
    try:
        response = supabase.table("watchlists").select("status").eq("user_id", user_id).execute()
        data = response.data
        total = len(data)
        watched = sum(1 for item in data if item["status"] == "watched")
        watching = sum(1 for item in data if item["status"] == "watching")
        want_to_watch = sum(1 for item in data if item["status"] == "want_to_watch")
        return {
            "success": True,
            "total": total,
            "watched": watched,
            "watching": watching,
            "want_to_watch": want_to_watch
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
