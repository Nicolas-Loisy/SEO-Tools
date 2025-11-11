"""Schema type detection service for structured data generation."""

from typing import Optional, Dict, Any, List
from enum import Enum
import re
from urllib.parse import urlparse


class SchemaType(str, Enum):
    """Supported Schema.org types."""
    ARTICLE = "Article"
    BLOG_POSTING = "BlogPosting"
    NEWS_ARTICLE = "NewsArticle"
    PRODUCT = "Product"
    ORGANIZATION = "Organization"
    LOCAL_BUSINESS = "LocalBusiness"
    PERSON = "Person"
    FAQ_PAGE = "FAQPage"
    HOW_TO = "HowTo"
    BREADCRUMB_LIST = "BreadcrumbList"
    WEB_PAGE = "WebPage"
    WEBSITE = "WebSite"


class SchemaDetector:
    """Service for detecting appropriate schema types based on page content."""

    def __init__(self):
        """Initialize detector with keyword patterns."""
        self.article_keywords = [
            'article', 'blog', 'post', 'news', 'story', 'editorial',
            'opinion', 'guide', 'tutorial', 'how-to'
        ]

        self.product_keywords = [
            'product', 'item', 'buy', 'purchase', 'price', 'cart',
            'shop', 'store', 'sale', 'sku'
        ]

        self.faq_keywords = [
            'faq', 'frequently asked', 'questions', 'q&a', 'qa'
        ]

        self.howto_keywords = [
            'how to', 'tutorial', 'guide', 'step by step', 'instructions',
            'steps to', 'learn how'
        ]

        self.local_business_keywords = [
            'contact', 'location', 'address', 'phone', 'hours',
            'open', 'closed', 'directions', 'map'
        ]

    def detect_schema_type(
        self,
        url: str,
        title: str,
        content: str,
        meta_description: Optional[str] = None,
        h1: Optional[str] = None,
    ) -> List[SchemaType]:
        """
        Detect appropriate schema types for a page.

        Args:
            url: Page URL
            title: Page title
            content: Page text content
            meta_description: Meta description
            h1: H1 heading

        Returns:
            List of recommended schema types (ordered by relevance)
        """
        scores = {}

        # Combine all text for analysis
        all_text = ' '.join([
            url.lower(),
            title.lower() if title else '',
            h1.lower() if h1 else '',
            meta_description.lower() if meta_description else '',
            content.lower()[:1000]  # First 1000 chars for performance
        ])

        # Check for Article/Blog indicators
        article_score = self._calculate_keyword_score(all_text, self.article_keywords)
        if article_score > 0:
            # Distinguish between Article types
            if 'blog' in all_text or '/blog/' in url.lower():
                scores[SchemaType.BLOG_POSTING] = article_score * 1.2
            elif 'news' in all_text or '/news/' in url.lower():
                scores[SchemaType.NEWS_ARTICLE] = article_score * 1.2
            else:
                scores[SchemaType.ARTICLE] = article_score

        # Check for Product indicators
        product_score = self._calculate_keyword_score(all_text, self.product_keywords)
        if product_score > 0:
            scores[SchemaType.PRODUCT] = product_score

        # Check for FAQ indicators
        faq_score = self._calculate_keyword_score(all_text, self.faq_keywords)
        if faq_score > 0 or self._has_faq_structure(content):
            scores[SchemaType.FAQ_PAGE] = faq_score + (2 if self._has_faq_structure(content) else 0)

        # Check for HowTo indicators
        howto_score = self._calculate_keyword_score(all_text, self.howto_keywords)
        if howto_score > 0 or self._has_steps_structure(content):
            scores[SchemaType.HOW_TO] = howto_score + (2 if self._has_steps_structure(content) else 0)

        # Check for LocalBusiness indicators
        business_score = self._calculate_keyword_score(all_text, self.local_business_keywords)
        if business_score > 0 and self._has_contact_info(content):
            scores[SchemaType.LOCAL_BUSINESS] = business_score * 1.5

        # Check if it's the homepage
        parsed_url = urlparse(url)
        if parsed_url.path in ['', '/'] or parsed_url.path.strip('/') == '':
            scores[SchemaType.WEBSITE] = 3.0
            scores[SchemaType.ORGANIZATION] = 2.5

        # Check for Organization indicators (about, company pages)
        if any(keyword in url.lower() for keyword in ['about', 'company', 'team']):
            scores[SchemaType.ORGANIZATION] = 2.0

        # Always consider basic WebPage
        if not scores:
            scores[SchemaType.WEB_PAGE] = 1.0

        # Sort by score and return top types
        sorted_types = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [schema_type for schema_type, _ in sorted_types[:3]]

    def _calculate_keyword_score(self, text: str, keywords: List[str]) -> float:
        """Calculate relevance score based on keyword presence."""
        score = 0.0
        for keyword in keywords:
            # Count occurrences
            count = text.count(keyword)
            if count > 0:
                # More occurrences = higher score, with diminishing returns
                score += min(count * 0.5, 2.0)
        return score

    def _has_faq_structure(self, content: str) -> bool:
        """Check if content has FAQ-like structure."""
        # Look for question patterns
        question_patterns = [
            r'\?[\s\n]',  # Questions ending with ?
            r'Q\d*[\.:)]',  # Q1: or Q. or Q)
            r'Question \d+',
        ]

        question_count = 0
        for pattern in question_patterns:
            matches = re.findall(pattern, content)
            question_count += len(matches)

        return question_count >= 3

    def _has_steps_structure(self, content: str) -> bool:
        """Check if content has step-by-step structure."""
        # Look for numbered steps
        step_patterns = [
            r'Step \d+',
            r'^\d+\.',  # Lines starting with numbers
            r'\d+\)',  # Numbers followed by )
        ]

        step_count = 0
        for pattern in step_patterns:
            matches = re.findall(pattern, content, re.MULTILINE)
            step_count += len(matches)

        return step_count >= 3

    def _has_contact_info(self, content: str) -> bool:
        """Check if content has contact information."""
        # Phone number pattern
        phone_pattern = r'\+?[\d\s\-\(\)]{10,}'
        # Email pattern
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        # Address indicators
        address_keywords = ['address', 'street', 'city', 'zip', 'postal']

        has_phone = bool(re.search(phone_pattern, content))
        has_email = bool(re.search(email_pattern, content))
        has_address = any(keyword in content.lower() for keyword in address_keywords)

        return has_phone or has_email or has_address

    def get_schema_priority(self, schema_type: SchemaType) -> int:
        """
        Get priority for schema type (lower = higher priority).

        Used to determine which schema to show first in UI.
        """
        priority_map = {
            SchemaType.ARTICLE: 1,
            SchemaType.BLOG_POSTING: 1,
            SchemaType.NEWS_ARTICLE: 1,
            SchemaType.PRODUCT: 1,
            SchemaType.FAQ_PAGE: 2,
            SchemaType.HOW_TO: 2,
            SchemaType.LOCAL_BUSINESS: 2,
            SchemaType.ORGANIZATION: 3,
            SchemaType.PERSON: 3,
            SchemaType.WEBSITE: 4,
            SchemaType.WEB_PAGE: 5,
            SchemaType.BREADCRUMB_LIST: 6,
        }
        return priority_map.get(schema_type, 10)


# Singleton instance
schema_detector = SchemaDetector()
