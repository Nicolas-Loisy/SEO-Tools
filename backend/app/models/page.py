"""Page and Link models for crawled content."""

from datetime import datetime
from sqlalchemy import String, Integer, DateTime, ForeignKey, Text, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector
from app.core.database import Base


class Page(Base):
    """
    Page model representing a crawled web page.

    Stores page metadata, content, and embeddings for semantic analysis.
    """

    __tablename__ = "pages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # URL & Identity
    url: Mapped[str] = mapped_column(String(2000), nullable=False)
    url_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)  # SHA256
    canonical_url: Mapped[str] = mapped_column(String(2000), nullable=True)

    # HTTP Response
    status_code: Mapped[int] = mapped_column(Integer, nullable=True)
    content_type: Mapped[str] = mapped_column(String(100), nullable=True)

    # SEO Metadata
    title: Mapped[str] = mapped_column(String(500), nullable=True)
    meta_description: Mapped[str] = mapped_column(Text, nullable=True)
    meta_keywords: Mapped[str] = mapped_column(Text, nullable=True)
    h1: Mapped[str] = mapped_column(Text, nullable=True)

    # Content
    text_content: Mapped[str] = mapped_column(Text, nullable=True)
    rendered_html: Mapped[str] = mapped_column(Text, nullable=True)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=True)  # MD5 of text content
    word_count: Mapped[int] = mapped_column(Integer, default=0)

    # Hreflang & Internationalization
    hreflang: Mapped[str] = mapped_column(String(2000), nullable=True)  # JSON string
    lang: Mapped[str] = mapped_column(String(10), nullable=True)

    # Crawl metadata
    depth: Mapped[int] = mapped_column(Integer, default=0)
    discovered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_crawled_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    # SEO Scores (computed)
    seo_score: Mapped[float] = mapped_column(default=0.0)

    # Vector embedding for semantic similarity (768 dims for sentence-transformers)
    embedding: Mapped[Vector] = mapped_column(Vector(768), nullable=True)

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="pages")

    outgoing_links: Mapped[list["Link"]] = relationship(
        "Link",
        foreign_keys="Link.source_page_id",
        back_populates="source_page",
        cascade="all, delete-orphan",
    )

    incoming_links: Mapped[list["Link"]] = relationship(
        "Link",
        foreign_keys="Link.target_page_id",
        back_populates="target_page",
        cascade="all, delete-orphan",
    )

    schema_suggestions: Mapped[list["SchemaSuggestion"]] = relationship(
        "SchemaSuggestion", back_populates="page", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_pages_project_url_hash", "project_id", "url_hash", unique=True),
        Index("ix_pages_embedding", "embedding", postgresql_using="ivfflat"),
    )

    def __repr__(self) -> str:
        return f"<Page(id={self.id}, url='{self.url[:50]}...', status={self.status_code})>"


class Link(Base):
    """
    Link model representing internal links between pages.

    Forms the graph structure for internal linking analysis.
    """

    __tablename__ = "links"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    source_page_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("pages.id", ondelete="CASCADE"), nullable=False, index=True
    )
    target_page_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("pages.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Link attributes
    anchor_text: Mapped[str] = mapped_column(Text, nullable=True)
    rel: Mapped[str] = mapped_column(String(100), nullable=True)  # nofollow, etc.
    is_internal: Mapped[bool] = mapped_column(default=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationships
    source_page: Mapped["Page"] = relationship(
        "Page", foreign_keys=[source_page_id], back_populates="outgoing_links"
    )
    target_page: Mapped["Page"] = relationship(
        "Page", foreign_keys=[target_page_id], back_populates="incoming_links"
    )

    __table_args__ = (
        Index("ix_links_source_target", "source_page_id", "target_page_id", unique=True),
    )

    def __repr__(self) -> str:
        return f"<Link(source={self.source_page_id}, target={self.target_page_id})>"
