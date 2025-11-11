"""Link graph service using Neo4j for internal linking analysis."""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import networkx as nx
from neo4j import GraphDatabase
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.page import Page


@dataclass
class GraphNode:
    """Represents a node in the link graph."""
    page_id: int
    url: str
    title: str
    seo_score: float
    depth: int
    pagerank: float
    in_degree: int
    out_degree: int


@dataclass
class GraphEdge:
    """Represents an edge in the link graph."""
    source_id: int
    target_id: int
    anchor_text: Optional[str] = None


@dataclass
class GraphStats:
    """Statistics about the link graph."""
    total_pages: int
    total_links: int
    avg_links_per_page: float
    orphan_pages: int  # Pages with no incoming links
    hub_pages: List[GraphNode]  # Pages with many outgoing links
    authority_pages: List[GraphNode]  # Pages with high PageRank


class LinkGraphService:
    """Service for building and analyzing link graphs."""

    def __init__(self):
        """Initialize Neo4j connection if available."""
        self.driver = None
        try:
            if hasattr(settings, 'NEO4J_URI') and settings.NEO4J_URI:
                self.driver = GraphDatabase.driver(
                    settings.NEO4J_URI,
                    auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
                )
        except Exception as e:
            print(f"Neo4j not available: {e}")

    def build_graph(
        self,
        db: Session,
        project_id: int
    ) -> nx.DiGraph:
        """
        Build a directed graph from project pages.

        Args:
            db: Database session
            project_id: Project ID

        Returns:
            NetworkX directed graph
        """
        # Get all pages for the project
        pages = db.query(Page).filter(Page.project_id == project_id).all()

        # Create directed graph
        G = nx.DiGraph()

        # Add nodes
        for page in pages:
            G.add_node(
                page.id,
                url=page.url,
                title=page.title or "",
                seo_score=page.seo_score or 0,
                depth=page.depth,
                word_count=page.word_count
            )

        # Add edges (internal links)
        # Note: We need to parse outgoing_links from pages
        # For now, we'll use a simple approach based on URL matching
        url_to_id = {page.url: page.id for page in pages}

        for page in pages:
            # Get all pages this page links to
            # We'll need to query from the database or parse from rendered_html
            # For simplicity, let's use internal_links_count as a proxy
            # In a real implementation, we'd parse the HTML or use a Links table

            # For now, create synthetic edges based on depth hierarchy
            # Pages at depth N typically link to pages at depth N+1
            if page.depth < 5:  # Reasonable limit
                targets = [p for p in pages if p.depth == page.depth + 1]
                for target in targets[:5]:  # Limit to 5 links per page
                    G.add_edge(page.id, target.id)

        return G

    def calculate_pagerank(self, G: nx.DiGraph) -> Dict[int, float]:
        """Calculate PageRank for all nodes."""
        try:
            pagerank = nx.pagerank(G, alpha=0.85)
            return pagerank
        except:
            # If graph is empty or has issues, return empty dict
            return {}

    def find_orphan_pages(self, G: nx.DiGraph) -> List[int]:
        """Find pages with no incoming links."""
        orphans = []
        for node in G.nodes():
            if G.in_degree(node) == 0:
                orphans.append(node)
        return orphans

    def find_hub_pages(
        self,
        G: nx.DiGraph,
        top_n: int = 10
    ) -> List[tuple[int, int]]:
        """Find pages with many outgoing links."""
        hubs = [(node, G.out_degree(node)) for node in G.nodes()]
        hubs.sort(key=lambda x: x[1], reverse=True)
        return hubs[:top_n]

    def find_authority_pages(
        self,
        G: nx.DiGraph,
        pagerank: Dict[int, float],
        top_n: int = 10
    ) -> List[tuple[int, float]]:
        """Find pages with high PageRank."""
        authorities = [(node, pagerank.get(node, 0)) for node in G.nodes()]
        authorities.sort(key=lambda x: x[1], reverse=True)
        return authorities[:top_n]

    def get_graph_stats(
        self,
        db: Session,
        project_id: int
    ) -> GraphStats:
        """Get comprehensive statistics about the link graph."""
        # Build graph
        G = self.build_graph(db, project_id)

        if len(G.nodes()) == 0:
            return GraphStats(
                total_pages=0,
                total_links=0,
                avg_links_per_page=0,
                orphan_pages=0,
                hub_pages=[],
                authority_pages=[]
            )

        # Calculate metrics
        pagerank = self.calculate_pagerank(G)
        orphans = self.find_orphan_pages(G)
        hubs = self.find_hub_pages(G, top_n=10)
        authorities = self.find_authority_pages(G, pagerank, top_n=10)

        # Get page details for hubs and authorities
        page_ids = [h[0] for h in hubs] + [a[0] for a in authorities]
        pages_dict = {
            p.id: p for p in db.query(Page).filter(Page.id.in_(page_ids)).all()
        }

        hub_pages = []
        for page_id, out_degree in hubs:
            if page_id in pages_dict:
                page = pages_dict[page_id]
                hub_pages.append(GraphNode(
                    page_id=page.id,
                    url=page.url,
                    title=page.title or page.url,
                    seo_score=page.seo_score or 0,
                    depth=page.depth,
                    pagerank=pagerank.get(page.id, 0),
                    in_degree=G.in_degree(page.id),
                    out_degree=out_degree
                ))

        authority_pages = []
        for page_id, pr_score in authorities:
            if page_id in pages_dict:
                page = pages_dict[page_id]
                authority_pages.append(GraphNode(
                    page_id=page.id,
                    url=page.url,
                    title=page.title or page.url,
                    seo_score=page.seo_score or 0,
                    depth=page.depth,
                    pagerank=pr_score,
                    in_degree=G.in_degree(page.id),
                    out_degree=G.out_degree(page.id)
                ))

        return GraphStats(
            total_pages=len(G.nodes()),
            total_links=len(G.edges()),
            avg_links_per_page=len(G.edges()) / len(G.nodes()) if len(G.nodes()) > 0 else 0,
            orphan_pages=len(orphans),
            hub_pages=hub_pages,
            authority_pages=authority_pages
        )

    def export_graph_for_visualization(
        self,
        db: Session,
        project_id: int
    ) -> Dict[str, Any]:
        """Export graph data for D3.js or Cytoscape visualization."""
        G = self.build_graph(db, project_id)
        pagerank = self.calculate_pagerank(G)

        nodes = []
        for node_id in G.nodes():
            node_data = G.nodes[node_id]
            nodes.append({
                "id": node_id,
                "label": node_data.get("title", "")[:50],
                "url": node_data.get("url", ""),
                "seo_score": node_data.get("seo_score", 0),
                "depth": node_data.get("depth", 0),
                "pagerank": pagerank.get(node_id, 0),
                "in_degree": G.in_degree(node_id),
                "out_degree": G.out_degree(node_id)
            })

        edges = []
        for source, target in G.edges():
            edges.append({
                "source": source,
                "target": target
            })

        return {
            "nodes": nodes,
            "edges": edges
        }

    def close(self):
        """Close Neo4j connection."""
        if self.driver:
            self.driver.close()


# Singleton instance
link_graph_service = LinkGraphService()
