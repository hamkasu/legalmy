import uuid
from sqlalchemy import String, Boolean, Text, Date, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class Case(Base):
    __tablename__ = "cases"

    id: Mapped[str] = mapped_column(
        String, primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    case_number: Mapped[str] = mapped_column(String(100), nullable=True, index=True)
    citation: Mapped[str] = mapped_column(String(200), nullable=True, index=True)
    court_id: Mapped[str] = mapped_column(String, ForeignKey("courts.id"), nullable=True)
    judge_id: Mapped[str] = mapped_column(String, ForeignKey("judges.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    plaintiff: Mapped[str] = mapped_column(String(300), nullable=True)
    defendant: Mapped[str] = mapped_column(String(300), nullable=True)
    date_filed: Mapped[str] = mapped_column(String(20), nullable=True)
    date_decided: Mapped[str] = mapped_column(String(20), nullable=True)
    practice_area: Mapped[str] = mapped_column(String(50), default="other")
    outcome: Mapped[str] = mapped_column(String(50), default="unknown")
    full_text: Mapped[str] = mapped_column(Text, nullable=True)
    summary: Mapped[str] = mapped_column(Text, nullable=True)
    source_url: Mapped[str] = mapped_column(String(500), nullable=True)
    source: Mapped[str] = mapped_column(String(50), default="other")
    language: Mapped[str] = mapped_column(String(10), default="en")
    is_published: Mapped[bool] = mapped_column(Boolean, default=True)
