"""Meilisearch service for full-text search."""

import meilisearch
from typing import List, Dict, Any, Optional
from app.core.config import settings


class MeilisearchService:
    """Service for managing Meilisearch operations."""

    def __init__(self):
        """Initialize Meilisearch client."""
        self.client = meilisearch.Client(
            settings.MEILISEARCH_URL,
            settings.MEILISEARCH_KEY
        )
        self.index_name = "pages"
        self._initialize_index()

    def _initialize_index(self):
        """Initialize or get the pages index with proper settings."""
        try:
            # Try to get existing index
            self.index = self.client.index(self.index_name)
        except Exception:
            # Create index if it doesn't exist
            self.client.create_index(self.index_name, {"primaryKey": "id"})
            self.index = self.client.index(self.index_name)

        # Configure searchable attributes
        self.index.update_searchable_attributes([
            "title",
            "meta_description",
            "h1",
            "text_content",
            "url",
        ])

        # Configure filterable attributes
        self.index.update_filterable_attributes([
            "project_id",
            "crawl_job_id",
            "status_code",
            "seo_score",
            "depth",
            "word_count",
        ])

        # Configure sortable attributes
        self.index.update_sortable_attributes([
            "seo_score",
            "word_count",
            "discovered_at",
        ])

    def index_page(self, page_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Index a single page.

        Args:
            page_data: Page data dictionary

        Returns:
            Meilisearch task info
        """
        # Prepare document for indexing
        document = {
            "id": page_data["id"],
            "project_id": page_data["project_id"],
            "crawl_job_id": page_data["crawl_job_id"],
            "url": page_data["url"],
            "title": page_data.get("title", ""),
            "meta_description": page_data.get("meta_description", ""),
            "h1": page_data.get("h1", ""),
            "text_content": page_data.get("text_content", "")[:5000],  # Limit content size
            "status_code": page_data.get("status_code"),
            "seo_score": page_data.get("seo_score", 0),
            "word_count": page_data.get("word_count", 0),
            "depth": page_data.get("depth", 0),
            "internal_links_count": page_data.get("internal_links_count", 0),
            "external_links_count": page_data.get("external_links_count", 0),
            "discovered_at": page_data.get("discovered_at"),
        }

        return self.index.add_documents([document])

    def index_pages_bulk(self, pages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Index multiple pages at once.

        Args:
            pages: List of page data dictionaries

        Returns:
            Meilisearch task info
        """
        documents = []
        for page in pages:
            documents.append({
                "id": page["id"],
                "project_id": page["project_id"],
                "crawl_job_id": page["crawl_job_id"],
                "url": page["url"],
                "title": page.get("title", ""),
                "meta_description": page.get("meta_description", ""),
                "h1": page.get("h1", ""),
                "text_content": page.get("text_content", "")[:5000],
                "status_code": page.get("status_code"),
                "seo_score": page.get("seo_score", 0),
                "word_count": page.get("word_count", 0),
                "depth": page.get("depth", 0),
                "internal_links_count": page.get("internal_links_count", 0),
                "external_links_count": page.get("external_links_count", 0),
                "discovered_at": str(page.get("discovered_at", "")),
            })

        print(f"Indexing {len(documents)} documents to Meilisearch")
        print(f"Sample document: {documents[0] if documents else 'None'}")

        task = self.index.add_documents(documents)

        # Wait for the task to complete
        print(f"Meilisearch task started: {task}")

        # Wait for task completion (with timeout)
        import time
        max_wait = 30  # 30 seconds max
        waited = 0

        while waited < max_wait:
            try:
                task_status = self.client.get_task(task.task_uid)
                print(f"Task status after {waited}s: {getattr(task_status, 'status', 'unknown')}")

                status = getattr(task_status, 'status', None)
                if status == 'succeeded':
                    print(f"✓ Indexing completed successfully after {waited}s")
                    break
                elif status == 'failed':
                    error = getattr(task_status, 'error', 'Unknown error')
                    print(f"✗ Indexing failed: {error}")
                    break

                time.sleep(1)
                waited += 1
            except Exception as e:
                print(f"Error checking task status: {e}")
                break

        return task

    def search(
        self,
        query: str,
        project_id: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        Search pages with full-text search.

        Args:
            query: Search query
            project_id: Filter by project ID
            filters: Additional filters (status_code, seo_score range, etc.)
            limit: Number of results to return
            offset: Pagination offset

        Returns:
            Search results with hits and metadata
        """
        # Build filter string
        filter_parts = []

        if project_id:
            filter_parts.append(f"project_id = {project_id}")

        if filters:
            if "status_code" in filters:
                filter_parts.append(f"status_code = {filters['status_code']}")

            if "min_seo_score" in filters:
                filter_parts.append(f"seo_score >= {filters['min_seo_score']}")

            if "max_seo_score" in filters:
                filter_parts.append(f"seo_score <= {filters['max_seo_score']}")

            if "min_word_count" in filters:
                filter_parts.append(f"word_count >= {filters['min_word_count']}")

        filter_string = " AND ".join(filter_parts) if filter_parts else None

        # Execute search
        results = self.index.search(
            query,
            {
                "filter": filter_string,
                "limit": limit,
                "offset": offset,
                "attributesToHighlight": ["title", "meta_description", "text_content"],
                "highlightPreTag": "<mark>",
                "highlightPostTag": "</mark>",
            }
        )

        return results

    def delete_page(self, page_id: int) -> Dict[str, Any]:
        """
        Delete a page from the index.

        Args:
            page_id: Page ID to delete

        Returns:
            Meilisearch task info
        """
        return self.index.delete_document(page_id)

    def delete_project_pages(self, project_id: int) -> Dict[str, Any]:
        """
        Delete all pages for a project.

        Args:
            project_id: Project ID

        Returns:
            Meilisearch task info
        """
        return self.index.delete_documents_by_filter(f"project_id = {project_id}")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get Meilisearch index statistics.

        Returns:
            Index statistics including document count
        """
        try:
            stats = self.index.get_stats()
            health = self.client.health()

            # Get values directly from object attributes
            number_of_documents = getattr(stats, 'number_of_documents', 0)
            is_indexing = getattr(stats, 'is_indexing', False)

            # field_distribution might be an object too, convert it
            field_dist = getattr(stats, 'field_distribution', {})
            if hasattr(field_dist, '__dict__'):
                # It's an object, convert to dict
                field_distribution = {k: v for k, v in field_dist.__dict__.items() if not k.startswith('_')}
            elif isinstance(field_dist, dict):
                field_distribution = field_dist
            else:
                field_distribution = {}

            # Handle health response
            if isinstance(health, dict):
                health_status = health.get("status", "unknown")
            else:
                health_status = getattr(health, 'status', 'unknown')

            return {
                "status": "healthy" if health_status == "available" else "unhealthy",
                "index_name": self.index_name,
                "number_of_documents": number_of_documents,
                "is_indexing": is_indexing,
                "field_distribution": field_distribution,
            }
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "error": str(e),
                "number_of_documents": 0,
            }


# Singleton instance
meilisearch_service = MeilisearchService()
