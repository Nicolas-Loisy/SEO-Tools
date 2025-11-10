"""Celery tasks for SEO analysis."""

from datetime import datetime
from app.workers.celery_app import celery_app
from app.core.database import SessionLocal
from app.models.page import Page
from app.services.nlp import get_embedding_service


@celery_app.task(name="app.workers.analysis_tasks.compute_page_embeddings")
def compute_page_embeddings(page_id: int) -> dict:
    """
    Compute semantic embeddings for a page.

    Args:
        page_id: Page ID

    Returns:
        Result dict
    """
    db = SessionLocal()
    try:
        # Get page
        page = db.query(Page).filter(Page.id == page_id).first()
        if not page:
            raise ValueError(f"Page {page_id} not found")

        # Skip if no text content
        if not page.text_content or len(page.text_content.strip()) < 50:
            return {"status": "skipped", "reason": "insufficient_content"}

        # Generate embedding
        embedding_service = get_embedding_service()

        # Combine title, meta, and text for better representation
        combined_text = f"{page.title or ''} {page.meta_description or ''} {page.text_content}"

        embedding = embedding_service.generate_embedding(combined_text)

        # Update page with embedding
        page.embedding = embedding
        db.commit()

        return {"status": "success", "dimensions": len(embedding)}

    except Exception as e:
        raise
    finally:
        db.close()


@celery_app.task(name="app.workers.analysis_tasks.compute_project_embeddings")
def compute_project_embeddings(project_id: int) -> dict:
    """
    Compute embeddings for all pages in a project.

    Args:
        project_id: Project ID

    Returns:
        Results dict
    """
    db = SessionLocal()
    try:
        # Get all pages for project
        pages = (
            db.query(Page)
            .filter(Page.project_id == project_id, Page.text_content.isnot(None))
            .all()
        )

        if not pages:
            return {"status": "no_pages", "processed": 0}

        # Get embedding service
        embedding_service = get_embedding_service()

        # Prepare texts
        texts = []
        valid_pages = []

        for page in pages:
            if page.text_content and len(page.text_content.strip()) >= 50:
                combined_text = (
                    f"{page.title or ''} {page.meta_description or ''} {page.text_content}"
                )
                texts.append(combined_text)
                valid_pages.append(page)

        if not texts:
            return {"status": "no_valid_content", "processed": 0}

        # Generate embeddings in batch (much faster)
        embeddings = embedding_service.generate_embeddings(texts)

        # Update pages
        for page, embedding in zip(valid_pages, embeddings):
            page.embedding = embedding

        db.commit()

        return {"status": "success", "processed": len(valid_pages)}

    except Exception as e:
        raise
    finally:
        db.close()


@celery_app.task(name="app.workers.analysis_tasks.compute_internal_linking_graph")
def compute_internal_linking_graph(project_id: int) -> dict:
    """
    Compute internal linking graph for a project.

    Args:
        project_id: Project ID

    Returns:
        Graph statistics
    """
    from app.models.page import Link
    from app.services.graph import LinkGraphService

    db = SessionLocal()
    try:
        # Get all pages for project
        pages = db.query(Page).filter(Page.project_id == project_id).all()

        if not pages:
            return {"status": "no_pages", "nodes": 0, "edges": 0}

        # Create page URL to ID mapping
        url_to_id = {page.url: page.id for page in pages}

        # Process outgoing links from crawled data
        links_to_create = []

        for page in pages:
            # This would come from crawled data
            # For now, we'll just count existing links
            pass

        # Get existing links
        links = db.query(Link).join(Page, Link.source_page_id == Page.id).filter(
            Page.project_id == project_id
        ).all()

        # Compute graph metrics
        graph_service = LinkGraphService()
        metrics = graph_service.compute_metrics(pages, links)

        return {
            "status": "success",
            "nodes": len(pages),
            "edges": len(links),
            **metrics,
        }

    except Exception as e:
        raise
    finally:
        db.close()


@celery_app.task(name="app.workers.analysis_tasks.generate_link_recommendations")
def generate_link_recommendations(project_id: int, top_k: int = 5) -> dict:
    """
    Generate internal link recommendations based on semantic similarity.

    Args:
        project_id: Project ID
        top_k: Number of recommendations per page

    Returns:
        Recommendations dict
    """
    from app.services.graph import LinkGraphService

    db = SessionLocal()
    try:
        # Get all pages with embeddings
        pages = (
            db.query(Page)
            .filter(Page.project_id == project_id, Page.embedding.isnot(None))
            .all()
        )

        if len(pages) < 2:
            return {"status": "insufficient_pages", "recommendations": 0}

        graph_service = LinkGraphService()
        recommendations = graph_service.generate_recommendations(pages, top_k=top_k)

        return {
            "status": "success",
            "pages_analyzed": len(pages),
            "total_recommendations": sum(len(recs) for recs in recommendations.values()),
        }

    except Exception as e:
        raise
    finally:
        db.close()


@celery_app.task(name="app.workers.analysis_tasks.generate_schema_suggestions")
def generate_schema_suggestions(page_id: int) -> dict:
    """
    Generate structured data suggestions for a page.

    Args:
        page_id: Page ID

    Returns:
        Schema.org suggestions
    """
    from app.models.schema import SchemaSuggestion

    db = SessionLocal()
    try:
        # Get page
        page = db.query(Page).filter(Page.id == page_id).first()
        if not page:
            raise ValueError(f"Page {page_id} not found")

        # Detect schema type based on content
        # This is a placeholder - would use NLP/ML for real detection
        schema_type = "Article"  # Default

        # Generate basic Article schema
        schema_json = {
            "@context": "https://schema.org",
            "@type": schema_type,
            "headline": page.title or "",
            "description": page.meta_description or "",
            "url": page.url,
        }

        # Check if suggestion already exists
        existing = (
            db.query(SchemaSuggestion).filter(SchemaSuggestion.page_id == page_id).first()
        )

        if existing:
            existing.schema_type = schema_type
            existing.schema_json = schema_json
            existing.confidence_score = 0.8
            db.commit()
        else:
            suggestion = SchemaSuggestion(
                page_id=page_id,
                schema_type=schema_type,
                schema_json=schema_json,
                confidence_score=0.8,
                generated_by="auto",
            )
            db.add(suggestion)
            db.commit()

        return {"status": "success", "schema_type": schema_type}

    except Exception as e:
        raise
    finally:
        db.close()
