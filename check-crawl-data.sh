#!/bin/bash

echo "╔══════════════════════════════════════════════════════════╗"
echo "║         Checking Crawl Data in Database                  ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

echo "1. Latest Crawl Jobs:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
docker compose exec -T postgres psql -U seouser -d seosaas -c "
SELECT
  id,
  project_id,
  mode,
  status,
  pages_crawled,
  pages_failed,
  created_at,
  completed_at
FROM crawl_jobs
ORDER BY created_at DESC
LIMIT 5;
"

echo ""
echo "2. Pages Crawled (from latest job):"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
LATEST_JOB=$(docker compose exec -T postgres psql -U seouser -d seosaas -t -c "SELECT id FROM crawl_jobs ORDER BY created_at DESC LIMIT 1;")

if [ -n "$LATEST_JOB" ]; then
  docker compose exec -T postgres psql -U seouser -d seosaas -c "
  SELECT
    id,
    url,
    status_code,
    title,
    SUBSTRING(meta_description, 1, 50) as description,
    word_count,
    internal_links_count,
    external_links_count
  FROM pages
  WHERE crawl_job_id = $LATEST_JOB
  ORDER BY created_at DESC
  LIMIT 10;
  "
else
  echo "No crawl jobs found"
fi

echo ""
echo "3. Project Statistics:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
docker compose exec -T postgres psql -U seouser -d seosaas -c "
SELECT
  p.id,
  p.name,
  p.domain,
  COUNT(DISTINCT cj.id) as total_crawls,
  COUNT(DISTINCT pg.id) as total_pages,
  p.last_crawl_at
FROM projects p
LEFT JOIN crawl_jobs cj ON p.id = cj.project_id
LEFT JOIN pages pg ON cj.id = pg.crawl_job_id
GROUP BY p.id
ORDER BY p.created_at DESC;
"
