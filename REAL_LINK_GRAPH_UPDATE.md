# Real Link Graph Implementation

## Problem

Previously, the link graph was **synthetic** - it created artificial links based on page depth:
- Pages at depth N linked to pages at depth N+1
- Maximum 5 links per page
- **Did NOT reflect actual HTML links on pages**

This resulted in:
- ❌ Inaccurate PageRank calculations
- ❌ Wrong hub/authority page detection
- ❌ Misleading graph analysis metrics

## Solution

The link graph now uses **real internal links** from the database `links` table.

### Changes Made

**File:** `backend/app/services/link_graph.py`

#### 1. Import Link Model

```python
from app.models.page import Page, Link
```

#### 2. Query Real Links from Database

**Before (Synthetic):**
```python
# Create synthetic edges based on depth hierarchy
if page.depth < 5:
    targets = [p for p in pages if p.depth == page.depth + 1]
    for target in targets[:5]:
        G.add_edge(page.id, target.id)
```

**After (Real Links):**
```python
# Get all page IDs in the graph
page_ids = [page.id for page in pages]

# Query all internal links between these pages
links = db.query(Link).filter(
    Link.source_page_id.in_(page_ids),
    Link.target_page_id.in_(page_ids),
    Link.is_internal == True
).all()

# Add edges to the graph with anchor text
for link in links:
    G.add_edge(
        link.source_page_id,
        link.target_page_id,
        anchor_text=link.anchor_text,
        rel=link.rel
    )
```

#### 3. Include Anchor Text in Graph Export

**Before:**
```python
edges.append({
    "source": source,
    "target": target
})
```

**After:**
```python
edges.append({
    "source": source,
    "target": target,
    "anchor_text": edge_data.get("anchor_text", ""),
    "rel": edge_data.get("rel", "")
})
```

## Benefits

### ✅ Accurate PageRank
- PageRank now reflects **actual link structure** of the site
- Pages that receive many real links get higher PageRank
- Orphan pages are correctly identified (pages with no real incoming links)

### ✅ Real Hub/Authority Detection
- **Hub pages**: Pages with many **real outgoing links**
- **Authority pages**: Pages with high PageRank from **real incoming links**

### ✅ Anchor Text Analysis
- Can now analyze anchor text used in internal links
- Future feature: Optimize anchor text for better internal linking

### ✅ Better Link Recommendations
- Recommendations based on actual site structure
- Can suggest adding links where they're truly missing

## Database Schema

The `links` table structure:

```sql
CREATE TABLE links (
    id SERIAL PRIMARY KEY,
    source_page_id INTEGER REFERENCES pages(id) ON DELETE CASCADE,
    target_page_id INTEGER REFERENCES pages(id) ON DELETE CASCADE,
    anchor_text TEXT,
    rel VARCHAR(100),  -- e.g., "nofollow"
    is_internal BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(source_page_id, target_page_id)
);
```

## How Links Are Populated

Links are extracted during the crawling process:

**File:** `backend/app/workers/crawler_tasks.py`

When a page is crawled:
1. HTML is parsed for `<a>` tags
2. Internal links (same domain) are identified
3. `Link` records are created with:
   - `source_page_id`: Current page
   - `target_page_id`: Linked page
   - `anchor_text`: Text inside `<a>` tag
   - `is_internal`: True for same-domain links

## Performance

**Query Optimization:**
- Uses `IN` clause to fetch all links for analyzed pages in one query
- Filters only internal links (`is_internal = true`)
- Only links between pages in the current graph

**Example:**
```
Project with 1000 pages:
- Old: 0 database queries (synthetic links)
- New: 1 database query (fetch all real links)
- Query time: ~50-200ms
```

## Logging

The system now logs the number of real links found:

```
[LinkGraph] Building graph for project 1 with 856 pages (max: 1000)
[LinkGraph] Found 3,421 real internal links between 856 pages
```

## Future Enhancements

### 1. Anchor Text Optimization
- Analyze anchor text distribution
- Suggest better anchor text for SEO
- Detect over-optimization (same anchor text repeated)

### 2. Link Context Analysis
- Extract surrounding text around links
- Analyze relevance of link placement
- Suggest contextual links

### 3. Broken Link Detection
- Detect links to 404 pages
- Suggest fixing or removing broken links

### 4. Link Velocity Tracking
- Track when links are added/removed
- Alert on sudden link changes
- Historical link graph analysis

## Testing

To verify real links are being used:

1. Crawl a project with real internal links
2. Check the database:
   ```sql
   SELECT COUNT(*) FROM links WHERE is_internal = true;
   ```
3. View graph analysis in frontend
4. Verify PageRank and hub/authority pages make sense

## Migration

**No migration needed** - the `links` table already exists and is populated during crawling.

If you have existing crawled projects:
- Links are already in the database
- Simply rebuild the graph analysis to use real links
- No need to re-crawl

## Related Files

- `backend/app/services/link_graph.py` - Graph building logic
- `backend/app/models/page.py` - Page and Link models
- `backend/app/workers/crawler_tasks.py` - Link extraction during crawl
- `docs/SEO_METRICS.md` - Documentation on SEO metrics
- `frontend/src/pages/InternalLinking.tsx` - Frontend display

## Author

Updated in branch: `claude/fix-real-link-graph`

## See Also

- [SEO Metrics Documentation](docs/SEO_METRICS.md)
- [Architecture Documentation](docs/ARCHITECTURE.md)
