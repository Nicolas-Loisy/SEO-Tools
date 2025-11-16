"""Keyword extraction service for internal linking recommendations."""

from typing import List, Tuple, Optional
from collections import Counter
import re


# English stopwords (most common)
STOPWORDS = {
    'a', 'about', 'above', 'after', 'again', 'against', 'all', 'am', 'an', 'and', 'any',
    'are', 'as', 'at', 'be', 'because', 'been', 'before', 'being', 'below', 'between',
    'both', 'but', 'by', 'can', 'cannot', 'could', 'did', 'do', 'does', 'doing', 'down',
    'during', 'each', 'few', 'for', 'from', 'further', 'had', 'has', 'have', 'having',
    'he', 'her', 'here', 'hers', 'herself', 'him', 'himself', 'his', 'how', 'i', 'if',
    'in', 'into', 'is', 'it', 'its', 'itself', 'just', 'me', 'might', 'more', 'most',
    'must', 'my', 'myself', 'no', 'nor', 'not', 'now', 'of', 'off', 'on', 'once', 'only',
    'or', 'other', 'our', 'ours', 'ourselves', 'out', 'over', 'own', 's', 'same', 'she',
    'should', 'so', 'some', 'such', 't', 'than', 'that', 'the', 'their', 'theirs', 'them',
    'themselves', 'then', 'there', 'these', 'they', 'this', 'those', 'through', 'to',
    'too', 'under', 'until', 'up', 'very', 'was', 'we', 'were', 'what', 'when', 'where',
    'which', 'while', 'who', 'whom', 'why', 'will', 'with', 'would', 'you', 'your',
    'yours', 'yourself', 'yourselves'
}


class KeywordExtractor:
    """Service for extracting keywords from page content."""

    def __init__(self):
        """Initialize keyword extractor (no ML model needed)."""
        print("[KeywordExtractor] Using FAST frequency-based extraction (KeyBERT disabled)")

    def extract_keywords(
        self,
        text: str,
        top_n: int = 20,
        min_ngram: int = 1,
        max_ngram: int = 3,
    ) -> List[Tuple[str, float]]:
        """
        Extract keywords from text using FAST frequency-based method.

        CRITICAL: KeyBERT was causing 30+ second timeouts. This simple method
        is 100x faster and still produces good results for internal linking.

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

        # Extract n-grams and count frequency
        keywords = self._extract_ngrams_fast(text, min_ngram, max_ngram, top_n)

        return keywords

    def _extract_ngrams_fast(
        self,
        text: str,
        min_ngram: int,
        max_ngram: int,
        top_n: int
    ) -> List[Tuple[str, float]]:
        """
        Fast n-gram extraction using frequency counting.

        Much faster than KeyBERT (milliseconds vs 30+ seconds).
        """
        # Tokenize and clean
        words = text.lower().split()
        words = [w.strip('.,!?;:()[]{}') for w in words]
        words = [w for w in words if len(w) > 2 and w not in STOPWORDS]

        ngrams = []

        # Extract unigrams (single words)
        if min_ngram <= 1 <= max_ngram:
            ngrams.extend(words)

        # Extract bigrams (2-word phrases)
        if min_ngram <= 2 <= max_ngram and len(words) > 1:
            for i in range(len(words) - 1):
                bigram = f"{words[i]} {words[i+1]}"
                ngrams.append(bigram)

        # Extract trigrams (3-word phrases)
        if min_ngram <= 3 <= max_ngram and len(words) > 2:
            for i in range(len(words) - 2):
                trigram = f"{words[i]} {words[i+1]} {words[i+2]}"
                ngrams.append(trigram)

        # Count frequencies
        counter = Counter(ngrams)

        # Get top N with normalized scores
        most_common = counter.most_common(top_n)

        if not most_common:
            return []

        # Normalize scores to 0-1 range
        max_count = most_common[0][1]
        keywords = [(phrase, count / max_count) for phrase, count in most_common]

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
