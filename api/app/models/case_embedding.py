import uuid
from sqlalchemy import String, ForeignKey, Vector
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class CaseEmbedding(Base):
    __tablename__ = "case_embeddings"

    id: Mapped[str] = mapped_column(
        String, primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    case_id: Mapped[str] = mapped_column(String, ForeignKey("cases.id"), nullable=False, index=True)
    embedding: Mapped[list] = mapped_column(Vector(1024), nullable=False)
    chunk_index: Mapped[int] = mapped_column(nullable=False)
