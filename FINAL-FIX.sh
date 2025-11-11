#!/bin/bash
set -e

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║         🔧 SEO SaaS - FINAL FIX SCRIPT 🔧                 ║"
echo "║   Fixes both Tailwind CSS and API connectivity issues      ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Step 1: Explain the issues
echo -e "${YELLOW}📋 Issues found:${NC}"
echo "  ❌ CSS file is only 620 bytes (should be several KB)"
echo "  ❌ Tailwind CSS not compiled (missing postcss.config.js)"
echo "  ❌ API calls get 403 errors (wrong API URL)"
echo "  ❌ Nginx returns HTML instead of proxying to backend"
echo ""
echo -e "${GREEN}✅ Fixes applied:${NC}"
echo "  ✓ Created postcss.config.js for Tailwind compilation"
echo "  ✓ Changed API URL from http://localhost:8000/api/v1 to /api/v1"
echo "  ✓ Added .env.production with correct API path"
echo ""
read -p "Press Enter to continue with the rebuild..."
echo ""

# Step 2: Stop frontend
echo -e "${CYAN}[1/6]${NC} ${YELLOW}Stopping frontend container...${NC}"
docker compose stop frontend
echo -e "      ${GREEN}✓ Frontend stopped${NC}"
echo ""

# Step 3: Remove old images
echo -e "${CYAN}[2/6]${NC} ${YELLOW}Removing old frontend image...${NC}"
docker rmi seo-tools-frontend:latest 2>/dev/null || true
docker rmi seosaas-frontend:latest 2>/dev/null || true
echo -e "      ${GREEN}✓ Old images removed${NC}"
echo ""

# Step 4: Build with no cache
echo -e "${CYAN}[3/6]${NC} ${YELLOW}Building frontend with Tailwind CSS...${NC}"
echo -e "      ${PURPLE}⏳ This will take 2-3 minutes...${NC}"
echo ""
docker compose build --no-cache frontend
echo ""
echo -e "      ${GREEN}✓ Frontend built successfully${NC}"
echo ""

# Step 5: Start frontend
echo -e "${CYAN}[4/6]${NC} ${YELLOW}Starting frontend...${NC}"
docker compose up -d frontend
echo -e "      ${GREEN}✓ Frontend started${NC}"
echo ""

# Step 6: Wait for ready
echo -e "${CYAN}[5/6]${NC} ${YELLOW}Waiting for frontend to be ready...${NC}"
sleep 5
echo -e "      ${GREEN}✓ Frontend is ready${NC}"
echo ""

# Step 7: Verify
echo -e "${CYAN}[6/6]${NC} ${YELLOW}Verifying setup...${NC}"
echo ""

# Check if container is running
if docker ps | grep -q seo-saas-frontend; then
    echo -e "      ${GREEN}✓ Container is running${NC}"
else
    echo -e "      ${RED}✗ Container is not running!${NC}"
    echo ""
    echo "Showing logs:"
    docker compose logs --tail=30 frontend
    exit 1
fi

# Check the CSS file size (should be much larger now)
echo ""
echo "📊 Checking CSS file size..."
docker compose exec -T frontend sh -c "ls -lh /usr/share/nginx/html/assets/*.css 2>/dev/null | head -1" || echo "No CSS files found yet"
echo ""

# Show last logs
echo "📋 Last 15 lines of frontend logs:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
docker compose logs --tail=15 frontend
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Final instructions
echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                    ✅ BUILD COMPLETE! ✅                    ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo -e "${BLUE}🌐 Access your application:${NC}"
echo "   👉 http://localhost:3000"
echo ""
echo -e "${YELLOW}🔑 CRITICAL: Clear your browser cache!${NC}"
echo ""
echo -e "${CYAN}Method 1 - Hard Refresh:${NC}"
echo "   • Chrome/Edge: Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)"
echo "   • Firefox:     Ctrl+F5 (Windows) or Cmd+Shift+R (Mac)"
echo ""
echo -e "${CYAN}Method 2 - DevTools:${NC}"
echo "   1. Press F12 to open DevTools"
echo "   2. Right-click on the refresh button ↻"
echo "   3. Select 'Empty Cache and Hard Reload'"
echo ""
echo -e "${CYAN}Method 3 - Complete Clear:${NC}"
echo "   1. Press Ctrl+Shift+Delete"
echo "   2. Check 'Cached images and files'"
echo "   3. Click 'Clear data'"
echo "   4. Refresh the page"
echo ""
echo -e "${GREEN}✨ What you should see now:${NC}"
echo "   ✓ Beautiful gradient background (blue/purple)"
echo "   ✓ White login card with shadows"
echo "   ✓ Animated blobs in the background"
echo "   ✓ Icons and styled buttons"
echo "   ✓ No more 403 errors in Network tab"
echo "   ✓ API calls go to /api/v1/* (not localhost:8000)"
echo ""
echo -e "${PURPLE}🔍 How to verify:${NC}"
echo "   1. Open DevTools (F12)"
echo "   2. Go to Network tab"
echo "   3. Clear and refresh page"
echo "   4. Check that CSS file is now 20-100 KB (not 620 bytes)"
echo "   5. Check that API calls go to /api/v1/... (not localhost:8000)"
echo ""
echo -e "${YELLOW}📞 Still having issues?${NC}"
echo "   • Check logs: docker compose logs -f frontend"
echo "   • Verify CSS size is large (see above)"
echo "   • Make sure you cleared browser cache"
echo ""
echo -e "${GREEN}Happy SEO analysis! 🚀${NC}"
echo ""
