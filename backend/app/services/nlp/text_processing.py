"""Text processing utilities for SEO content with multilingual support."""

import re
from typing import List, Dict, Any
from collections import Counter
from app.services.nlp.language import detect_language, get_stop_words


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

    # Remove special characters (keep alphanumeric, accents, and basic punctuation)
    # Keep French accents: é, è, ê, à, ù, etc.
    text = re.sub(r"[^\w\s.,!?;:\-\'\"()àâäéèêëïîôùûüÿçÀÂÄÉÈÊËÏÎÔÙÛÜŸÇ]", "", text)

    return text.strip()


def extract_keywords(
    text: str, top_n: int = 10, min_length: int = 3, language: str = None
) -> List[str]:
    """
    Extract top keywords from text using frequency analysis (multilingual).

    Args:
        text: Input text
        top_n: Number of keywords to return
        min_length: Minimum word length
        language: Language code (auto-detected if None)

    Returns:
        List of top keywords
    """
    if not text:
        return []

    # Detect language if not provided
    if not language:
        language = detect_language(text) or "en"

    # Clean and lowercase
    text = clean_text(text.lower())

    # Get stop words for the language
    stop_words = get_stop_words(language)

    # Tokenize (support accented characters)
    if language == "fr":
        # French: keep accented characters
        words = re.findall(r"\b[a-zàâäéèêëïîôùûüÿç]+\b", text)
    else:
        # English and others
        words = re.findall(r"\b[a-z]+\b", text)

    # Filter
    words = [w for w in words if len(w) >= min_length and w not in stop_words]

    # Count frequencies
    counter = Counter(words)

    return [word for word, _ in counter.most_common(top_n)]


def calculate_readability_score(text: str, language: str = None) -> float:
    """
    Calculate readability score (multilingual support).

    For English: Flesch Reading Ease
    For French: Flesch-Vacca (adapted formula)

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
        language: Language code (auto-detected if None)

    Returns:
        Readability score (0-100)
    """
    if not text or len(text.strip()) < 10:
        return 0.0

    # Detect language if not provided
    if not language:
        language = detect_language(text) or "en"

    # Count sentences (approximation)
    sentences = len(re.findall(r"[.!?]+", text))
    if sentences == 0:
        sentences = 1

    # Count words (support accented characters)
    if language == "fr":
        words = re.findall(r"\b[a-zàâäéèêëïîôùûüÿç]+\b", text.lower())
    else:
        words = re.findall(r"\b\w+\b", text)

    word_count = len(words)

    if word_count == 0:
        return 0.0

    # Count syllables (rough approximation)
    def count_syllables(word: str) -> int:
        word = word.lower()
        if language == "fr":
            # French: count vowel groups (including accented vowels)
            syllables = len(re.findall(r"[aeiouyàâäéèêëïîôùûüÿ]+", word))
        else:
            # English
            syllables = len(re.findall(r"[aeiouy]+", word))
        return max(1, syllables)

    total_syllables = sum(count_syllables(w) for w in words)

    # Calculate metrics
    avg_sentence_length = word_count / sentences
    avg_syllables_per_word = total_syllables / word_count

    # Readability formula
    if language == "fr":
        # Flesch-Vacca for French (adapted formula)
        score = 207 - 1.015 * avg_sentence_length - 73.6 * avg_syllables_per_word
    else:
        # Flesch Reading Ease for English
        score = 206.835 - 1.015 * avg_sentence_length - 84.6 * avg_syllables_per_word

    # Clamp to 0-100
    return max(0.0, min(100.0, score))


def analyze_content_structure(html_text: str) -> Dict[str, Any]:
    """
    Analyze content structure for SEO (language-agnostic).

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


def detect_content_language(text: str) -> str:
    """
    Detect the language of content.

    Args:
        text: Content text

    Returns:
        ISO 639-1 language code (e.g., "en", "fr")
    """
    return detect_language(text) or "en"
