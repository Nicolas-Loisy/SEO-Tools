"""SEO Analysis Service - Calculates SEO scores and provides recommendations."""

from typing import Dict, List, Tuple


class SEOAnalyzer:
    """
    Analyze page SEO metrics and provide actionable recommendations.

    Scoring criteria:
    - Title: 20 points
    - Meta Description: 20 points
    - H1: 15 points
    - Content Length: 20 points
    - Status Code: 15 points
    - Internal Links: 10 points
    """

    @staticmethod
    def analyze_page(
        url: str,
        title: str | None,
        meta_description: str | None,
        h1: str | None,
        word_count: int,
        status_code: int | None,
        internal_links_count: int,
    ) -> Tuple[float, List[Dict[str, str]]]:
        """
        Analyze a page and return SEO score and recommendations.

        Args:
            url: Page URL
            title: Page title
            meta_description: Meta description
            h1: H1 heading
            word_count: Total word count
            status_code: HTTP status code
            internal_links_count: Number of internal links

        Returns:
            Tuple of (score, recommendations)
            - score: Float between 0 and 100
            - recommendations: List of dicts with 'type', 'severity', and 'message'
        """
        score = 0.0
        recommendations = []

        # 1. Title Analysis (20 points)
        if not title:
            recommendations.append({
                "type": "title",
                "severity": "critical",
                "message": "Missing title tag. Add a descriptive title (50-60 characters)."
            })
        elif len(title) < 30:
            score += 10
            recommendations.append({
                "type": "title",
                "severity": "warning",
                "message": f"Title is too short ({len(title)} chars). Optimal length is 50-60 characters."
            })
        elif len(title) > 60:
            score += 15
            recommendations.append({
                "type": "title",
                "severity": "warning",
                "message": f"Title is too long ({len(title)} chars). It may be truncated in search results. Aim for 50-60 characters."
            })
        elif 50 <= len(title) <= 60:
            score += 20
        else:
            score += 18

        # 2. Meta Description Analysis (20 points)
        if not meta_description:
            recommendations.append({
                "type": "meta_description",
                "severity": "high",
                "message": "Missing meta description. Add a compelling description (150-160 characters)."
            })
        elif len(meta_description) < 120:
            score += 10
            recommendations.append({
                "type": "meta_description",
                "severity": "warning",
                "message": f"Meta description is too short ({len(meta_description)} chars). Optimal length is 150-160 characters."
            })
        elif len(meta_description) > 160:
            score += 15
            recommendations.append({
                "type": "meta_description",
                "severity": "warning",
                "message": f"Meta description is too long ({len(meta_description)} chars). It may be truncated. Aim for 150-160 characters."
            })
        elif 150 <= len(meta_description) <= 160:
            score += 20
        else:
            score += 18

        # 3. H1 Analysis (15 points)
        if not h1:
            recommendations.append({
                "type": "h1",
                "severity": "high",
                "message": "Missing H1 heading. Add a clear, descriptive H1 that includes your target keyword."
            })
        elif len(h1) < 20:
            score += 8
            recommendations.append({
                "type": "h1",
                "severity": "info",
                "message": f"H1 is quite short ({len(h1)} chars). Consider making it more descriptive."
            })
        elif len(h1) > 70:
            score += 12
            recommendations.append({
                "type": "h1",
                "severity": "info",
                "message": f"H1 is quite long ({len(h1)} chars). Keep it concise and focused."
            })
        else:
            score += 15

        # 4. Content Length Analysis (20 points)
        if word_count < 300:
            if word_count < 100:
                score += 5
                recommendations.append({
                    "type": "content_length",
                    "severity": "critical",
                    "message": f"Very thin content ({word_count} words). Add at least 300 words of quality content."
                })
            else:
                score += 10
                recommendations.append({
                    "type": "content_length",
                    "severity": "warning",
                    "message": f"Content is short ({word_count} words). Aim for at least 300 words for better ranking."
                })
        elif word_count < 500:
            score += 15
        elif word_count >= 1000:
            score += 20
        else:
            score += 18

        # 5. Status Code Analysis (15 points)
        if status_code == 200:
            score += 15
        elif status_code and 200 <= status_code < 300:
            score += 14
        elif status_code and 300 <= status_code < 400:
            score += 8
            recommendations.append({
                "type": "status_code",
                "severity": "warning",
                "message": f"Page redirects (status {status_code}). Avoid redirect chains for better performance."
            })
        elif status_code and status_code >= 400:
            recommendations.append({
                "type": "status_code",
                "severity": "critical",
                "message": f"Page returns error status {status_code}. Fix broken pages."
            })
        else:
            recommendations.append({
                "type": "status_code",
                "severity": "warning",
                "message": "Could not determine page status."
            })

        # 6. Internal Links Analysis (10 points)
        if internal_links_count == 0:
            recommendations.append({
                "type": "internal_links",
                "severity": "warning",
                "message": "No internal links found. Add links to related content on your site."
            })
        elif internal_links_count < 3:
            score += 5
            recommendations.append({
                "type": "internal_links",
                "severity": "info",
                "message": f"Only {internal_links_count} internal link(s). Add more links to improve site structure."
            })
        elif internal_links_count > 100:
            score += 7
            recommendations.append({
                "type": "internal_links",
                "severity": "info",
                "message": f"Many internal links ({internal_links_count}). Ensure they're all relevant."
            })
        else:
            score += 10

        # Round score to 1 decimal place
        score = round(score, 1)

        # Add success message if score is good
        if score >= 90:
            recommendations.insert(0, {
                "type": "overall",
                "severity": "success",
                "message": "Excellent! Your page is well-optimized for SEO."
            })
        elif score >= 70:
            recommendations.insert(0, {
                "type": "overall",
                "severity": "success",
                "message": "Good job! Your page has solid SEO fundamentals."
            })

        return score, recommendations


# Singleton instance
seo_analyzer = SEOAnalyzer()
