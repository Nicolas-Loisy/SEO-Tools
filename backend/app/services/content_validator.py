"""SEO content validation service."""

import re
from typing import Dict, Any, List
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """Content validation result."""
    score: int  # 0-100
    issues: List[Dict[str, Any]]
    suggestions: List[str]
    metrics: Dict[str, Any]


class ContentValidator:
    """
    Validates content for SEO best practices.

    Checks keyword usage, readability, structure, and more.
    """

    def validate_content(
        self,
        content: str,
        keyword: str,
        meta_title: str = None,
        meta_description: str = None,
        min_words: int = 300,
        max_words: int = 2500
    ) -> ValidationResult:
        """
        Validate content for SEO.

        Args:
            content: Content text
            keyword: Target keyword
            meta_title: Meta title
            meta_description: Meta description
            min_words: Minimum word count
            max_words: Maximum word count

        Returns:
            Validation result with score and suggestions
        """
        issues = []
        suggestions = []
        metrics = {}

        # 1. Word count
        word_count = len(content.split())
        metrics["word_count"] = word_count

        if word_count < min_words:
            issues.append({
                "type": "word_count",
                "severity": "high",
                "message": f"Content too short ({word_count} words). Minimum: {min_words} words"
            })
            suggestions.append(f"Add more content to reach at least {min_words} words")
        elif word_count > max_words:
            issues.append({
                "type": "word_count",
                "severity": "medium",
                "message": f"Content too long ({word_count} words). Maximum recommended: {max_words} words"
            })
            suggestions.append(f"Consider splitting into multiple pages or reducing to {max_words} words")

        # 2. Keyword analysis
        keyword_lower = keyword.lower()
        content_lower = content.lower()

        keyword_count = content_lower.count(keyword_lower)
        keyword_density = (keyword_count / word_count * 100) if word_count > 0 else 0

        metrics["keyword_count"] = keyword_count
        metrics["keyword_density"] = round(keyword_density, 2)

        if keyword_count == 0:
            issues.append({
                "type": "keyword",
                "severity": "critical",
                "message": f"Target keyword '{keyword}' not found in content"
            })
            suggestions.append(f"Include the keyword '{keyword}' naturally 3-5 times")
        elif keyword_count < 2:
            issues.append({
                "type": "keyword",
                "severity": "medium",
                "message": f"Keyword appears only {keyword_count} time(s). Recommended: 3-5 times"
            })
            suggestions.append(f"Use the keyword '{keyword}' 2-4 more times naturally")
        elif keyword_density > 3.0:
            issues.append({
                "type": "keyword",
                "severity": "high",
                "message": f"Keyword density too high ({keyword_density}%). Risk of keyword stuffing"
            })
            suggestions.append("Reduce keyword usage and use semantic variations")

        # 3. Heading structure
        h1_count = len(re.findall(r'<h1[^>]*>.*?</h1>', content, re.IGNORECASE))
        h2_count = len(re.findall(r'<h2[^>]*>.*?</h2>', content, re.IGNORECASE))
        h3_count = len(re.findall(r'<h3[^>]*>.*?</h3>', content, re.IGNORECASE))

        metrics["h1_count"] = h1_count
        metrics["h2_count"] = h2_count
        metrics["h3_count"] = h3_count

        if h1_count == 0:
            issues.append({
                "type": "structure",
                "severity": "critical",
                "message": "No H1 heading found"
            })
            suggestions.append("Add an H1 heading with the target keyword")
        elif h1_count > 1:
            issues.append({
                "type": "structure",
                "severity": "medium",
                "message": f"Multiple H1 headings ({h1_count}). Use only one H1 per page"
            })
            suggestions.append("Keep only one H1 heading per page")

        if h2_count == 0:
            issues.append({
                "type": "structure",
                "severity": "high",
                "message": "No H2 headings found"
            })
            suggestions.append("Add H2 headings to structure your content")
        elif h2_count < 2:
            suggestions.append("Add more H2 headings to improve structure")

        # 4. Meta title validation
        if meta_title:
            title_length = len(meta_title)
            metrics["meta_title_length"] = title_length

            if title_length < 30:
                issues.append({
                    "type": "meta_title",
                    "severity": "medium",
                    "message": f"Meta title too short ({title_length} chars). Recommended: 50-60 chars"
                })
                suggestions.append("Expand meta title to 50-60 characters")
            elif title_length > 60:
                issues.append({
                    "type": "meta_title",
                    "severity": "medium",
                    "message": f"Meta title too long ({title_length} chars). May be truncated in search results"
                })
                suggestions.append("Shorten meta title to 50-60 characters")

            if keyword_lower not in meta_title.lower():
                issues.append({
                    "type": "meta_title",
                    "severity": "high",
                    "message": "Target keyword not in meta title"
                })
                suggestions.append(f"Include '{keyword}' in the meta title")

        # 5. Meta description validation
        if meta_description:
            desc_length = len(meta_description)
            metrics["meta_description_length"] = desc_length

            if desc_length < 120:
                issues.append({
                    "type": "meta_description",
                    "severity": "medium",
                    "message": f"Meta description too short ({desc_length} chars). Recommended: 150-160 chars"
                })
                suggestions.append("Expand meta description to 150-160 characters")
            elif desc_length > 160:
                issues.append({
                    "type": "meta_description",
                    "severity": "medium",
                    "message": f"Meta description too long ({desc_length} chars). May be truncated"
                })
                suggestions.append("Shorten meta description to 150-160 characters")

            if keyword_lower not in meta_description.lower():
                suggestions.append(f"Consider including '{keyword}' in the meta description")

        # 6. Readability checks
        sentences = re.split(r'[.!?]+', content)
        avg_words_per_sentence = word_count / len(sentences) if len(sentences) > 0 else 0
        metrics["avg_words_per_sentence"] = round(avg_words_per_sentence, 1)

        if avg_words_per_sentence > 25:
            issues.append({
                "type": "readability",
                "severity": "medium",
                "message": f"Average sentence length is high ({avg_words_per_sentence:.1f} words). Recommended: <20 words"
            })
            suggestions.append("Break long sentences into shorter ones for better readability")

        # 7. Paragraph length
        paragraphs = content.split('\n\n')
        long_paragraphs = sum(1 for p in paragraphs if len(p.split()) > 150)

        if long_paragraphs > 0:
            issues.append({
                "type": "readability",
                "severity": "low",
                "message": f"{long_paragraphs} paragraph(s) are very long (>150 words)"
            })
            suggestions.append("Break long paragraphs into smaller chunks")

        # Calculate overall score
        score = self._calculate_score(issues, metrics, min_words, max_words)

        return ValidationResult(
            score=score,
            issues=issues,
            suggestions=suggestions,
            metrics=metrics
        )

    def _calculate_score(
        self,
        issues: List[Dict[str, Any]],
        metrics: Dict[str, Any],
        min_words: int,
        max_words: int
    ) -> int:
        """Calculate SEO score (0-100)."""
        score = 100

        # Deduct points based on issues
        for issue in issues:
            severity = issue.get("severity", "low")
            if severity == "critical":
                score -= 20
            elif severity == "high":
                score -= 10
            elif severity == "medium":
                score -= 5
            else:  # low
                score -= 2

        # Bonus for good metrics
        word_count = metrics.get("word_count", 0)
        if min_words <= word_count <= max_words:
            score += 5

        keyword_density = metrics.get("keyword_density", 0)
        if 1.0 <= keyword_density <= 2.5:
            score += 5

        h2_count = metrics.get("h2_count", 0)
        if h2_count >= 3:
            score += 5

        # Ensure score is within bounds
        return max(0, min(100, score))


# Singleton instance
content_validator = ContentValidator()
