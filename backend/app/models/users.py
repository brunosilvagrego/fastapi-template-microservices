from sqlalchemy import Boolean, Column, Integer, String

from app.models.base import Base


class User(Base):
    # Pluralize table name to avoid conflicts with reserved keywords in some
    # databases (e.g., "user" is reserved in PostgreSQL)
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=True)
    is_superuser = Column(Boolean, default=False)
