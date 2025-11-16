"""Advanced site architecture generator using keyword clustering and LLM."""

import json
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import numpy as np
from sklearn.cluster import KMeans
from app.services.google_autocomplete import google_autocomplete
from app.services.llm_adapter import llm_adapter


@dataclass
class ClusterResult:
    """Result of keyword clustering."""
    cluster_id: int
    keywords: List[str]
    centroid_keyword: str  # Most representative keyword


class ArchitectureGenerator:
    """
    Advanced site architecture generator.

    Workflow:
    1. Google Autocomplete → keyword suggestions
    2. LLM embeddings → vectorization
    3. K-means clustering → semantic grouping
    4. LLM → hierarchical structure with SEO metadata
    """

    def __init__(self):
        """Initialize architecture generator."""
        pass

    async def generate_architecture(
        self,
        topic: str,
        language: str = "en",
        country: str = "us",
        max_keywords: int = 100,
        num_clusters: int = 5,
        depth: int = 3,
        provider: str = "openai",
    ) -> Dict[str, Any]:
        """
        Generate complete site architecture.

        Args:
            topic: Main topic/keyword
            language: Language code (en, fr, etc.)
            country: Country code (us, fr, etc.)
            max_keywords: Max keywords to gather from Google
            num_clusters: Number of semantic clusters
            depth: Tree depth (1-5)
            provider: LLM provider

        Returns:
            Complete architecture with tree structure
        """
        # Step 1: Get keyword suggestions from Google Autocomplete
        print(f"[ArchGen] Step 1: Fetching keywords from Google Autocomplete...")
        keywords = await self._fetch_keywords(topic, language, country, max_keywords)
        print(f"[ArchGen] Found {len(keywords)} keywords")

        if len(keywords) < 3:
            # Fallback: use simple LLM generation if not enough keywords
            print("[ArchGen] Not enough keywords, using LLM-only generation")
            return await self._generate_simple_architecture(topic, depth, language, provider)

        # Step 2: Generate embeddings for all keywords
        print(f"[ArchGen] Step 2: Generating embeddings...")
        embeddings = await self._generate_embeddings(keywords, provider)
        print(f"[ArchGen] Generated embeddings: {len(embeddings)} vectors")

        # Step 3: Cluster keywords semantically
        print(f"[ArchGen] Step 3: Clustering keywords into {num_clusters} groups...")
        clusters = self._cluster_keywords(keywords, embeddings, num_clusters)
        print(f"[ArchGen] Created {len(clusters)} clusters")

        # Step 4: Generate hierarchical structure using LLM
        print(f"[ArchGen] Step 4: Generating tree structure with LLM...")
        tree = await self._build_tree_from_clusters(
            topic, clusters, depth, language, provider
        )
        print(f"[ArchGen] Tree generated successfully")

        return {
            "topic": topic,
            "language": language,
            "total_keywords": len(keywords),
            "num_clusters": len(clusters),
            "depth": depth,
            "tree": tree,
            "clusters": [
                {
                    "id": c.cluster_id,
                    "keywords": c.keywords,
                    "centroid": c.centroid_keyword,
                }
                for c in clusters
            ],
        }

    async def _fetch_keywords(
        self,
        topic: str,
        language: str,
        country: str,
        max_keywords: int,
    ) -> List[str]:
        """
        Fetch keyword suggestions from Google Autocomplete.

        Args:
            topic: Main topic
            language: Language code
            country: Country code
            max_keywords: Maximum keywords to fetch

        Returns:
            List of keyword suggestions
        """
        # Configure scraper
        google_autocomplete.language = language
        google_autocomplete.country = country

        # Get comprehensive suggestions
        keywords = await google_autocomplete.get_comprehensive_suggestions(
            keyword=topic,
            use_alphabet=True,
            use_questions=True,
            max_suggestions=max_keywords,
        )

        # Always include the main topic
        if topic not in keywords:
            keywords.insert(0, topic)

        return keywords

    async def _generate_embeddings(
        self,
        keywords: List[str],
        provider: str,
    ) -> np.ndarray:
        """
        Generate embeddings for keywords using LLM.

        Args:
            keywords: List of keywords
            provider: LLM provider

        Returns:
            NumPy array of embeddings (shape: [n_keywords, embedding_dim])
        """
        embeddings = []

        # Generate embeddings in batches for efficiency
        batch_size = 20
        for i in range(0, len(keywords), batch_size):
            batch = keywords[i:i + batch_size]

            for keyword in batch:
                try:
                    # Use LLM adapter to generate embedding
                    embedding = await llm_adapter.generate_embedding(
                        text=keyword,
                        provider=provider,
                    )
                    embeddings.append(embedding)
                except Exception as e:
                    print(f"[ArchGen] Error generating embedding for '{keyword}': {e}")
                    # Fallback: random embedding (should rarely happen)
                    embeddings.append(np.random.rand(1536).tolist())

        return np.array(embeddings)

    def _cluster_keywords(
        self,
        keywords: List[str],
        embeddings: np.ndarray,
        num_clusters: int,
    ) -> List[ClusterResult]:
        """
        Cluster keywords using K-means on embeddings.

        Args:
            keywords: List of keywords
            embeddings: Embeddings matrix
            num_clusters: Number of clusters

        Returns:
            List of cluster results
        """
        # Adjust num_clusters if we have fewer keywords
        num_clusters = min(num_clusters, len(keywords))

        # Run K-means clustering
        kmeans = KMeans(n_clusters=num_clusters, random_state=42, n_init=10)
        cluster_labels = kmeans.fit_predict(embeddings)

        # Group keywords by cluster
        clusters_dict: Dict[int, List[Tuple[str, float]]] = {}

        for i, label in enumerate(cluster_labels):
            keyword = keywords[i]
            # Calculate distance to centroid
            distance = np.linalg.norm(embeddings[i] - kmeans.cluster_centers_[label])

            if label not in clusters_dict:
                clusters_dict[label] = []

            clusters_dict[label].append((keyword, distance))

        # Create ClusterResult objects
        clusters = []
        for cluster_id, kw_distances in clusters_dict.items():
            # Sort by distance to centroid (ascending)
            kw_distances.sort(key=lambda x: x[1])

            # Extract just keywords
            cluster_keywords = [kw for kw, _ in kw_distances]

            # Centroid keyword is the closest one
            centroid_keyword = cluster_keywords[0]

            clusters.append(
                ClusterResult(
                    cluster_id=cluster_id,
                    keywords=cluster_keywords,
                    centroid_keyword=centroid_keyword,
                )
            )

        return clusters

    async def _build_tree_from_clusters(
        self,
        topic: str,
        clusters: List[ClusterResult],
        depth: int,
        language: str,
        provider: str,
    ) -> Dict[str, Any]:
        """
        Build hierarchical tree structure from clusters using LLM.

        Args:
            topic: Main topic
            clusters: Keyword clusters
            depth: Tree depth
            language: Language code
            provider: LLM provider

        Returns:
            Tree structure dictionary
        """
        # Build prompt for LLM
        system_prompt = self._get_system_prompt(language)
        user_prompt = self._build_tree_prompt(topic, clusters, depth, language)

        # Generate tree with LLM
        response = await llm_adapter.generate_text(
            prompt=user_prompt,
            system_prompt=system_prompt,
            provider=provider,
            max_tokens=3000,
            temperature=0.7,
        )

        # Parse JSON response
        tree = self._parse_tree_response(response)

        # Enrich tree with metadata
        tree = self._enrich_tree(tree, 0)

        return tree

    def _build_tree_prompt(
        self,
        topic: str,
        clusters: List[ClusterResult],
        depth: int,
        language: str,
    ) -> str:
        """Build LLM prompt for tree generation."""
        clusters_text = ""
        for i, cluster in enumerate(clusters, 1):
            top_keywords = cluster.keywords[:10]  # Show top 10 per cluster
            clusters_text += f"\nCluster {i} (theme: {cluster.centroid_keyword}):\n"
            clusters_text += "- " + "\n- ".join(top_keywords) + "\n"

        lang_instruction = (
            "Répondez en français." if language == "fr"
            else "Respond in English."
        )

        prompt = f"""Generate a comprehensive SEO-optimized site architecture for the topic: "{topic}"

I have performed semantic clustering on {len(clusters)} keyword groups from Google Autocomplete:
{clusters_text}

Create a hierarchical site structure with {depth} levels that:
1. Uses these keyword clusters to inform the structure
2. Creates logical categories based on semantic grouping
3. Assigns SEO-optimized titles, slugs, and meta descriptions
4. Follows information architecture best practices
5. Ensures clear parent-child relationships

{lang_instruction}

Output ONLY valid JSON in this exact format:
{{
  "name": "Homepage Title",
  "slug": "/",
  "keyword": "{topic}",
  "title": "SEO Title (60 chars)",
  "meta_description": "Meta description (155 chars)",
  "priority": "critical",
  "children": [
    {{
      "name": "Category Name",
      "slug": "/category-slug",
      "keyword": "target keyword",
      "title": "Category SEO Title",
      "meta_description": "Category meta description",
      "priority": "high",
      "children": [...]
    }}
  ]
}}

Generate the complete tree structure as valid JSON:"""

        return prompt

    def _parse_tree_response(self, response: str) -> Dict[str, Any]:
        """
        Parse LLM response to extract JSON tree.

        Args:
            response: LLM response text

        Returns:
            Parsed tree dictionary
        """
        # Try to extract JSON from markdown code blocks
        json_match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", response, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Try to find JSON directly
            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                raise ValueError("No valid JSON found in LLM response")

        try:
            tree_data = json.loads(json_str)
            return tree_data
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON tree: {e}")

    def _enrich_tree(
        self,
        tree: Dict[str, Any],
        level: int,
    ) -> Dict[str, Any]:
        """
        Enrich tree with computed metadata.

        Args:
            tree: Tree node
            level: Current depth level

        Returns:
            Enriched tree node
        """
        # Add level
        tree["level"] = level

        # Set default priority if missing
        if "priority" not in tree:
            if level == 0:
                tree["priority"] = "critical"
            elif level == 1:
                tree["priority"] = "high"
            else:
                tree["priority"] = "medium"

        # Set target word count
        if "target_word_count" not in tree:
            if level == 0:
                tree["target_word_count"] = 1500
            elif level == 1:
                tree["target_word_count"] = 1200
            else:
                tree["target_word_count"] = 800

        # Ensure slug format
        if "slug" in tree and not tree["slug"].startswith("/"):
            tree["slug"] = "/" + tree["slug"]

        # Recursively enrich children
        if "children" in tree and isinstance(tree["children"], list):
            tree["children"] = [
                self._enrich_tree(child, level + 1)
                for child in tree["children"]
            ]

        return tree

    async def _generate_simple_architecture(
        self,
        topic: str,
        depth: int,
        language: str,
        provider: str,
    ) -> Dict[str, Any]:
        """
        Fallback: Simple LLM-only generation when not enough keywords.

        Args:
            topic: Main topic
            depth: Tree depth
            language: Language
            provider: LLM provider

        Returns:
            Simple architecture structure
        """
        system_prompt = self._get_system_prompt(language)

        user_prompt = f"""Generate a site architecture for: "{topic}"

Create a {depth}-level structure with SEO-optimized pages.

Output valid JSON with this structure:
{{
  "name": "Homepage",
  "slug": "/",
  "keyword": "{topic}",
  "title": "SEO Title",
  "meta_description": "Meta description",
  "priority": "critical",
  "children": [...]
}}"""

        response = await llm_adapter.generate_text(
            prompt=user_prompt,
            system_prompt=system_prompt,
            provider=provider,
            max_tokens=2000,
        )

        tree = self._parse_tree_response(response)
        tree = self._enrich_tree(tree, 0)

        return {
            "topic": topic,
            "language": language,
            "total_keywords": 0,
            "num_clusters": 0,
            "depth": depth,
            "tree": tree,
            "clusters": [],
        }

    def _get_system_prompt(self, language: str) -> str:
        """Get system prompt for LLM."""
        if language == "fr":
            return (
                "Vous êtes un expert en architecture de l'information et SEO. "
                "Vous créez des structures de site optimisées pour les moteurs de recherche "
                "en utilisant l'analyse sémantique des mots-clés. "
                "Vous répondez UNIQUEMENT en JSON valide, sans texte additionnel."
            )
        else:
            return (
                "You are an information architecture and SEO expert. "
                "You create SEO-optimized site structures using semantic keyword analysis. "
                "You respond ONLY with valid JSON, no additional text."
            )

    def flatten_tree(self, tree: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Flatten tree into list of pages.

        Args:
            tree: Hierarchical tree

        Returns:
            Flat list of pages
        """
        pages = []

        def traverse(node: Dict[str, Any], parent_slug: Optional[str] = None):
            node_copy = node.copy()
            children = node_copy.pop("children", [])

            node_copy["parent_slug"] = parent_slug
            pages.append(node_copy)

            for child in children:
                traverse(child, node_copy["slug"])

        traverse(tree)
        return pages


# Singleton instance
architecture_generator = ArchitectureGenerator()
