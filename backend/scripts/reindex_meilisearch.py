#!/usr/bin/env python3
"""Script to reindex all existing pages in Meilisearch."""

import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.core.database import SessionLocal
from app.models.page import Page
from app.services.meilisearch_service import meilisearch_service


def reindex_all_pages():
    """Reindex all pages from the database to Meilisearch."""
    db = SessionLocal()
    try:
        # Get all pages from database
        print("Fetching all pages from database...")
        pages = db.query(Page).all()

        if not pages:
            print("No pages found in database.")
            return

        print(f"Found {len(pages)} pages to index.")

        # Format pages for Meilisearch
        documents = []
        for page in pages:
            documents.append({
                "id": page.id,
                "project_id": page.project_id,
                "crawl_job_id": page.crawl_job_id,
                "url": page.url,
                "title": page.title or "",
                "meta_description": page.meta_description or "",
                "h1": page.h1 or "",
                "text_content": page.text_content or "",
                "status_code": page.status_code,
                "word_count": page.word_count,
                "seo_score": page.seo_score,
                "depth": page.depth,
                "internal_links_count": page.internal_links_count,
                "external_links_count": page.external_links_count,
            })

        # Index in batches of 1000
        batch_size = 1000
        total_batches = (len(documents) + batch_size - 1) // batch_size

        print(f"Indexing in {total_batches} batch(es)...")

        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            batch_num = i // batch_size + 1
            print(f"Indexing batch {batch_num}/{total_batches} ({len(batch)} documents)...")

            try:
                meilisearch_service.index_pages_bulk(batch)
                print(f"✓ Batch {batch_num} indexed successfully")
            except Exception as e:
                print(f"✗ Error indexing batch {batch_num}: {e}")

        print("\n✓ Reindexing complete!")
        print(f"Total pages indexed: {len(documents)}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    reindex_all_pages()
