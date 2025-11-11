"""Semantic embeddings service with multilingual support."""

from typing import List
import numpy as np
from sentence_transformers import SentenceTransformer


class EmbeddingService:
    """
    Service for generating semantic embeddings from text.

    Uses sentence-transformers to create vector representations for
    semantic similarity search. Supports multiple languages.
    """

    # Available models with their configurations
    MODELS = {
        "multilingual": {
            "name": "paraphrase-multilingual-MiniLM-L12-v2",
            "dimensions": 384,
            "languages": ["en", "fr", "de", "es", "it", "pt", "nl", "pl", "ru", "zh", "ja"],
            "description": "Fast multilingual model supporting 50+ languages",
        },
        "english": {
            "name": "all-MiniLM-L6-v2",
            "dimensions": 384,
            "languages": ["en"],
            "description": "Fast English-only model",
        },
        "multilingual-large": {
            "name": "paraphrase-multilingual-mpnet-base-v2",
            "dimensions": 768,
            "languages": ["en", "fr", "de", "es", "it", "pt", "nl", "pl", "ru", "zh", "ja"],
            "description": "Best quality multilingual model (slower)",
        },
    }

    def __init__(self, model_key: str = "multilingual"):
        """
        Initialize embedding service.

        Args:
            model_key: Model key from MODELS dict
                      Default: "multilingual" (French + English + 50+ languages)
        """
        if model_key not in self.MODELS:
            raise ValueError(f"Unknown model: {model_key}. Available: {list(self.MODELS.keys())}")

        self.model_config = self.MODELS[model_key]
        self.model_name = self.model_config["name"]
        self.dimensions = self.model_config["dimensions"]
        self.supported_languages = self.model_config["languages"]
        self._model: SentenceTransformer | None = None

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

    def generate_embedding(self, text: str, language: str = None) -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Input text
            language: Optional language hint (e.g., "en", "fr")

        Returns:
            Embedding vector as list of floats
        """
        if not text or not text.strip():
            # Return zero vector for empty text
            return [0.0] * self.dimensions

        # Warn if language not supported (but still process)
        if language and language not in self.supported_languages and "multilingual" not in self.model_name:
            print(f"Warning: Language '{language}' may not be well supported by {self.model_name}")

        # Truncate very long texts (model limit is usually 512 tokens)
        max_chars = 10000
        if len(text) > max_chars:
            text = text[:max_chars]

        # Generate embedding
        embedding = self.model.encode(text, convert_to_numpy=True)

        # Normalize (for cosine similarity)
        embedding = embedding / np.linalg.norm(embedding)

        return embedding.tolist()

    def generate_embeddings(
        self, texts: List[str], languages: List[str] = None
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts (batched for efficiency).

        Args:
            texts: List of input texts
            languages: Optional list of language hints (same length as texts)

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


# Global instances for different configurations
_embedding_services = {}


def get_embedding_service(model_key: str = "multilingual") -> EmbeddingService:
    """
    Get embedding service instance (singleton per model).

    Args:
        model_key: Model configuration key
                  "multilingual" - French + English + 50+ languages (default)
                  "english" - English only (slightly faster)
                  "multilingual-large" - Best quality (slower)

    Returns:
        EmbeddingService instance
    """
    global _embedding_services

    if model_key not in _embedding_services:
        _embedding_services[model_key] = EmbeddingService(model_key)

    return _embedding_services[model_key]
