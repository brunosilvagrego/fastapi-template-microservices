from sqlalchemy import Column, ForeignKey, Integer, String

from app.models.base import Base


class Item(Base):
    __tablename__ = "item"

    id = Column(Integer, primary_key=True, index=True, unique=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    owner_id = Column(Integer, ForeignKey("client.id"), nullable=False)
