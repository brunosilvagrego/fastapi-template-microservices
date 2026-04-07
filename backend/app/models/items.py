from sqlalchemy import BigInteger, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Item(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    title: Mapped[str]
    description: Mapped[str]
    owner_id: Mapped[int] = mapped_column(ForeignKey("clients.id"))
