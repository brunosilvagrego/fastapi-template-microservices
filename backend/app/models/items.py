from sqlalchemy import Column, ForeignKey, Integer, String

from app.models.base import Base


class Item(Base):
    __tablename__ = "item"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), index=True)
    description = Column(String(255))
    user_id = Column(Integer, ForeignKey("users.id"))
