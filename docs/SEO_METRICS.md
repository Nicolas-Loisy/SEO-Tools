# SEO Metrics Calculation Guide

This document explains how SEO Score and PageRank are calculated in the SEO Tools application.

## Table of Contents

- [SEO Score Calculation](#seo-score-calculation)
- [PageRank Calculation](#pagerank-calculation)
- [Important Notes](#important-notes)

---

## SEO Score Calculation

The **SEO Score** is calculated on a scale of **0-100 points** based on 6 key criteria. Each criterion contributes a specific number of points to the total score.

### Scoring Breakdown

#### 1. Title Tag (20 points max)

The page title is one of the most important on-page SEO factors.

| Condition | Points | Description |
|-----------|--------|-------------|
| **Optimal** (50-60 characters) | 20 | Perfect length for search results |
| **Acceptable** (30-70 characters) | 15-18 | Decent but not optimal |
| **Too Short** (< 30 characters) | 10 | Not descriptive enough |
| **Missing** | 0 | Critical SEO issue |

**Recommendations:**
- Too short: Add more descriptive text (aim for 50-60 characters)
- Too long: May be truncated in search results (keep under 60 characters)

#### 2. Meta Description (20 points max)

The meta description appears in search results and impacts click-through rates.

| Condition | Points | Description |
|-----------|--------|-------------|
| **Optimal** (150-160 characters) | 20 | Perfect length for search results |
| **Acceptable** (120-180 characters) | 15-18 | Decent but not optimal |
| **Too Short** (< 120 characters) | 10 | Not compelling enough |
| **Missing** | 0 | Search engines will auto-generate |

**Recommendations:**
- Too short: Add more compelling description (aim for 150-160 characters)
- Too long: May be truncated in search results (keep under 160 characters)

#### 3. H1 Heading (15 points max)

The main heading should clearly describe the page content.

| Condition | Points | Description |
|-----------|--------|-------------|
| **Optimal** (20-70 characters) | 15 | Clear and focused |
| **Too Short** (< 20 characters) | 8 | Not descriptive enough |
| **Too Long** (> 70 characters) | 12 | Too verbose |
| **Missing** | 0 | Critical SEO issue |

**Recommendations:**
- Include target keywords naturally
- Keep it concise and descriptive

#### 4. Content Length (20 points max)

Content depth is a ranking factor. Longer, quality content tends to rank better.

| Word Count | Points | Description |
|------------|--------|-------------|
| **≥ 1000 words** | 20 | Excellent in-depth content |
| **500-999 words** | 18 | Good content depth |
| **300-499 words** | 15 | Acceptable minimum |
| **100-299 words** | 10 | Thin content |
| **< 100 words** | 5 | Very thin content |

**Recommendations:**
- Aim for at least 300 words for basic pages
- 1000+ words for content pages and blog posts
- Focus on quality over quantity

#### 5. HTTP Status Code (15 points max)

The HTTP response code indicates page health and accessibility.

| Status Code | Points | Description |
|-------------|--------|-------------|
| **200 OK** | 15 | Perfect - page loads successfully |
| **2xx Success** | 14 | Other success codes |
| **3xx Redirect** | 8 | Redirects slow down crawling |
| **4xx/5xx Error** | 0 | Page is broken or inaccessible |

**Recommendations:**
- Fix 404 errors immediately
- Avoid redirect chains
- Ensure all pages return 200 OK

#### 6. Internal Links (10 points max)

Internal linking helps with site navigation and distributes PageRank.

| Link Count | Points | Description |
|------------|--------|-------------|
| **3-100 links** | 10 | Optimal internal linking |
| **1-2 links** | 5 | Too few connections |
| **> 100 links** | 7 | May dilute link equity |
| **0 links** | 0 | Orphan page - bad for SEO |

**Recommendations:**
- Include 3-10 relevant internal links per page
- Link to related content
- Avoid excessive linking

### Score Interpretation

| Score Range | Grade | Interpretation |
|-------------|-------|----------------|
| **90-100** | Excellent | Page is well-optimized for SEO |
| **70-89** | Good | Solid SEO fundamentals in place |
| **50-69** | Average | Needs improvement in several areas |
| **30-49** | Poor | Multiple critical issues to fix |
| **0-29** | Very Poor | Significant SEO problems |

### Implementation

**File:** `backend/app/services/seo_analyzer.py`

**Function:** `SEOAnalyzer.analyze_page()`

**Returns:** Tuple of `(score: float, recommendations: List[Dict])`

The function analyzes each criterion and returns:
- A score rounded to 1 decimal place (0.0 - 100.0)
- A list of specific recommendations for improvement

---

## PageRank Calculation

**PageRank** is Google's algorithm for measuring the importance of pages based on the link graph structure.

### Algorithm

The PageRank is calculated using NetworkX's implementation of the PageRank algorithm:

```python
import networkx as nx

pagerank = nx.pagerank(G, alpha=0.85)
```

### Parameters

- **alpha = 0.85**: Damping factor (standard value)
  - 85% probability of following a link
  - 15% probability of random teleportation to any page

### How It Works

1. **Initialize**: All pages start with equal PageRank (1/N where N = total pages)

2. **Iterate**: Each page distributes its PageRank to pages it links to:
   ```
   PR(A) = (1-d) + d * Σ(PR(Ti) / C(Ti))
   ```
   Where:
   - `PR(A)` = PageRank of page A
   - `d` = damping factor (0.85)
   - `PR(Ti)` = PageRank of pages linking to A
   - `C(Ti)` = number of outbound links from page Ti

3. **Converge**: Repeat until PageRank values stabilize

### Interpretation

| PageRank | Interpretation |
|----------|---------------|
| **High (> 0.01)** | Important page with many quality incoming links |
| **Medium (0.001 - 0.01)** | Average importance |
| **Low (< 0.001)** | Few or low-quality incoming links |

### Example

```
Page A (PR = 0.05) → Page B
Page C (PR = 0.03) → Page B
Page D (PR = 0.02) → Page B

→ Page B will have high PageRank because it receives links from important pages
```

### Graph Metrics

The system also calculates:

- **Hub Pages**: Pages with many outgoing links (high out-degree)
- **Authority Pages**: Pages with high PageRank (many quality incoming links)
- **Orphan Pages**: Pages with zero incoming links (in-degree = 0)

### Implementation

**File:** `backend/app/services/link_graph.py`

**Key Functions:**
- `build_graph()`: Constructs directed graph from pages
- `calculate_pagerank()`: Computes PageRank for all nodes
- `find_hub_pages()`: Identifies pages with most outgoing links
- `find_authority_pages()`: Identifies pages with highest PageRank
- `find_orphan_pages()`: Identifies pages with no incoming links

---

## Important Notes

### Current Limitation: Synthetic Link Graph

⚠️ **The current implementation builds a synthetic link graph** based on page depth hierarchy (line 113-117 in `link_graph.py`):

```python
# Synthetic edges based on depth hierarchy
if page.depth < 5:
    targets = [p for p in pages if p.depth == page.depth + 1]
    for target in targets[:5]:  # Limit to 5 links per page
        G.add_edge(page.id, target.id)
```

This means:
- Pages at depth N link to pages at depth N+1
- Maximum 5 links per page
- **Does NOT reflect actual HTML links**

### Future Improvement

For accurate PageRank calculation, the system should:

1. **Parse actual HTML links** from `rendered_html` field
2. **Use the `links` database table** which stores real internal links:
   - `source_page_id`
   - `target_page_id`
   - `anchor_text`
   - `is_internal`

**Database Schema:**
```sql
SELECT
  l.source_page_id,
  l.target_page_id,
  l.anchor_text
FROM links l
WHERE l.is_internal = true
  AND l.source_page_id IN (SELECT id FROM pages WHERE project_id = ?)
```

This would provide:
- **Real link relationships** between pages
- **Accurate PageRank** based on actual site structure
- **Better hub/authority detection**
- **Anchor text analysis** for keyword optimization

### Database Tables

**Pages Table:**
```sql
CREATE TABLE pages (
  id SERIAL PRIMARY KEY,
  project_id INTEGER,
  url VARCHAR(2000),
  title VARCHAR(500),
  seo_score FLOAT DEFAULT 0.0,
  word_count INTEGER,
  depth INTEGER,
  internal_links_count INTEGER,
  ...
);
```

**Links Table:**
```sql
CREATE TABLE links (
  id SERIAL PRIMARY KEY,
  source_page_id INTEGER REFERENCES pages(id),
  target_page_id INTEGER REFERENCES pages(id),
  anchor_text TEXT,
  rel VARCHAR(100),
  is_internal BOOLEAN DEFAULT true,
  ...
);
```

---

## References

- **SEO Score**: `backend/app/services/seo_analyzer.py`
- **PageRank**: `backend/app/services/link_graph.py`
- **Database Models**: `backend/app/models/page.py`
- **Page Model**: Line 10-96 in `page.py`
- **Link Model**: Line 98-136 in `page.py`

## Further Reading

- [Google's Original PageRank Paper](http://infolab.stanford.edu/~backrub/google.html)
- [NetworkX PageRank Documentation](https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.link_analysis.pagerank_alg.pagerank.html)
- [Moz: On-Page SEO Factors](https://moz.com/learn/seo/on-page-factors)
