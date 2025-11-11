"""Keyword extraction service for internal linking recommendations."""

from typing import List, Tuple, Optional
from keybert import KeyBERT
import re


class KeywordExtractor:
    """Service for extracting keywords from page content."""

    def __init__(self):
        """Initialize KeyBERT model."""
        # Use lightweight model for keyword extraction
        self.kw_model = KeyBERT(model='all-MiniLM-L6-v2')

    def extract_keywords(
        self,
        text: str,
        top_n: int = 20,
        min_ngram: int = 1,
        max_ngram: int = 3,
    ) -> List[Tuple[str, float]]:
        """
        Extract keywords from text using KeyBERT.

        Args:
            text: Text content to extract keywords from
            top_n: Number of top keywords to return
            min_ngram: Minimum n-gram size
            max_ngram: Maximum n-gram size

        Returns:
            List of (keyword, score) tuples
        """
        if not text or len(text.strip()) < 50:
            return []

        # Clean text
        text = self._clean_text(text)

        # Extract keywords with KeyBERT
        keywords = self.kw_model.extract_keywords(
            text,
            keyphrase_ngram_range=(min_ngram, max_ngram),
            stop_words='english',
            top_n=top_n,
            use_maxsum=True,
            nr_candidates=top_n * 3,
            diversity=0.7
        )

        return keywords

    def extract_entities(self, text: str) -> List[str]:
        """
        Extract named entities from text (simpler fallback without spaCy).

        Args:
            text: Text content

        Returns:
            List of entity strings
        """
        # For now, just extract capitalized phrases (proper nouns)
        # This is a lightweight alternative to full NER
        words = text.split()
        entities = []

        current_entity = []
        for word in words:
            # Check if word starts with capital letter (potential entity)
            if word and word[0].isupper() and len(word) > 2:
                current_entity.append(word)
            else:
                if current_entity and len(current_entity) >= 1:
                    entity = ' '.join(current_entity)
                    if len(entity) > 3:  # Filter out very short entities
                        entities.append(entity)
                current_entity = []

        # Add last entity if exists
        if current_entity:
            entity = ' '.join(current_entity)
            if len(entity) > 3:
                entities.append(entity)

        # Remove duplicates and return
        return list(set(entities))[:20]

    def _clean_text(self, text: str) -> str:
        """Clean text for keyword extraction."""
        # Remove URLs
        text = re.sub(r'http[s]?://\S+', '', text)

        # Remove email addresses
        text = re.sub(r'\S+@\S+', '', text)

        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)

        return text.strip()


# Singleton instance
keyword_extractor = KeywordExtractor()
