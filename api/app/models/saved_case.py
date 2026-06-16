import uuid
from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class SavedCase(Base):
    __tablename__ = "saved_cases"

    id: Mapped[str] = mapped_column(
        String, primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False)
    case_id: Mapped[str] = mapped_column(String, ForeignKey("cases.id"), nullable=False)
    notes: Mapped[str] = mapped_column(Text, nullable=True)
