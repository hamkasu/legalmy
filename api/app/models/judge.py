import uuid
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class Judge(Base):
    __tablename__ = "judges"

    id: Mapped[str] = mapped_column(
        String, primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    court_id: Mapped[str] = mapped_column(String, ForeignKey("courts.id"), nullable=True, index=True)
    state: Mapped[str] = mapped_column(String(100), nullable=True, index=True)
