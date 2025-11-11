"""NLP and semantic analysis services with multilingual support."""

from app.services.nlp.embeddings import EmbeddingService, get_embedding_service
from app.services.nlp.text_processing import (
    clean_text,
    extract_keywords,
    calculate_readability_score,
    analyze_content_structure,
    detect_content_language,
)
from app.services.nlp.language import (
    detect_language,
    get_language_name,
    is_language_supported,
    get_stop_words,
)

__all__ = [
    "EmbeddingService",
    "get_embedding_service",
    "clean_text",
    "extract_keywords",
    "calculate_readability_score",
    "analyze_content_structure",
    "detect_content_language",
    "detect_language",
    "get_language_name",
    "is_language_supported",
    "get_stop_words",
]
