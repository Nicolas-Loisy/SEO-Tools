"""Content models for generated site trees and drafts."""

from datetime import datetime
from sqlalchemy import String, Integer, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class SiteTree(Base):
    """
    SiteTree model for storing generated site architectures.

    Stores hierarchical site structure with categories, pages, slugs, and metadata.
    """

    __tablename__ = "site_trees"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Tree metadata
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)

    # Input parameters
    keyword: Mapped[str] = mapped_column(String(255), nullable=True)
    theme: Mapped[str] = mapped_column(String(255), nullable=True)
    depth: Mapped[int] = mapped_column(Integer, default=3)

    # Tree structure (hierarchical JSON)
    tree_json: Mapped[dict] = mapped_column(JSON, nullable=False)

    # Generation metadata
    llm_provider: Mapped[str] = mapped_column(String(50), nullable=True)  # openai, anthropic, manual
    generation_prompt: Mapped[str] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="site_trees")

    def __repr__(self) -> str:
        return f"<SiteTree(id={self.id}, name='{self.name}', depth={self.depth})>"


class ContentDraft(Base):
    """
    ContentDraft model for storing generated SEO-optimized content.

    Contains generated articles, meta descriptions, headings, and SEO recommendations.
    """

    __tablename__ = "content_drafts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Content metadata
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=True)

    # SEO
    meta_title: Mapped[str] = mapped_column(String(500), nullable=True)
    meta_description: Mapped[str] = mapped_column(Text, nullable=True)
    meta_keywords: Mapped[str] = mapped_column(Text, nullable=True)

    # Content structure
    h1: Mapped[str] = mapped_column(String(500), nullable=True)
    outline: Mapped[dict] = mapped_column(JSON, nullable=True)  # H2, H3 structure

    # Main content
    body: Mapped[str] = mapped_column(Text, nullable=False)
    body_html: Mapped[str] = mapped_column(Text, nullable=True)

    # SEO recommendations
    keywords: Mapped[list] = mapped_column(JSON, default=list)  # primary & LSI keywords
    internal_links_suggestions: Mapped[list] = mapped_column(JSON, default=list)

    # Originality & Quality
    word_count: Mapped[int] = mapped_column(Integer, default=0)
    readability_score: Mapped[float] = mapped_column(default=0.0)
    originality_score: Mapped[float] = mapped_column(default=0.0)

    # Generation source
    origin_llm: Mapped[str] = mapped_column(String(50), nullable=True)
    generation_prompt: Mapped[str] = mapped_column(Text, nullable=True)

    # Status
    status: Mapped[str] = mapped_column(String(50), default="draft")  # draft, reviewed, published

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="content_drafts")

    def __repr__(self) -> str:
        return f"<ContentDraft(id={self.id}, title='{self.title}', status='{self.status}')>"
