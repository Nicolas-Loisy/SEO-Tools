"""Internal linking graph analysis and recommendations."""

from typing import List, Dict, Any, Set, Tuple
from collections import defaultdict
import numpy as np


class LinkGraphService:
    """
    Service for analyzing internal linking structure and generating recommendations.

    Uses graph algorithms to compute metrics and semantic similarity for suggestions.
    """

    def compute_metrics(self, pages: List[Any], links: List[Any]) -> Dict[str, Any]:
        """
        Compute graph metrics.

        Args:
            pages: List of Page objects
            links: List of Link objects

        Returns:
            Metrics dictionary
        """
        if not pages:
            return {}

        # Build adjacency lists
        outgoing = defaultdict(list)
        incoming = defaultdict(int)

        for link in links:
            outgoing[link.source_page_id].append(link.target_page_id)
            incoming[link.target_page_id] += 1

        # Compute metrics
        total_pages = len(pages)
        total_links = len(links)
        avg_outgoing = total_links / total_pages if total_pages > 0 else 0

        # Find orphan pages (no incoming links)
        orphan_pages = [p.id for p in pages if incoming.get(p.id, 0) == 0]

        # Find hub pages (many outgoing links)
        hub_threshold = avg_outgoing * 2
        hub_pages = [
            page_id for page_id, targets in outgoing.items() if len(targets) >= hub_threshold
        ]

        # Compute PageRank-like score
        page_scores = self._compute_page_importance(pages, links)

        return {
            "total_pages": total_pages,
            "total_links": total_links,
            "avg_links_per_page": round(avg_outgoing, 2),
            "orphan_pages": len(orphan_pages),
            "hub_pages": len(hub_pages),
            "max_incoming_links": max(incoming.values()) if incoming else 0,
            "pages_with_no_outgoing": sum(1 for p in pages if p.id not in outgoing),
        }

    def _compute_page_importance(
        self, pages: List[Any], links: List[Any], damping: float = 0.85, iterations: int = 20
    ) -> Dict[int, float]:
        """
        Compute PageRank-like importance scores.

        Args:
            pages: List of Page objects
            links: List of Link objects
            damping: Damping factor (default: 0.85)
            iterations: Number of iterations

        Returns:
            Dict mapping page_id to importance score
        """
        if not pages:
            return {}

        # Build graph
        page_ids = [p.id for p in pages]
        n = len(page_ids)
        id_to_idx = {pid: i for i, pid in enumerate(page_ids)}

        # Outgoing links per page
        outgoing = defaultdict(list)
        for link in links:
            if link.source_page_id in id_to_idx and link.target_page_id in id_to_idx:
                outgoing[link.source_page_id].append(link.target_page_id)

        # Initialize scores
        scores = np.ones(n) / n

        # Iterate
        for _ in range(iterations):
            new_scores = np.ones(n) * (1 - damping) / n

            for i, page_id in enumerate(page_ids):
                # Find pages linking to this page
                for src_id, targets in outgoing.items():
                    if page_id in targets:
                        src_idx = id_to_idx[src_id]
                        new_scores[i] += damping * scores[src_idx] / len(targets)

            scores = new_scores

        return {page_id: float(scores[i]) for i, page_id in enumerate(page_ids)}

    def generate_recommendations(
        self, pages: List[Any], top_k: int = 5, similarity_threshold: float = 0.6
    ) -> Dict[int, List[Dict[str, Any]]]:
        """
        Generate internal link recommendations based on semantic similarity.

        Args:
            pages: List of Page objects with embeddings
            top_k: Number of recommendations per page
            similarity_threshold: Minimum similarity score

        Returns:
            Dict mapping source_page_id to list of recommendation dicts
        """
        recommendations = {}

        # Filter pages with embeddings
        pages_with_embeddings = [p for p in pages if p.embedding is not None]

        if len(pages_with_embeddings) < 2:
            return recommendations

        # Compute pairwise similarities
        embeddings = np.array([p.embedding for p in pages_with_embeddings])

        for i, source_page in enumerate(pages_with_embeddings):
            # Compute similarities to all other pages
            source_emb = embeddings[i]
            similarities = np.dot(embeddings, source_emb)

            # Get top-k similar pages (excluding self)
            similar_indices = np.argsort(similarities)[::-1][1 : top_k + 1]

            page_recommendations = []
            for idx in similar_indices:
                sim_score = float(similarities[idx])

                if sim_score >= similarity_threshold:
                    target_page = pages_with_embeddings[idx]
                    page_recommendations.append(
                        {
                            "target_page_id": target_page.id,
                            "target_url": target_page.url,
                            "target_title": target_page.title,
                            "similarity_score": round(sim_score, 3),
                            "reason": "semantic_similarity",
                        }
                    )

            if page_recommendations:
                recommendations[source_page.id] = page_recommendations

        return recommendations

    def find_missing_links(
        self, pages: List[Any], existing_links: List[Any], recommendations: Dict[int, List[Dict]]
    ) -> List[Dict[str, Any]]:
        """
        Find recommended links that don't exist yet.

        Args:
            pages: List of Page objects
            existing_links: List of existing Link objects
            recommendations: Recommendations from generate_recommendations

        Returns:
            List of missing link suggestions
        """
        # Build set of existing links
        existing = {(link.source_page_id, link.target_page_id) for link in existing_links}

        missing_links = []

        for source_id, recs in recommendations.items():
            for rec in recs:
                target_id = rec["target_page_id"]

                if (source_id, target_id) not in existing:
                    missing_links.append(
                        {
                            "source_page_id": source_id,
                            "target_page_id": target_id,
                            "similarity_score": rec["similarity_score"],
                            "priority": "high"
                            if rec["similarity_score"] > 0.8
                            else "medium",
                        }
                    )

        # Sort by similarity score
        missing_links.sort(key=lambda x: x["similarity_score"], reverse=True)

        return missing_links

    def detect_link_opportunities(
        self, pages: List[Any], links: List[Any]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Detect various link opportunities.

        Args:
            pages: List of Page objects
            links: List of Link objects

        Returns:
            Dict with different types of opportunities
        """
        # Build incoming/outgoing maps
        incoming_count = defaultdict(int)
        outgoing_count = defaultdict(int)

        for link in links:
            outgoing_count[link.source_page_id] += 1
            incoming_count[link.target_page_id] += 1

        opportunities = {
            "orphan_pages": [],  # Pages with no incoming links
            "hub_candidates": [],  # Pages that could be hubs
            "underlinked_pages": [],  # Important pages with few incoming links
        }

        for page in pages:
            page_id = page.id

            # Orphan pages
            if incoming_count.get(page_id, 0) == 0:
                opportunities["orphan_pages"].append(
                    {"page_id": page_id, "url": page.url, "title": page.title}
                )

            # Underlinked pages (have content but few links)
            if page.word_count > 300 and incoming_count.get(page_id, 0) < 2:
                opportunities["underlinked_pages"].append(
                    {
                        "page_id": page_id,
                        "url": page.url,
                        "title": page.title,
                        "incoming_links": incoming_count.get(page_id, 0),
                    }
                )

        return opportunities
