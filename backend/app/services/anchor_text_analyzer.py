"""Anchor text analysis service for internal linking optimization."""

from typing import List, Dict, Any, Tuple
from collections import Counter
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.page import Link


# Generic anchors that should be avoided for SEO
GENERIC_ANCHORS_EN = {
    'click here', 'here', 'read more', 'learn more', 'more', 'continue reading',
    'click', 'link', 'this page', 'this link', 'this article', 'view more',
    'see more', 'more info', 'more information', 'details', 'info'
}

GENERIC_ANCHORS_FR = {
    'cliquez ici', 'ici', 'lire la suite', 'en savoir plus', 'plus', 'suite',
    'cliquer', 'lien', 'cette page', 'ce lien', 'cet article', 'voir plus',
    'plus d\'info', 'plus d\'informations', 'détails', 'info', 'continuer'
}

GENERIC_ANCHORS = GENERIC_ANCHORS_EN | GENERIC_ANCHORS_FR


class AnchorTextAnalyzer:
    """Service for analyzing anchor text distribution and quality."""

    def get_anchor_text_stats(
        self,
        db: Session,
        project_id: int,
        max_pages: int = 1000
    ) -> Dict[str, Any]:
        """
        Analyze anchor text distribution for a project.

        Args:
            db: Database session
            project_id: Project ID
            max_pages: Maximum pages to analyze

        Returns:
            Dictionary with anchor text statistics
        """
        from app.models.page import Page

        # Get all pages for this project (limited)
        pages = db.query(Page).filter(
            Page.project_id == project_id
        ).order_by(
            Page.seo_score.desc().nullslast()
        ).limit(max_pages).all()

        page_ids = [page.id for page in pages]

        # Get all internal links with anchor text
        links = db.query(Link).filter(
            Link.source_page_id.in_(page_ids),
            Link.target_page_id.in_(page_ids),
            Link.is_internal == True,
            Link.anchor_text.isnot(None),
            Link.anchor_text != ''
        ).all()

        if not links:
            return {
                "total_links": 0,
                "links_with_anchor_text": 0,
                "links_without_anchor_text": 0,
                "generic_anchors_count": 0,
                "generic_anchors_percentage": 0,
                "top_anchor_texts": [],
                "generic_anchors": [],
                "over_optimized_anchors": [],
                "average_anchor_length": 0
            }

        # Count total links (with and without anchor text)
        total_links_query = db.query(func.count(Link.id)).filter(
            Link.source_page_id.in_(page_ids),
            Link.target_page_id.in_(page_ids),
            Link.is_internal == True
        ).scalar()

        # Analyze anchor texts
        anchor_texts = [link.anchor_text.strip().lower() for link in links if link.anchor_text]
        anchor_counter = Counter(anchor_texts)

        # Detect generic anchors
        generic_anchors = []
        for anchor, count in anchor_counter.items():
            if anchor in GENERIC_ANCHORS:
                generic_anchors.append({
                    "anchor_text": anchor,
                    "count": count,
                    "percentage": round((count / len(links)) * 100, 2)
                })

        # Sort by count descending
        generic_anchors.sort(key=lambda x: x["count"], reverse=True)

        # Get top anchor texts
        top_anchor_texts = [
            {
                "anchor_text": anchor,
                "count": count,
                "percentage": round((count / len(links)) * 100, 2)
            }
            for anchor, count in anchor_counter.most_common(20)
        ]

        # Detect over-optimization (same anchor used too many times)
        # Rule: If an anchor text is used more than 5% of total links, it might be over-optimized
        over_optimized = []
        for anchor, count in anchor_counter.items():
            percentage = (count / len(links)) * 100
            if percentage > 5 and anchor not in GENERIC_ANCHORS:  # Ignore generic anchors
                over_optimized.append({
                    "anchor_text": anchor,
                    "count": count,
                    "percentage": round(percentage, 2),
                    "severity": "high" if percentage > 10 else "medium"
                })

        # Sort by percentage descending
        over_optimized.sort(key=lambda x: x["percentage"], reverse=True)

        # Calculate average anchor length
        avg_length = sum(len(anchor) for anchor in anchor_texts) / len(anchor_texts) if anchor_texts else 0

        return {
            "total_links": total_links_query,
            "links_with_anchor_text": len(links),
            "links_without_anchor_text": total_links_query - len(links),
            "generic_anchors_count": len(generic_anchors),
            "generic_anchors_percentage": round((sum(g["count"] for g in generic_anchors) / len(links)) * 100, 2) if links else 0,
            "top_anchor_texts": top_anchor_texts,
            "generic_anchors": generic_anchors[:10],  # Top 10 generic anchors
            "over_optimized_anchors": over_optimized[:10],  # Top 10 over-optimized
            "average_anchor_length": round(avg_length, 1),
            "unique_anchor_texts": len(anchor_counter)
        }

    def get_anchor_text_recommendations(
        self,
        db: Session,
        project_id: int,
        max_pages: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Generate recommendations for improving anchor text.

        Args:
            db: Database session
            project_id: Project ID
            max_pages: Maximum pages to analyze

        Returns:
            List of recommendations
        """
        stats = self.get_anchor_text_stats(db, project_id, max_pages)
        recommendations = []

        # Recommendation 1: Too many generic anchors
        if stats["generic_anchors_percentage"] > 20:
            recommendations.append({
                "type": "generic_anchors",
                "severity": "high" if stats["generic_anchors_percentage"] > 30 else "medium",
                "title": "Too Many Generic Anchor Texts",
                "message": f"{stats['generic_anchors_percentage']}% of your links use generic anchor text like 'click here' or 'read more'. Use descriptive anchor text that includes keywords.",
                "count": stats["generic_anchors_count"]
            })

        # Recommendation 2: Over-optimization
        if stats["over_optimized_anchors"]:
            high_severity = [a for a in stats["over_optimized_anchors"] if a["severity"] == "high"]
            if high_severity:
                recommendations.append({
                    "type": "over_optimization",
                    "severity": "high",
                    "title": "Over-Optimized Anchor Texts Detected",
                    "message": f"{len(high_severity)} anchor text(s) are used too frequently (>10% of links). This may appear unnatural to search engines. Vary your anchor text.",
                    "examples": [a["anchor_text"] for a in high_severity[:3]]
                })

        # Recommendation 3: Empty anchor texts
        if stats["links_without_anchor_text"] > stats["links_with_anchor_text"] * 0.3:
            recommendations.append({
                "type": "empty_anchors",
                "severity": "medium",
                "title": "Many Links Without Anchor Text",
                "message": f"{stats['links_without_anchor_text']} links ({round((stats['links_without_anchor_text'] / stats['total_links']) * 100, 1)}%) have no anchor text. Add descriptive text to improve SEO.",
                "count": stats["links_without_anchor_text"]
            })

        # Recommendation 4: Anchor text too short
        if stats["average_anchor_length"] < 15:
            recommendations.append({
                "type": "short_anchors",
                "severity": "low",
                "title": "Anchor Texts Are Too Short",
                "message": f"Average anchor text length is {stats['average_anchor_length']} characters. Consider using more descriptive anchor text (2-5 words is ideal).",
                "average_length": stats["average_anchor_length"]
            })

        # Recommendation 5: Good anchor text usage
        if stats["generic_anchors_percentage"] < 10 and not stats["over_optimized_anchors"]:
            recommendations.append({
                "type": "success",
                "severity": "success",
                "title": "Good Anchor Text Distribution",
                "message": "Your anchor texts are well-distributed and descriptive. Keep up the good work!",
            })

        return recommendations


# Singleton instance
anchor_text_analyzer = AnchorTextAnalyzer()
