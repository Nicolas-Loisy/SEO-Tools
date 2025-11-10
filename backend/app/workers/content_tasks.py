"""Celery tasks for content generation."""

from app.workers.celery_app import celery_app


@celery_app.task(name="app.workers.content_tasks.generate_site_tree")
def generate_site_tree(project_id: int, keyword: str, depth: int = 3) -> dict:
    """
    Generate site architecture tree.

    Args:
        project_id: Project ID
        keyword: Main keyword/theme
        depth: Tree depth

    Returns:
        Generated tree structure
    """
    # TODO: Implement site tree generation using LLM adapter
    pass


@celery_app.task(name="app.workers.content_tasks.generate_content")
def generate_content(project_id: int, topic: str, keywords: list[str]) -> dict:
    """
    Generate SEO-optimized content.

    Args:
        project_id: Project ID
        topic: Content topic
        keywords: Target keywords

    Returns:
        Generated content
    """
    # TODO: Implement content generation using LLM adapter
    pass
