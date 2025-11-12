"""JSON-LD generator service for structured data."""

from typing import Dict, Any, Optional, List
from datetime import datetime
from urllib.parse import urlparse, urljoin
import json
import re
from bs4 import BeautifulSoup

from app.services.schema_detector import SchemaType
from app.models.page import Page


class JSONLDGenerator:
    """Service for generating Schema.org JSON-LD markup."""

    def _extract_metadata_from_html(self, page: Page) -> Dict[str, Any]:
        """Extract rich metadata from page HTML."""
        metadata = {
            'images': [],
            'author': None,
            'published_date': None,
            'modified_date': None,
            'logo': None,
        }

        if not page.html_content:
            return metadata

        try:
            soup = BeautifulSoup(page.html_content, 'lxml')
            base_url = f"{urlparse(page.url).scheme}://{urlparse(page.url).netloc}"

            # Extract images
            # 1. OpenGraph image
            og_image = soup.find('meta', property='og:image')
            if og_image and og_image.get('content'):
                img_url = og_image['content']
                if not img_url.startswith('http'):
                    img_url = urljoin(base_url, img_url)
                metadata['images'].append(img_url)

            # 2. Twitter card image
            twitter_image = soup.find('meta', attrs={'name': 'twitter:image'})
            if twitter_image and twitter_image.get('content'):
                img_url = twitter_image['content']
                if not img_url.startswith('http'):
                    img_url = urljoin(base_url, img_url)
                if img_url not in metadata['images']:
                    metadata['images'].append(img_url)

            # 3. First article image
            article = soup.find(['article', 'main'])
            if article:
                first_img = article.find('img', src=True)
                if first_img:
                    img_url = first_img['src']
                    if not img_url.startswith('http'):
                        img_url = urljoin(base_url, img_url)
                    if img_url not in metadata['images']:
                        metadata['images'].append(img_url)

            # Extract author
            # 1. Meta author
            author_meta = soup.find('meta', attrs={'name': 'author'})
            if author_meta and author_meta.get('content'):
                metadata['author'] = author_meta['content']

            # 2. Article:author
            if not metadata['author']:
                article_author = soup.find('meta', property='article:author')
                if article_author and article_author.get('content'):
                    metadata['author'] = article_author['content']

            # 3. Schema.org author
            if not metadata['author']:
                schema_author = soup.find('span', itemprop='author')
                if schema_author:
                    metadata['author'] = schema_author.get_text(strip=True)

            # Extract dates
            # 1. Article published time
            published_meta = soup.find('meta', property='article:published_time')
            if published_meta and published_meta.get('content'):
                metadata['published_date'] = published_meta['content']

            # 2. Time tag with datetime
            if not metadata['published_date']:
                time_tag = soup.find('time', datetime=True)
                if time_tag:
                    metadata['published_date'] = time_tag['datetime']

            # 3. Modified time
            modified_meta = soup.find('meta', property='article:modified_time')
            if modified_meta and modified_meta.get('content'):
                metadata['modified_date'] = modified_meta['content']

            # Extract logo
            logo_meta = soup.find('meta', property='og:logo')
            if logo_meta and logo_meta.get('content'):
                metadata['logo'] = logo_meta['content']

            # Link rel icon as fallback
            if not metadata['logo']:
                icon_link = soup.find('link', rel='icon')
                if icon_link and icon_link.get('href'):
                    logo_url = icon_link['href']
                    if not logo_url.startswith('http'):
                        logo_url = urljoin(base_url, logo_url)
                    metadata['logo'] = logo_url

        except Exception as e:
            # Fail silently, return empty metadata
            pass

        return metadata

    def generate_schema(
        self,
        page: Page,
        schema_type: SchemaType,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate JSON-LD schema for a page.

        Args:
            page: Page model instance
            schema_type: Type of schema to generate
            additional_data: Optional additional data to include

        Returns:
            JSON-LD dictionary
        """
        # Base context
        schema = {
            "@context": "https://schema.org",
            "@type": schema_type.value
        }

        # Route to appropriate generator
        if schema_type in [SchemaType.ARTICLE, SchemaType.BLOG_POSTING, SchemaType.NEWS_ARTICLE]:
            schema.update(self._generate_article_schema(page, schema_type, additional_data))
        elif schema_type == SchemaType.PRODUCT:
            schema.update(self._generate_product_schema(page, additional_data))
        elif schema_type == SchemaType.ORGANIZATION:
            schema.update(self._generate_organization_schema(page, additional_data))
        elif schema_type == SchemaType.LOCAL_BUSINESS:
            schema.update(self._generate_local_business_schema(page, additional_data))
        elif schema_type == SchemaType.FAQ_PAGE:
            schema.update(self._generate_faq_schema(page, additional_data))
        elif schema_type == SchemaType.HOW_TO:
            schema.update(self._generate_howto_schema(page, additional_data))
        elif schema_type == SchemaType.WEBSITE:
            schema.update(self._generate_website_schema(page, additional_data))
        elif schema_type == SchemaType.WEB_PAGE:
            schema.update(self._generate_webpage_schema(page, additional_data))
        elif schema_type == SchemaType.BREADCRUMB_LIST:
            schema.update(self._generate_breadcrumb_schema(page, additional_data))
        else:
            schema.update(self._generate_webpage_schema(page, additional_data))

        return schema

    def _generate_article_schema(
        self,
        page: Page,
        schema_type: SchemaType,
        additional_data: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate Article, BlogPosting, or NewsArticle schema."""
        parsed_url = urlparse(page.url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"

        # Extract metadata from HTML
        metadata = self._extract_metadata_from_html(page)

        # Use extracted dates or fallback to crawl dates
        published_date = metadata['published_date'] or (
            page.created_at.isoformat() if page.created_at else datetime.utcnow().isoformat()
        )
        modified_date = metadata['modified_date'] or (
            page.updated_at.isoformat() if page.updated_at else datetime.utcnow().isoformat()
        )

        schema = {
            "headline": page.title or "Untitled",
            "description": page.meta_description or "",
            "url": page.url,
            "datePublished": published_date,
            "dateModified": modified_date,
        }

        # Add author (priority: additional_data > extracted > default)
        if additional_data and 'author' in additional_data:
            schema["author"] = {
                "@type": "Person",
                "name": additional_data['author']
            }
        elif metadata['author']:
            schema["author"] = {
                "@type": "Person",
                "name": metadata['author']
            }
        else:
            schema["author"] = {
                "@type": "Organization",
                "name": parsed_url.netloc
            }

        # Add publisher with logo
        publisher = {
            "@type": "Organization",
            "name": parsed_url.netloc,
            "url": base_url
        }

        # Add logo if available
        if metadata['logo']:
            publisher["logo"] = {
                "@type": "ImageObject",
                "url": metadata['logo']
            }

        if additional_data and 'publisher' in additional_data:
            schema["publisher"] = additional_data['publisher']
        else:
            schema["publisher"] = publisher

        # Add images (priority: additional_data > extracted)
        if additional_data and 'image' in additional_data:
            schema["image"] = additional_data['image']
        elif metadata['images']:
            # Google recommends multiple images for better appearance
            schema["image"] = metadata['images'][:3]  # Max 3 images

        # Add word count if available
        if page.word_count and page.word_count > 0:
            schema["wordCount"] = page.word_count

        # Add main entity of page
        schema["mainEntityOfPage"] = {
            "@type": "WebPage",
            "@id": page.url
        }

        return schema

    def _generate_product_schema(
        self,
        page: Page,
        additional_data: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate Product schema."""
        schema = {
            "name": page.title or "Product",
            "description": page.meta_description or "",
            "url": page.url,
        }

        # These fields typically come from additional_data
        if additional_data:
            if 'price' in additional_data:
                schema["offers"] = {
                    "@type": "Offer",
                    "price": additional_data['price'],
                    "priceCurrency": additional_data.get('currency', 'USD'),
                    "availability": additional_data.get('availability', 'https://schema.org/InStock'),
                    "url": page.url
                }

            if 'brand' in additional_data:
                schema["brand"] = {
                    "@type": "Brand",
                    "name": additional_data['brand']
                }

            if 'image' in additional_data:
                schema["image"] = additional_data['image']

            if 'sku' in additional_data:
                schema["sku"] = additional_data['sku']

            if 'rating' in additional_data:
                schema["aggregateRating"] = {
                    "@type": "AggregateRating",
                    "ratingValue": additional_data['rating'],
                    "reviewCount": additional_data.get('review_count', 1)
                }

        return schema

    def _generate_organization_schema(
        self,
        page: Page,
        additional_data: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate Organization schema."""
        parsed_url = urlparse(page.url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"

        schema = {
            "name": additional_data.get('name', parsed_url.netloc) if additional_data else parsed_url.netloc,
            "url": base_url,
            "description": page.meta_description or ""
        }

        if additional_data:
            if 'logo' in additional_data:
                schema["logo"] = additional_data['logo']

            if 'social_links' in additional_data:
                schema["sameAs"] = additional_data['social_links']

            if 'contact_point' in additional_data:
                schema["contactPoint"] = additional_data['contact_point']

        return schema

    def _generate_local_business_schema(
        self,
        page: Page,
        additional_data: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate LocalBusiness schema."""
        parsed_url = urlparse(page.url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"

        schema = {
            "name": additional_data.get('name', parsed_url.netloc) if additional_data else parsed_url.netloc,
            "url": base_url,
            "description": page.meta_description or ""
        }

        if additional_data:
            if 'address' in additional_data:
                schema["address"] = {
                    "@type": "PostalAddress",
                    **additional_data['address']
                }

            if 'phone' in additional_data:
                schema["telephone"] = additional_data['phone']

            if 'opening_hours' in additional_data:
                schema["openingHours"] = additional_data['opening_hours']

            if 'geo' in additional_data:
                schema["geo"] = {
                    "@type": "GeoCoordinates",
                    **additional_data['geo']
                }

            if 'price_range' in additional_data:
                schema["priceRange"] = additional_data['price_range']

        return schema

    def _generate_faq_schema(
        self,
        page: Page,
        additional_data: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate FAQPage schema."""
        schema = {
            "name": page.title or "FAQ",
            "url": page.url
        }

        # FAQ items should come from additional_data
        if additional_data and 'questions' in additional_data:
            schema["mainEntity"] = [
                {
                    "@type": "Question",
                    "name": qa['question'],
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": qa['answer']
                    }
                }
                for qa in additional_data['questions']
            ]

        return schema

    def _generate_howto_schema(
        self,
        page: Page,
        additional_data: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate HowTo schema."""
        schema = {
            "name": page.title or "How To",
            "description": page.meta_description or "",
            "url": page.url
        }

        # Steps should come from additional_data
        if additional_data and 'steps' in additional_data:
            schema["step"] = [
                {
                    "@type": "HowToStep",
                    "name": step['name'],
                    "text": step['text'],
                    "url": f"{page.url}#step{idx + 1}" if 'url' not in step else step['url']
                }
                for idx, step in enumerate(additional_data['steps'])
            ]

        if additional_data and 'total_time' in additional_data:
            schema["totalTime"] = additional_data['total_time']

        return schema

    def _generate_website_schema(
        self,
        page: Page,
        additional_data: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate WebSite schema."""
        parsed_url = urlparse(page.url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"

        schema = {
            "name": page.title or parsed_url.netloc,
            "url": base_url,
            "description": page.meta_description or ""
        }

        # Add search action for homepage
        if additional_data and 'search_url' in additional_data:
            schema["potentialAction"] = {
                "@type": "SearchAction",
                "target": additional_data['search_url'],
                "query-input": "required name=search_term_string"
            }
        else:
            # Default search action
            schema["potentialAction"] = {
                "@type": "SearchAction",
                "target": f"{base_url}/search?q={{search_term_string}}",
                "query-input": "required name=search_term_string"
            }

        return schema

    def _generate_webpage_schema(
        self,
        page: Page,
        additional_data: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate generic WebPage schema."""
        schema = {
            "name": page.title or "Web Page",
            "description": page.meta_description or "",
            "url": page.url
        }

        return schema

    def _generate_breadcrumb_schema(
        self,
        page: Page,
        additional_data: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate BreadcrumbList schema."""
        parsed_url = urlparse(page.url)
        base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
        path_parts = [p for p in parsed_url.path.split('/') if p]

        # Build breadcrumb items
        items = [{
            "@type": "ListItem",
            "position": 1,
            "name": "Home",
            "item": base_url
        }]

        current_path = base_url
        for idx, part in enumerate(path_parts, start=2):
            current_path += f"/{part}"
            items.append({
                "@type": "ListItem",
                "position": idx,
                "name": part.replace('-', ' ').replace('_', ' ').title(),
                "item": current_path
            })

        schema = {
            "itemListElement": items
        }

        return schema

    def validate_schema(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate JSON-LD schema.

        Returns validation result with errors/warnings.
        """
        errors = []
        warnings = []

        # Check required @context and @type
        if "@context" not in schema:
            errors.append("Missing required field: @context")

        if "@type" not in schema:
            errors.append("Missing required field: @type")

        # Validate JSON structure
        try:
            json.dumps(schema)
        except (TypeError, ValueError) as e:
            errors.append(f"Invalid JSON structure: {str(e)}")

        # Type-specific validation
        schema_type = schema.get("@type")
        if schema_type in ["Article", "BlogPosting", "NewsArticle"]:
            if "headline" not in schema:
                warnings.append("Missing recommended field: headline")
            if "datePublished" not in schema:
                warnings.append("Missing recommended field: datePublished")
            if "author" not in schema:
                warnings.append("Missing recommended field: author")

        elif schema_type == "Product":
            if "name" not in schema:
                errors.append("Missing required field for Product: name")
            if "offers" not in schema:
                warnings.append("Missing recommended field: offers")

        elif schema_type == "Organization":
            if "name" not in schema:
                errors.append("Missing required field for Organization: name")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }

    def format_for_html(self, schema: Dict[str, Any]) -> str:
        """
        Format JSON-LD schema for HTML insertion.

        Returns:
            Formatted <script> tag with JSON-LD
        """
        json_str = json.dumps(schema, indent=2, ensure_ascii=False)
        return f'<script type="application/ld+json">\n{json_str}\n</script>'


# Singleton instance
jsonld_generator = JSONLDGenerator()
