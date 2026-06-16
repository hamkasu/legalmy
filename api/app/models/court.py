import uuid
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class Court(Base):
    __tablename__ = "courts"

    id: Mapped[str] = mapped_column(
        String, primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    court_type: Mapped[str] = mapped_column(String(100), nullable=True, index=True)
    state: Mapped[str] = mapped_column(String(100), nullable=True, index=True)
    jurisdiction: Mapped[str] = mapped_column(String(255), nullable=True)
    country: Mapped[str] = mapped_column(String(100), default="IN")
