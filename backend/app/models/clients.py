from sqlalchemy import Boolean, Column, DateTime, Integer, String

from app.models.base import Base


class Client(Base):
    __tablename__ = "client"

    id = Column(Integer, primary_key=True, index=True, unique=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    is_admin = Column(Boolean, default=False, nullable=False)
    oauth_id = Column(String, unique=True, nullable=False)
    oauth_secret_hash = Column(String, nullable=False)

    @property
    def is_active(self) -> bool:
        return self.deleted_at is None
