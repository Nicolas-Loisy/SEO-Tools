"""Language detection and multilingual text utilities."""

from typing import Optional
from langdetect import detect, LangDetectException


def detect_language(text: str) -> Optional[str]:
    """
    Detect the language of a text.

    Args:
        text: Input text

    Returns:
        ISO 639-1 language code (e.g., "en", "fr") or None if detection fails
    """
    if not text or len(text.strip()) < 20:
        return None

    try:
        # langdetect returns ISO 639-1 codes
        return detect(text)
    except LangDetectException:
        return None


def get_language_name(code: str) -> str:
    """
    Get full language name from ISO code.

    Args:
        code: ISO 639-1 language code

    Returns:
        Language name in English
    """
    languages = {
        "en": "English",
        "fr": "French",
        "es": "Spanish",
        "de": "German",
        "it": "Italian",
        "pt": "Portuguese",
        "nl": "Dutch",
        "pl": "Polish",
        "ru": "Russian",
        "zh": "Chinese",
        "ja": "Japanese",
        "ko": "Korean",
        "ar": "Arabic",
    }

    return languages.get(code, code.upper())


def is_language_supported(language_code: str, model_languages: list[str]) -> bool:
    """
    Check if a language is supported by a model.

    Args:
        language_code: ISO 639-1 language code
        model_languages: List of supported language codes

    Returns:
        True if language is supported
    """
    return language_code in model_languages


# Common stop words for French and English
STOP_WORDS = {
    "en": {
        "the", "is", "at", "which", "on", "a", "an", "and", "or", "but",
        "in", "with", "to", "for", "of", "as", "by", "that", "this", "it",
        "from", "be", "are", "was", "were", "been", "being", "have", "has",
        "had", "do", "does", "did", "will", "would", "could", "should",
    },
    "fr": {
        "le", "la", "les", "un", "une", "des", "de", "du", "et", "ou",
        "mais", "dans", "avec", "pour", "par", "sur", "à", "en", "ce",
        "qui", "que", "dont", "où", "se", "il", "elle", "on", "nous",
        "vous", "ils", "elles", "être", "avoir", "faire", "dire", "aller",
        "voir", "savoir", "pouvoir", "falloir", "vouloir", "venir", "devoir",
    },
}


def get_stop_words(language: str) -> set[str]:
    """
    Get stop words for a language.

    Args:
        language: ISO 639-1 language code

    Returns:
        Set of stop words
    """
    return STOP_WORDS.get(language, STOP_WORDS["en"])
