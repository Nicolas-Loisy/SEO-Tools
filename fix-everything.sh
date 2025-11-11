#!/bin/bash
set -e

echo "🔧 SEO SaaS - Complete Setup & Fix Script"
echo "=========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Step 1: Stop everything
echo -e "${YELLOW}📦 Step 1: Stopping all containers...${NC}"
docker compose down
echo -e "${GREEN}✓ Containers stopped${NC}"
echo ""

# Step 2: Initialize database
echo -e "${YELLOW}📊 Step 2: Starting database...${NC}"
docker compose up -d postgres redis
echo "⏳ Waiting for PostgreSQL to be ready..."
sleep 5
echo -e "${GREEN}✓ Database started${NC}"
echo ""

# Step 3: Run migrations
echo -e "${YELLOW}🔄 Step 3: Running database migrations...${NC}"
docker compose run --rm backend alembic upgrade head
echo -e "${GREEN}✓ Migrations completed${NC}"
echo ""

# Step 4: Bootstrap (create tenant + API key)
echo -e "${YELLOW}🔑 Step 4: Creating tenant and API key...${NC}"
echo ""
echo -e "${BLUE}================================================${NC}"
docker compose run --rm backend python scripts/bootstrap.py
echo -e "${BLUE}================================================${NC}"
echo ""
echo -e "${YELLOW}⚠️  IMPORTANT: Copy the API key above! You'll need it to login.${NC}"
echo ""
read -p "Press Enter once you've copied the API key..."
echo ""

# Step 5: Rebuild frontend
echo -e "${YELLOW}🎨 Step 5: Rebuilding frontend (this may take 2-3 minutes)...${NC}"
docker compose build --no-cache frontend
echo -e "${GREEN}✓ Frontend rebuilt${NC}"
echo ""

# Step 6: Start all services
echo -e "${YELLOW}🚀 Step 6: Starting all services...${NC}"
docker compose up -d
echo -e "${GREEN}✓ All services started${NC}"
echo ""

# Step 7: Show status
echo -e "${YELLOW}📋 Step 7: Checking service status...${NC}"
sleep 3
docker compose ps
echo ""

# Final instructions
echo ""
echo -e "${GREEN}=========================================="
echo "✅ SETUP COMPLETE!"
echo -e "==========================================${NC}"
echo ""
echo -e "${BLUE}📱 Access your application:${NC}"
echo "   Frontend: http://localhost"
echo "   Backend:  http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo -e "${YELLOW}🔑 Next steps:${NC}"
echo "   1. Open http://localhost in your browser"
echo "   2. Clear browser cache (Ctrl+Shift+R or Cmd+Shift+R)"
echo "   3. Enter the API key you copied earlier"
echo "   4. You should see the styled login page!"
echo ""
echo -e "${YELLOW}💡 Troubleshooting:${NC}"
echo "   - If styles don't appear: Clear browser cache completely"
echo "   - If API key doesn't work: Check the key you copied"
echo "   - Check logs: docker compose logs -f frontend"
echo "   - Check logs: docker compose logs -f backend"
echo ""
echo -e "${GREEN}Happy SEO analysis! 🚀${NC}"
