from fastapi import FastAPI
from pydantic import BaseModel
from backend.database import supabase

app = FastAPI(
    title="CineList API",
    description="REST API untuk aplikasi CineList",
    version="1.0.0"
)


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


@app.get("/")
def root():
    return {
        "message": "CineList API is running"
    }


@app.get("/movies")
def get_movies():
    response = supabase.table("movies").select("*").execute()
    return response.data


@app.post("/movies")
def create_movie(movie: MovieCreate):
    response = supabase.table("movies").insert(movie.model_dump()).execute()
    return response.data


@app.put("/movies/{movie_id}")
def update_movie(movie_id: int, movie: MovieUpdate):
    response = (
        supabase
        .table("movies")
        .update(movie.model_dump())
        .eq("id", movie_id)
        .execute()
    )

    return response.data


@app.delete("/movies/{movie_id}")
def delete_movie(movie_id: int):
    response = (
        supabase
        .table("movies")
        .delete()
        .eq("id", movie_id)
        .execute()
    )

    return {
        "message": "Movie berhasil dihapus",
        "data": response.data
    }