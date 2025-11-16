"""Link recommendation service for internal linking optimization."""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from sqlalchemy import select, and_, func
from sqlalchemy.orm import Session
import re

from app.models.page import Page
from app.services.keyword_extractor import keyword_extractor


@dataclass
class LinkSuggestion:
    """Represents a link recommendation."""
    source_page_id: int
    source_url: str
    target_page_id: int
    target_url: str
    target_title: str
    keyword: str
    context: str  # Text snippet where the link should be added
    position: int  # Character position in text
    score: float  # Recommendation confidence score (0-1)
    reason: str  # Why this link is recommended


class LinkRecommender:
    """Service for generating internal link recommendations."""

    def __init__(self):
        """Initialize the link recommender."""
        pass

    def get_recommendations(
        self,
        db: Session,
        page_id: int,
        project_id: int,
        max_suggestions: int = 20,
        max_target_pages: int = 500
    ) -> List[LinkSuggestion]:
        """
        Get link recommendations for a specific page.

        Args:
            db: Database session
            page_id: Source page ID
            project_id: Project ID
            max_suggestions: Maximum number of suggestions to return
            max_target_pages: Maximum target pages to consider (prevents timeout)

        Returns:
            List of link suggestions
        """
        # Get source page
        source_page = db.query(Page).filter(Page.id == page_id).first()
        if not source_page or not source_page.text_content:
            return []

        print(f"[LinkRecommender] Getting recommendations for page {page_id}, max_targets={max_target_pages}")

        # NEW: Using FAST frequency-based extraction (KeyBERT removed)
        # No need to limit text length - new method handles 50k+ chars in milliseconds
        print(f"[LinkRecommender] Extracting keywords from {len(source_page.text_content)} chars using FAST method")

        # Extract keywords from source page (fast method - can process full text)
        keywords = keyword_extractor.extract_keywords(
            source_page.text_content,  # Can use FULL text now!
            top_n=15  # Increased from 10 (extraction is now instant)
        )

        print(f"[LinkRecommender] Extracted {len(keywords)} keywords in <1ms")

        # Get pages in the same project (potential targets)
        # OPTIMIZATION: Limit to prevent timeout, prioritize by SEO score
        target_pages = db.query(Page).filter(
            and_(
                Page.project_id == project_id,
                Page.id != page_id,
                Page.text_content.isnot(None)
            )
        ).order_by(
            Page.seo_score.desc().nullslast()
        ).limit(max_target_pages).all()

        print(f"[LinkRecommender] Found {len(target_pages)} target pages, starting matching...")

        suggestions = []

        # For each keyword, find relevant target pages
        for idx, (keyword, keyword_score) in enumerate(keywords):
            if idx % 3 == 0:  # Log progress every 3 keywords
                print(f"[LinkRecommender] Processing keyword {idx+1}/{len(keywords)}")

            # Find pages that match this keyword
            matching_pages = self._find_matching_pages(
                keyword,
                target_pages,
                source_page
            )

            for target_page, relevance_score in matching_pages[:3]:  # Top 3 per keyword
                # Find where the keyword appears in source page
                positions = self._find_keyword_positions(
                    source_page.text_content,
                    keyword
                )

                for pos in positions[:2]:  # Max 2 positions per keyword
                    # Check if there's already a link near this position
                    if self._has_nearby_link(source_page, pos):
                        continue

                    # Extract context around the keyword
                    context = self._extract_context(
                        source_page.text_content,
                        pos,
                        keyword
                    )

                    # Calculate final score
                    final_score = self._calculate_score(
                        keyword_score,
                        relevance_score,
                        target_page
                    )

                    suggestions.append(LinkSuggestion(
                        source_page_id=source_page.id,
                        source_url=source_page.url,
                        target_page_id=target_page.id,
                        target_url=target_page.url,
                        target_title=target_page.title or target_page.url,
                        keyword=keyword,
                        context=context,
                        position=pos,
                        score=final_score,
                        reason=f"Content similarity on '{keyword}'"
                    ))

        # Sort by score and return top suggestions
        suggestions.sort(key=lambda x: x.score, reverse=True)

        print(f"[LinkRecommender] Generated {len(suggestions[:max_suggestions])} recommendations (from {len(suggestions)} total)")

        return suggestions[:max_suggestions]

    def _find_matching_pages(
        self,
        keyword: str,
        target_pages: List[Page],
        source_page: Page
    ) -> List[tuple[Page, float]]:
        """Find pages that match the keyword."""
        matches = []

        keyword_lower = keyword.lower()

        for page in target_pages:
            if not page.text_content:
                continue

            # Calculate relevance score
            score = 0.0

            # Check in title (highest weight)
            if page.title and keyword_lower in page.title.lower():
                score += 0.5

            # Check in H1
            if page.h1 and keyword_lower in page.h1.lower():
                score += 0.3

            # Check in meta description
            if page.meta_description and keyword_lower in page.meta_description.lower():
                score += 0.2

            # Check in content (count occurrences)
            content_lower = page.text_content.lower()
            occurrence_count = content_lower.count(keyword_lower)
            # Normalize by content length
            if occurrence_count > 0:
                score += min(occurrence_count / 10.0, 0.5)

            # Bonus for high SEO score
            if page.seo_score:
                score += (page.seo_score / 100.0) * 0.2

            if score > 0:
                matches.append((page, score))

        # Sort by relevance
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches

    def _find_keyword_positions(self, text: str, keyword: str) -> List[int]:
        """Find all positions where keyword appears in text."""
        positions = []
        text_lower = text.lower()
        keyword_lower = keyword.lower()

        start = 0
        while True:
            pos = text_lower.find(keyword_lower, start)
            if pos == -1:
                break
            positions.append(pos)
            start = pos + len(keyword)

        return positions

    def _has_nearby_link(self, page: Page, position: int, radius: int = 100) -> bool:
        """Check if there's already a link near this position."""
        # Simple heuristic: check if <a> tag exists nearby
        if not page.rendered_html:
            return False

        start = max(0, position - radius)
        end = min(len(page.rendered_html), position + radius)
        snippet = page.rendered_html[start:end]

        return '<a ' in snippet or '</a>' in snippet

    def _extract_context(
        self,
        text: str,
        position: int,
        keyword: str,
        context_size: int = 150
    ) -> str:
        """Extract context around the keyword."""
        start = max(0, position - context_size)
        end = min(len(text), position + len(keyword) + context_size)

        context = text[start:end]

        # Add ellipsis if truncated
        if start > 0:
            context = '...' + context
        if end < len(text):
            context = context + '...'

        return context.strip()

    def _calculate_score(
        self,
        keyword_score: float,
        relevance_score: float,
        target_page: Page
    ) -> float:
        """Calculate final recommendation score."""
        # Combine scores
        score = (keyword_score * 0.4) + (relevance_score * 0.6)

        # Bonus for pages at optimal depth (2-3)
        if 2 <= target_page.depth <= 3:
            score *= 1.1

        # Penalty for very deep pages
        if target_page.depth > 5:
            score *= 0.8

        return min(score, 1.0)


# Singleton instance
link_recommender = LinkRecommender()
