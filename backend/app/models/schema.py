"""Schema suggestion model for structured data generation."""

from datetime import datetime
from sqlalchemy import String, Integer, DateTime, ForeignKey, JSON, Float, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class SchemaSuggestion(Base):
    """
    SchemaSuggestion model for generated JSON-LD structured data.

    Stores generated schema.org markup for pages to improve rich snippets.
    """

    __tablename__ = "schema_suggestions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    page_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("pages.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Schema type detection
    schema_type: Mapped[str] = mapped_column(
        String(100), nullable=False
    )  # Article, Product, FAQ, LocalBusiness, etc.
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)

    # Generated JSON-LD
    schema_json: Mapped[dict] = mapped_column(JSON, nullable=False)

    # Validation
    is_valid: Mapped[bool] = mapped_column(default=False)
    validation_errors: Mapped[list] = mapped_column(JSON, default=list)

    # Meta tags
    og_tags: Mapped[dict] = mapped_column(JSON, nullable=True)  # OpenGraph
    twitter_tags: Mapped[dict] = mapped_column(JSON, nullable=True)  # Twitter Cards

    # Generation metadata
    generated_by: Mapped[str] = mapped_column(String(50), default="auto")  # auto, llm, manual
    notes: Mapped[str] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    page: Mapped["Page"] = relationship("Page", back_populates="schema_suggestions")

    def __repr__(self) -> str:
        return f"<SchemaSuggestion(id={self.id}, type='{self.schema_type}', score={self.confidence_score})>"
