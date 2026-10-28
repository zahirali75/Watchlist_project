"""Import semua model di sini supaya terdaftar di Base.metadata (dipakai Alembic)."""
from app.db.models.audit_log import AuditLog
from app.db.models.movie import Movie
from app.db.models.password_reset import PasswordReset
from app.db.models.refresh_token import RefreshToken
from app.db.models.review import Review
from app.db.models.user import User
from app.db.models.watchlist import Watchlist

__all__ = ["AuditLog", "Movie", "PasswordReset", "RefreshToken", "Review", "User", "Watchlist"]
