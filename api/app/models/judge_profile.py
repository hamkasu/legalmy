import uuid
from sqlalchemy import String, Float, Integer, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class JudgeProfile(Base):
    __tablename__ = "judge_profiles"

    id: Mapped[str] = mapped_column(
        String, primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    judge_id: Mapped[str] = mapped_column(
        String, ForeignKey("judges.id"), unique=True, nullable=False
    )
    total_decisions: Mapped[int] = mapped_column(Integer, default=0)
    plaintiff_favourable_rate: Mapped[float] = mapped_column(Float, nullable=True)
    avg_disposal_days: Mapped[float] = mapped_column(Float, nullable=True)
    interlocutory_grant_rate: Mapped[float] = mapped_column(Float, nullable=True)
    costs_awarded_rate: Mapped[float] = mapped_column(Float, nullable=True)
    top_practice_areas: Mapped[str] = mapped_column(Text, nullable=True)
    last_computed_at: Mapped[str] = mapped_column(String(50), nullable=True)
