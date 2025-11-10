"""Semantic embeddings service using sentence-transformers."""

from typing import List
import numpy as np
from sentence_transformers import SentenceTransformer


class EmbeddingService:
    """
    Service for generating semantic embeddings from text.

    Uses sentence-transformers to create vector representations for
    semantic similarity search.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize embedding service.

        Args:
            model_name: Sentence-transformers model to use
                       Default: all-MiniLM-L6-v2 (384 dims, fast, good quality)
                       Alternative: all-mpnet-base-v2 (768 dims, slower, best quality)
        """
        self.model_name = model_name
        self._model: SentenceTransformer | None = None
        self.dimensions = 384 if "MiniLM" in model_name else 768

    @property
    def model(self) -> SentenceTransformer:
        """
        Lazy load the model.

        Returns:
            Loaded sentence-transformers model
        """
        if self._model is None:
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Input text

        Returns:
            Embedding vector as list of floats
        """
        if not text or not text.strip():
            # Return zero vector for empty text
            return [0.0] * self.dimensions

        # Truncate very long texts (model limit is usually 512 tokens)
        max_chars = 10000
        if len(text) > max_chars:
            text = text[:max_chars]

        # Generate embedding
        embedding = self.model.encode(text, convert_to_numpy=True)

        # Normalize (for cosine similarity)
        embedding = embedding / np.linalg.norm(embedding)

        return embedding.tolist()

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts (batched for efficiency).

        Args:
            texts: List of input texts

        Returns:
            List of embedding vectors
        """
        if not texts:
            return []

        # Preprocess texts
        processed_texts = []
        for text in texts:
            if not text or not text.strip():
                processed_texts.append("")
            else:
                # Truncate long texts
                max_chars = 10000
                processed_texts.append(text[:max_chars] if len(text) > max_chars else text)

        # Generate embeddings in batch (much faster)
        embeddings = self.model.encode(
            processed_texts,
            convert_to_numpy=True,
            show_progress_bar=len(processed_texts) > 10,
        )

        # Normalize
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        embeddings = embeddings / norms

        return embeddings.tolist()

    def compute_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Compute cosine similarity between two embeddings.

        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector

        Returns:
            Similarity score (0-1)
        """
        vec1 = np.array(embedding1)
        vec2 = np.array(embedding2)

        # Cosine similarity (vectors should already be normalized)
        similarity = np.dot(vec1, vec2)

        return float(similarity)

    def find_most_similar(
        self, query_embedding: List[float], embeddings: List[List[float]], top_k: int = 10
    ) -> List[tuple[int, float]]:
        """
        Find most similar embeddings to query.

        Args:
            query_embedding: Query vector
            embeddings: List of candidate vectors
            top_k: Number of results to return

        Returns:
            List of (index, similarity_score) tuples, sorted by similarity
        """
        if not embeddings:
            return []

        query = np.array(query_embedding)
        candidates = np.array(embeddings)

        # Compute similarities
        similarities = np.dot(candidates, query)

        # Get top k indices
        top_indices = np.argsort(similarities)[::-1][:top_k]

        return [(int(idx), float(similarities[idx])) for idx in top_indices]


# Global instance
_embedding_service: EmbeddingService | None = None


def get_embedding_service(model_name: str = "all-MiniLM-L6-v2") -> EmbeddingService:
    """
    Get global embedding service instance (singleton).

    Args:
        model_name: Model to use

    Returns:
        EmbeddingService instance
    """
    global _embedding_service

    if _embedding_service is None:
        _embedding_service = EmbeddingService(model_name)

    return _embedding_service
