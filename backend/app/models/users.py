from sqlalchemy import Boolean, Column, DateTime, Integer, String

from app.models.base import Base


class User(Base):
    # Pluralize table name to avoid conflicts with reserved keywords in some
    # databases (e.g., "user" is reserved in PostgreSQL)
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=True)
    created_at = Column(DateTime, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    is_superuser = Column(Boolean, default=False)
    hashed_password = Column(String, nullable=False)

    @property
    def is_active(self) -> bool:
        return self.deleted_at is None
