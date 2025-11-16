"""Google Autocomplete scraper for keyword suggestions."""

import httpx
import urllib.parse
from typing import List, Optional, Set
import asyncio


class GoogleAutocompleteScraper:
    """
    Scrapes Google Autocomplete suggestions for keyword research.

    Uses the public Google Suggest API (completely free).
    No API key required.
    """

    BASE_URL = "http://suggestqueries.google.com/complete/search"

    def __init__(self, language: str = "en", country: str = "us"):
        """
        Initialize scraper.

        Args:
            language: Language code (en, fr, es, etc.)
            country: Country code (us, fr, uk, etc.)
        """
        self.language = language
        self.country = country
        self.client = httpx.AsyncClient(timeout=10.0)

    async def get_suggestions(
        self,
        keyword: str,
        max_suggestions: int = 10
    ) -> List[str]:
        """
        Get autocomplete suggestions for a keyword.

        Args:
            keyword: Base keyword to get suggestions for
            max_suggestions: Maximum number of suggestions to return

        Returns:
            List of keyword suggestions
        """
        params = {
            "client": "firefox",
            "q": keyword,
            "hl": self.language,
            "gl": self.country,
        }

        try:
            response = await self.client.get(self.BASE_URL, params=params)
            response.raise_for_status()

            # Response is JSON array: [query, [suggestions]]
            data = response.json()

            if len(data) >= 2 and isinstance(data[1], list):
                suggestions = data[1][:max_suggestions]
                return suggestions

            return []

        except Exception as e:
            print(f"Error fetching suggestions for '{keyword}': {e}")
            return []

    async def get_suggestions_with_prefixes(
        self,
        keyword: str,
        prefixes: Optional[List[str]] = None,
        max_per_prefix: int = 10,
    ) -> List[str]:
        """
        Get suggestions using multiple prefixes (a-z, how, what, etc.).

        Args:
            keyword: Base keyword
            prefixes: List of prefixes to try (default: a-z)
            max_per_prefix: Max suggestions per prefix

        Returns:
            Unique list of all suggestions
        """
        if prefixes is None:
            # Default: alphabet
            prefixes = list("abcdefghijklmnopqrstuvwxyz")

        all_suggestions: Set[str] = set()

        # Fetch suggestions for each prefix
        tasks = []
        for prefix in prefixes:
            query = f"{keyword} {prefix}"
            tasks.append(self.get_suggestions(query, max_per_prefix))

        # Also get base keyword suggestions
        tasks.append(self.get_suggestions(keyword, max_per_prefix))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, list):
                all_suggestions.update(result)

        # Filter out the base keyword itself
        all_suggestions.discard(keyword)

        return sorted(list(all_suggestions))

    async def get_suggestions_with_question_words(
        self,
        keyword: str,
        question_words: Optional[List[str]] = None,
        max_per_question: int = 10,
    ) -> List[str]:
        """
        Get suggestions using question words (how, what, why, etc.).

        Args:
            keyword: Base keyword
            question_words: List of question words (default: common questions)
            max_per_question: Max suggestions per question word

        Returns:
            Unique list of question-based suggestions
        """
        if question_words is None:
            if self.language == "fr":
                question_words = [
                    "comment", "pourquoi", "quoi", "quel", "quelle",
                    "où", "quand", "combien", "est-ce que"
                ]
            else:
                question_words = [
                    "how", "what", "why", "when", "where",
                    "who", "which", "can", "does", "is"
                ]

        all_suggestions: Set[str] = set()

        tasks = []
        for qword in question_words:
            query = f"{qword} {keyword}"
            tasks.append(self.get_suggestions(query, max_per_question))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, list):
                all_suggestions.update(result)

        return sorted(list(all_suggestions))

    async def get_comprehensive_suggestions(
        self,
        keyword: str,
        use_alphabet: bool = True,
        use_questions: bool = True,
        max_suggestions: int = 200,
    ) -> List[str]:
        """
        Get comprehensive keyword suggestions using multiple strategies.

        Args:
            keyword: Base keyword
            use_alphabet: Use alphabet prefixes
            use_questions: Use question words
            max_suggestions: Maximum total suggestions to return

        Returns:
            Comprehensive list of unique suggestions
        """
        all_suggestions: Set[str] = set()

        # Base suggestions
        base = await self.get_suggestions(keyword, 10)
        all_suggestions.update(base)

        # Alphabet-based suggestions
        if use_alphabet:
            alphabet_suggestions = await self.get_suggestions_with_prefixes(
                keyword, max_per_prefix=5
            )
            all_suggestions.update(alphabet_suggestions)

        # Question-based suggestions
        if use_questions:
            question_suggestions = await self.get_suggestions_with_question_words(
                keyword, max_per_question=5
            )
            all_suggestions.update(question_suggestions)

        # Limit total
        suggestions_list = sorted(list(all_suggestions))[:max_suggestions]

        return suggestions_list

    async def close(self):
        """Close HTTP client."""
        await self.client.aclose()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


# Singleton instance
google_autocomplete = GoogleAutocompleteScraper()
