"""Text processing utilities for SEO content."""

import re
from typing import List, Dict, Any
from collections import Counter


def clean_text(text: str) -> str:
    """
    Clean text for processing.

    Args:
        text: Raw text

    Returns:
        Cleaned text
    """
    if not text:
        return ""

    # Remove extra whitespace
    text = re.sub(r"\s+", " ", text)

    # Remove special characters (keep alphanumeric and basic punctuation)
    text = re.sub(r"[^\w\s.,!?;:\-\'\"()]", "", text)

    return text.strip()


def extract_keywords(text: str, top_n: int = 10, min_length: int = 3) -> List[str]:
    """
    Extract top keywords from text using simple frequency analysis.

    Args:
        text: Input text
        top_n: Number of keywords to return
        min_length: Minimum word length

    Returns:
        List of top keywords
    """
    if not text:
        return []

    # Clean and lowercase
    text = clean_text(text.lower())

    # Common stop words
    stop_words = {
        "the",
        "is",
        "at",
        "which",
        "on",
        "a",
        "an",
        "and",
        "or",
        "but",
        "in",
        "with",
        "to",
        "for",
        "of",
        "as",
        "by",
        "that",
        "this",
        "it",
        "from",
        "be",
        "are",
        "was",
        "were",
        "been",
        "being",
        "have",
        "has",
        "had",
        "do",
        "does",
        "did",
        "will",
        "would",
        "could",
        "should",
    }

    # Tokenize
    words = re.findall(r"\b[a-z]+\b", text)

    # Filter
    words = [w for w in words if len(w) >= min_length and w not in stop_words]

    # Count frequencies
    counter = Counter(words)

    return [word for word, _ in counter.most_common(top_n)]


def calculate_readability_score(text: str) -> float:
    """
    Calculate Flesch Reading Ease score (simplified).

    Score interpretation:
    90-100: Very easy to read
    80-89: Easy to read
    70-79: Fairly easy to read
    60-69: Standard
    50-59: Fairly difficult to read
    30-49: Difficult to read
    0-29: Very difficult to read

    Args:
        text: Input text

    Returns:
        Readability score (0-100)
    """
    if not text or len(text.strip()) < 10:
        return 0.0

    # Count sentences (approximation)
    sentences = len(re.findall(r"[.!?]+", text))
    if sentences == 0:
        sentences = 1

    # Count words
    words = re.findall(r"\b\w+\b", text)
    word_count = len(words)

    if word_count == 0:
        return 0.0

    # Count syllables (rough approximation)
    def count_syllables(word: str) -> int:
        word = word.lower()
        syllables = len(re.findall(r"[aeiouy]+", word))
        return max(1, syllables)

    total_syllables = sum(count_syllables(w) for w in words)

    # Flesch Reading Ease formula
    avg_sentence_length = word_count / sentences
    avg_syllables_per_word = total_syllables / word_count

    score = 206.835 - 1.015 * avg_sentence_length - 84.6 * avg_syllables_per_word

    # Clamp to 0-100
    return max(0.0, min(100.0, score))


def analyze_content_structure(html_text: str) -> Dict[str, Any]:
    """
    Analyze content structure for SEO.

    Args:
        html_text: HTML or text content

    Returns:
        Structure analysis dict
    """
    # Extract headings
    h2_count = len(re.findall(r"<h2[^>]*>", html_text, re.IGNORECASE))
    h3_count = len(re.findall(r"<h3[^>]*>", html_text, re.IGNORECASE))

    # Extract paragraphs
    p_count = len(re.findall(r"<p[^>]*>", html_text, re.IGNORECASE))

    # Extract lists
    ul_count = len(re.findall(r"<ul[^>]*>", html_text, re.IGNORECASE))
    ol_count = len(re.findall(r"<ol[^>]*>", html_text, re.IGNORECASE))

    # Extract images
    img_count = len(re.findall(r"<img[^>]*>", html_text, re.IGNORECASE))

    # Count internal/external links
    links = re.findall(r'<a[^>]*href=["\']([^"\']+)["\']', html_text, re.IGNORECASE)

    return {
        "h2_count": h2_count,
        "h3_count": h3_count,
        "paragraph_count": p_count,
        "list_count": ul_count + ol_count,
        "image_count": img_count,
        "link_count": len(links),
        "has_structure": h2_count > 0 or p_count > 2,
    }
