#!/bin/bash

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║         🔍 Celery Worker Diagnostic                      ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Check 1: Is Celery worker running?
echo -e "${BLUE}[1/5]${NC} Checking if Celery worker is running..."
if docker compose ps | grep -q "celery-worker.*Up"; then
    echo -e "      ${GREEN}✓ Celery worker is running${NC}"
else
    echo -e "      ${RED}✗ Celery worker is NOT running!${NC}"
    echo ""
    echo "      This is why crawls don't start. Starting it now..."
    docker compose up -d celery-worker
    sleep 3
fi
echo ""

# Check 2: Worker logs
echo -e "${BLUE}[2/5]${NC} Checking worker logs (last 20 lines)..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
docker compose logs --tail=20 celery-worker
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check 3: Redis connection
echo -e "${BLUE}[3/5]${NC} Checking Redis (Celery broker)..."
if docker compose exec -T redis redis-cli ping | grep -q "PONG"; then
    echo -e "      ${GREEN}✓ Redis is responding${NC}"
else
    echo -e "      ${RED}✗ Redis is not responding${NC}"
fi
echo ""

# Check 4: Check if tasks are in queue
echo -e "${BLUE}[4/5]${NC} Checking Celery queue..."
QUEUE_LENGTH=$(docker compose exec -T redis redis-cli llen celery 2>/dev/null || echo "0")
echo "      Tasks in queue: $QUEUE_LENGTH"
if [ "$QUEUE_LENGTH" -gt "0" ]; then
    echo -e "      ${YELLOW}⚠ There are $QUEUE_LENGTH pending tasks in the queue${NC}"
else
    echo -e "      ${GREEN}✓ Queue is empty (tasks are being processed)${NC}"
fi
echo ""

# Check 5: Active tasks
echo -e "${BLUE}[5/5]${NC} Checking active tasks..."
docker compose exec -T celery-worker celery -A app.workers.celery_app inspect active 2>/dev/null || echo "Could not inspect active tasks"
echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${YELLOW}📝 What happens when you start a crawl:${NC}"
echo ""
echo "  1. Frontend sends POST /api/v1/crawl/ → Backend"
echo "  2. Backend creates CrawlJob in DB (status: 'pending')"
echo "  3. Backend sends task to Celery (via Redis)"
echo "  4. Celery worker picks up the task"
echo "  5. Worker executes the crawl (status: 'running')"
echo "  6. Worker updates DB when done (status: 'completed')"
echo ""
echo -e "${YELLOW}💡 Common issues:${NC}"
echo ""
echo "  ❌ Worker not running → crawls stay 'pending' forever"
echo "  ❌ Redis down → tasks can't be queued"
echo "  ❌ Worker crashed → check logs above"
echo "  ❌ Wrong Redis URL → worker can't connect to broker"
echo ""
echo -e "${GREEN}✅ To manually start a crawl (for testing):${NC}"
echo ""
echo "  docker compose exec backend python -c \\"
echo "    from app.workers.tasks import process_crawl_job; \\"
echo "    process_crawl_job.delay(JOB_ID)\\"
echo ""
echo "  (Replace JOB_ID with your crawl job ID)"
echo ""
echo -e "${YELLOW}🔄 To restart the worker:${NC}"
echo ""
echo "  docker compose restart celery-worker"
echo ""
echo -e "${YELLOW}📋 To see worker logs in real-time:${NC}"
echo ""
echo "  docker compose logs -f celery-worker"
echo ""
