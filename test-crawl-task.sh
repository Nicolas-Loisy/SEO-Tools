#!/bin/bash

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║         🔍 Test Crawl Task Manually                      ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

echo "This script will test if Celery tasks work by:"
echo "  1. Checking backend logs for errors"
echo "  2. Manually sending a test task to Celery"
echo "  3. Watching worker logs"
echo ""

# Get the last crawl job ID
echo "Finding latest crawl job..."
JOB_ID=$(docker compose exec -T postgres psql -U seouser -d seosaas -t -c "SELECT id FROM crawl_jobs ORDER BY created_at DESC LIMIT 1;" | tr -d ' ')

if [ -z "$JOB_ID" ]; then
    echo "❌ No crawl jobs found in database"
    echo ""
    echo "Create a crawl job in the frontend first!"
    exit 1
fi

echo "✓ Found crawl job ID: $JOB_ID"
echo ""

# Check job status
echo "Current status:"
docker compose exec -T postgres psql -U seouser -d seosaas -c "SELECT id, project_id, mode, status, celery_task_id, created_at FROM crawl_jobs WHERE id = $JOB_ID;"
echo ""

# Check backend logs for errors
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Backend logs (last 30 lines):"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
docker compose logs --tail=30 backend | grep -i "crawl\|celery\|error" || echo "(No relevant logs found)"
echo ""

# Check if task was sent to Redis
echo "Checking Redis queues..."
CRAWLER_QUEUE=$(docker compose exec -T redis redis-cli llen crawler 2>/dev/null || echo "0")
CONTENT_QUEUE=$(docker compose exec -T redis redis-cli llen content 2>/dev/null || echo "0")
ANALYSIS_QUEUE=$(docker compose exec -T redis redis-cli llen analysis 2>/dev/null || echo "0")
echo "Tasks in 'crawler' queue: $CRAWLER_QUEUE"
echo "Tasks in 'content' queue: $CONTENT_QUEUE"
echo "Tasks in 'analysis' queue: $ANALYSIS_QUEUE"
echo ""

# Try to send task manually
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Manually triggering crawl task for job $JOB_ID..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
docker compose exec -T backend python <<EOF
from app.workers.crawler_tasks import crawl_site
print("✓ Task imported successfully")
task = crawl_site.delay($JOB_ID)
print(f"✓ Task sent to Celery: {task.id}")
EOF
echo ""

# Wait a bit
echo "Waiting 3 seconds..."
sleep 3
echo ""

# Check worker logs
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Worker logs (last 30 lines):"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
docker compose logs --tail=30 celery-worker
echo ""

# Check updated status
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Updated status:"
docker compose exec -T postgres psql -U seouser -d seosaas -c "SELECT id, status, started_at, finished_at, pages_crawled, error_message FROM crawl_jobs WHERE id = $JOB_ID;"
echo ""

echo "💡 If the status is still 'pending', check:"
echo "   1. Backend logs for import errors"
echo "   2. Worker logs for task processing"
echo "   3. Redis connection (both backend and worker must connect)"
echo ""
echo "📋 To watch logs in real-time:"
echo "   docker compose logs -f celery-worker backend"
echo ""
