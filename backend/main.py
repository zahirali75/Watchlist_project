from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException, Query, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os
from pathlib import Path
from dotenv import load_dotenv
import jwt
from passlib.context import CryptContext
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

# -------------------------------------------------
load_dotenv()

# -------------------------------------------------
# (Already loaded above, no duplicate import needed)

SECRET_KEY = os.getenv("SECRET_KEY") or "supersecretkey"
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

# Password hashing (use pbkdf2_sha256 for unlimited length)
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

# HTTP Bearer security scheme (Authorization: Bearer ***)
bearer = HTTPBearer()

# -------------------------------------------------
# JWT helper functions
# -------------------------------------------------
def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token kedaluwarsa")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token tidak valid")

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(bearer)):
    token = credentials.credentials
    payload = decode_token(token)
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Token tidak memiliki sub")
    return int(user_id)

def get_current_user_with_role(credentials: HTTPAuthorizationCredentials = Depends(bearer)):
    """Return user_id dan role dari JWT token untuk RBAC."""
    token = credentials.credentials
    payload = decode_token(token)
    user_id = payload.get("sub")
    role = payload.get("role", "user")  # default role: user
    if user_id is None:
        raise HTTPException(status_code=401, detail="Token tidak memiliki sub")
    return {"user_id": int(user_id), "role": role}

def require_admin(credentials: HTTPAuthorizationCredentials = Depends(bearer)):
    """Hanya admin yang bisa akses endpoint ini."""
    user_info = get_current_user_with_role(credentials)
    if user_info["role"] != "admin":
        raise HTTPException(status_code=403, detail="Akses ditolak: hanya admin yang diizinkan")
    return user_info["user_id"]

from backend.database import supabase

app = FastAPI(
    title="CineList API",
    description="REST API untuk aplikasi CineList",
    version="1.0.0"
)

# -------------------------------------------------
# CORS Middleware - aktifkan untuk frontend React
# -------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],  # Vite default: 5173
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------
# Data models
# -------------------------------------------------
class MovieCreate(BaseModel):
    title: str
    release_year: int
    genre: str
    director: str
    overview: str
    poster_url: str
    rating: float

class MovieUpdate(BaseModel):
    title: str
    release_year: int
    genre: str
    director: str
    overview: str
    poster_url: str
    rating: float

class WatchlistCreate(BaseModel):
    user_id: str
    movie_id: int
    status: Optional[str] = "want_to_watch"
    notes: Optional[str] = None

class WatchlistUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None

class RegisterUser(BaseModel):
    email: str
    password: str
    name: Optional[str] = None

class LoginUser(BaseModel):
    email: str
    password: str

# -------------------------------------------------
# Endpoints
# -------------------------------------------------
@app.get("/", tags=["Health Check"])
def root():
    return {
        "message": "Selamat datang di CineList API! 🎬",
        "docs": "/docs",
        "status": "Online & Connected to Supabase"
    }

# Movies catalog
@app.get("/movies", tags=["Movies Catalog"])
def get_movies(
    search: Optional[str] = Query(None, description="Cari film berdasarkan judul"),
    genre: Optional[str] = Query(None, description="Filter berdasarkan genre")
):
    """Mengambil daftar film dari Supabase dengan opsi pencarian & filter."""
    try:
        query = supabase.table("movies").select("*")
        if search:
            query = query.ilike("title", f"%{search}%")
        if genre:
            query = query.ilike("genre", f"%{genre}%")
        response = query.execute()
        return {"success": True, "count": len(response.data), "data": response.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/movies/{movie_id}", tags=["Movies Catalog"])
def get_movie_detail(movie_id: int):
    """Mengambil detail lengkap 1 film spesifik."""
    try:
        response = supabase.table("movies").select("*").eq("id", movie_id).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Film tidak ditemukan")
        return {"success": True, "data": response.data[0]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/movies", tags=["Movies Catalog"])
def create_movie(movie: MovieCreate):
    response = supabase.table("movies").insert(movie.model_dump()).execute()
    return response.data

@app.put("/movies/{movie_id}", tags=["Movies Catalog"])
def update_movie(movie_id: int, movie: MovieUpdate):
    response = (
        supabase
        .table("movies")
        .update(movie.model_dump())
        .eq("id", movie_id)
        .execute()
    )
    return response.data

@app.delete("/movies/{movie_id}", tags=["Movies Catalog"])
def delete_movie(movie_id: int):
    response = (
        supabase
        .table("movies")
        .delete()
        .eq("id", movie_id)
        .execute()
    )
    return {"message": "Movie berhasil dihapus", "data": response.data}

# Watchlist – protected by JWT
@app.get("/watchlists/{user_id}", tags=["Watchlist"])
def get_watchlist(user_id: str, current_user: int = Depends(get_current_user)):
    if current_user != int(user_id):
        raise HTTPException(status_code=403, detail="Tidak diizinkan mengakses watchlist orang lain")
    try:
        response = supabase.table("watchlists").select("*, movies(*)").eq("user_id", user_id).execute()
        return {"success": True, "count": len(response.data), "data": response.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/watchlists", tags=["Watchlist"])
def add_to_watchlist(item: WatchlistCreate, current_user: int = Depends(get_current_user)):
    """Menambahkan film ke watchlist user dengan status tertentu (JWT protected)."""
    try:
        if item.status and item.status not in ["want_to_watch", "watching", "watched"]:
            raise HTTPException(
                status_code=400,
                detail="Status tidak valid. Harus salah satu dari: want_to_watch, watching, watched"
            )
        data = {"user_id": item.user_id, "movie_id": item.movie_id, "status": item.status, "notes": item.notes}
        response = supabase.table("watchlists").insert(data).execute()
        return {"success": True, "message": "Film berhasil ditambahkan ke watchlist!", "data": response.data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/watchlists/{watchlist_id}", tags=["Watchlist"])
def update_watchlist_item(
    watchlist_id: int,
    update_data: WatchlistUpdate,
    current_user: int = Depends(get_current_user)
):
    """Update status atau notes dari watchlist item (JWT protected)."""
    try:
        # Cek apakah watchlist item milik user yang login
        check = supabase.table("watchlists").select("user_id").eq("id", watchlist_id).execute()
        if not check.data:
            raise HTTPException(status_code=404, detail="Watchlist item tidak ditemukan")
        
        owner_id = check.data[0]["user_id"]
        if current_user != int(owner_id):
            raise HTTPException(status_code=403, detail="Tidak diizinkan mengubah watchlist orang lain")
        
        # Validasi status jika diberikan
        if update_data.status and update_data.status not in ["want_to_watch", "watching", "watched"]:
            raise HTTPException(
                status_code=400,
                detail="Status tidak valid. Harus salah satu dari: want_to_watch, watching, watched"
            )
        
        # Update hanya field yang diberikan
        update_payload = update_data.model_dump(exclude_unset=True)
        if not update_payload:
            raise HTTPException(status_code=400, detail="Tidak ada data untuk diupdate")
        
        response = (
            supabase
            .table("watchlists")
            .update(update_payload)
            .eq("id", watchlist_id)
            .execute()
        )
        return {"success": True, "message": "Watchlist item berhasil diupdate", "data": response.data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/watchlists/{watchlist_id}", tags=["Watchlist"])
def delete_watchlist_item(watchlist_id: int, current_user: int = Depends(get_current_user)):
    """Hapus item dari watchlist (JWT protected)."""
    try:
        # Cek ownership
        check = supabase.table("watchlists").select("user_id").eq("id", watchlist_id).execute()
        if not check.data:
            raise HTTPException(status_code=404, detail="Watchlist item tidak ditemukan")
        
        owner_id = check.data[0]["user_id"]
        if current_user != int(owner_id):
            raise HTTPException(status_code=403, detail="Tidak diizinkan menghapus watchlist orang lain")
        
        response = supabase.table("watchlists").delete().eq("id", watchlist_id).execute()
        return {"success": True, "message": "Watchlist item berhasil dihapus", "data": response.data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Users
@app.get("/users", tags=["Users"])
def get_all_users():
    """Mengambil semua user dari Supabase `users`."""
    try:
        resp = supabase.table("users").select("id, name, email, created_at").execute()
        return {"success": True, "count": len(resp.data), "data": resp.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/users", tags=["Users"])
def register_user(user: RegisterUser):
    """Buat user baru di Supabase → hash password → JWT."""
    pwd = str(user.password)
    hashed = pwd_context.hash(pwd)
    payload = {"email": user.email, "password_hash": hashed, "name": user.name or "", "role": "user"}
    try:
        resp = supabase.table("users").insert(payload).execute()
        if not resp.data:
            raise HTTPException(status_code=500, detail="Gagal menyimpan user ke Supabase")
        user_id = resp.data[0].get("id")
        role = resp.data[0].get("role", "user")
        token = create_access_token({"sub": str(user_id), "role": role})
        return {"success": True, "user_id": user_id, "access_token": token, "role": role}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/login", tags=["Authentication"])
def login_user(credentials: LoginUser):
    """Login user → verifikasi password → return JWT token."""
    try:
        # Cari user berdasarkan email
        resp = supabase.table("users").select("*").eq("email", credentials.email).execute()
        if not resp.data:
            raise HTTPException(status_code=401, detail="Email atau password salah")
        
        user = resp.data[0]
        stored_hash = user.get("password_hash")
        
        # Verifikasi password
        if not pwd_context.verify(credentials.password, stored_hash):
            raise HTTPException(status_code=401, detail="Email atau password salah")
        
        # Generate JWT token dengan role
        user_id = user.get("id")
        role = user.get("role", "user")
        token = create_access_token({"sub": str(user_id), "role": role})
        
        return {
            "success": True,
            "user_id": user_id,
            "email": user.get("email"),
            "name": user.get("name"),
            "role": role,
            "access_token": token
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/users/{user_id}/stats", tags=["Stats"])
def get_user_stats(user_id: str):
    """Ringkasan statistik watchlist user."""
    try:
        response = supabase.table("watchlists").select("status").eq("user_id", user_id).execute()
        data = response.data
        total = len(data)
        watched = sum(1 for i in data if i["status"] == "watched")
        watching = sum(1 for i in data if i["status"] == "watching")
        want_to_watch = sum(1 for i in data if i["status"] == "want_to_watch")
        return {"success": True, "total": total, "watched": watched, "watching": watching, "want_to_watch": want_to_watch}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
