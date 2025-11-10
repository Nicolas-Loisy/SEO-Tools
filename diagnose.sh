#!/bin/bash

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║         🔍 SEO SaaS - Diagnostic Script                  ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

ISSUES=0

# Check 1: Docker Compose running
echo -e "${BLUE}[1/8]${NC} Checking if Docker Compose is running..."
if docker compose ps > /dev/null 2>&1; then
    echo -e "      ${GREEN}✓ Docker Compose is running${NC}"
else
    echo -e "      ${RED}✗ Docker Compose not running!${NC}"
    echo "      Run: docker compose up -d"
    ISSUES=$((ISSUES+1))
fi
echo ""

# Check 2: Backend container
echo -e "${BLUE}[2/8]${NC} Checking backend container..."
if docker compose ps | grep -q "seo-saas-backend.*Up"; then
    echo -e "      ${GREEN}✓ Backend is running${NC}"

    # Check backend health
    if docker compose exec -T backend curl -f http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "      ${GREEN}✓ Backend is healthy${NC}"
    else
        echo -e "      ${YELLOW}⚠ Backend health check failed${NC}"
        ISSUES=$((ISSUES+1))
    fi
else
    echo -e "      ${RED}✗ Backend is not running!${NC}"
    ISSUES=$((ISSUES+1))
fi
echo ""

# Check 3: Frontend container
echo -e "${BLUE}[3/8]${NC} Checking frontend container..."
if docker compose ps | grep -q "seo-saas-frontend.*Up"; then
    echo -e "      ${GREEN}✓ Frontend is running${NC}"
else
    echo -e "      ${RED}✗ Frontend is not running!${NC}"
    ISSUES=$((ISSUES+1))
fi
echo ""

# Check 4: Network connectivity (frontend -> backend)
echo -e "${BLUE}[4/8]${NC} Checking network connectivity (frontend -> backend)..."
if docker compose exec -T frontend sh -c "wget -q -O- http://backend:8000/health" > /dev/null 2>&1; then
    echo -e "      ${GREEN}✓ Frontend can reach backend${NC}"
else
    echo -e "      ${RED}✗ Frontend CANNOT reach backend!${NC}"
    echo "      This is the main issue - containers can't communicate"
    ISSUES=$((ISSUES+1))
fi
echo ""

# Check 5: Backend API endpoint
echo -e "${BLUE}[5/8]${NC} Testing backend API directly..."
RESPONSE=$(docker compose exec -T backend curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/health 2>/dev/null)
if [ "$RESPONSE" = "200" ]; then
    echo -e "      ${GREEN}✓ Backend API responds (HTTP $RESPONSE)${NC}"
else
    echo -e "      ${RED}✗ Backend API issue (HTTP $RESPONSE)${NC}"
    ISSUES=$((ISSUES+1))
fi
echo ""

# Check 6: Frontend proxy to backend
echo -e "${BLUE}[6/8]${NC} Testing frontend -> backend proxy..."
PROXY_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000/api/v1/health 2>/dev/null)
if [ "$PROXY_RESPONSE" = "200" ]; then
    echo -e "      ${GREEN}✓ Nginx proxy works (HTTP $PROXY_RESPONSE)${NC}"
elif [ "$PROXY_RESPONSE" = "404" ]; then
    echo -e "      ${RED}✗ Nginx proxy returns 404 - not forwarding to backend${NC}"
    echo "      This means nginx.conf needs to be fixed"
    ISSUES=$((ISSUES+1))
elif [ "$PROXY_RESPONSE" = "502" ] || [ "$PROXY_RESPONSE" = "503" ]; then
    echo -e "      ${RED}✗ Nginx can't reach backend (HTTP $PROXY_RESPONSE)${NC}"
    echo "      Backend might be down or unreachable"
    ISSUES=$((ISSUES+1))
else
    echo -e "      ${YELLOW}⚠ Unexpected response (HTTP $PROXY_RESPONSE)${NC}"
    ISSUES=$((ISSUES+1))
fi
echo ""

# Check 7: Database connection
echo -e "${BLUE}[7/8]${NC} Checking database..."
if docker compose exec -T postgres pg_isready -U seouser -d seosaas > /dev/null 2>&1; then
    echo -e "      ${GREEN}✓ Database is ready${NC}"
else
    echo -e "      ${RED}✗ Database not ready${NC}"
    ISSUES=$((ISSUES+1))
fi
echo ""

# Check 8: Docker network
echo -e "${BLUE}[8/8]${NC} Checking Docker network..."
NETWORK=$(docker compose ps -q frontend | xargs docker inspect -f '{{range .NetworkSettings.Networks}}{{.NetworkID}}{{end}}' 2>/dev/null | cut -c1-12)
if [ -n "$NETWORK" ]; then
    echo -e "      ${GREEN}✓ Containers are on network: $NETWORK${NC}"

    # List containers on the same network
    echo "      Containers on this network:"
    docker network inspect $NETWORK 2>/dev/null | grep -A1 "Containers" -A 20 | grep "Name" | sed 's/.*"Name": "\(.*\)".*/        - \1/'
else
    echo -e "      ${YELLOW}⚠ Could not determine network${NC}"
fi
echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ $ISSUES -eq 0 ]; then
    echo -e "${GREEN}✅ All checks passed! Your setup looks good.${NC}"
    echo ""
    echo "If you still have issues:"
    echo "  1. Clear browser cache (Ctrl+Shift+R)"
    echo "  2. Check browser console for errors (F12)"
    echo "  3. Verify API key is valid"
else
    echo -e "${RED}❌ Found $ISSUES issue(s) that need fixing${NC}"
    echo ""
    echo -e "${YELLOW}Recommended fixes:${NC}"

    # If network issue
    if docker compose exec -T frontend sh -c "wget -q -O- http://backend:8000/health" > /dev/null 2>&1; then
        :
    else
        echo ""
        echo "📡 Network connectivity issue:"
        echo "   1. Stop everything: docker compose down"
        echo "   2. Restart: docker compose up -d"
        echo "   3. Wait 10 seconds"
        echo "   4. Re-run this diagnostic"
    fi

    # If proxy issue
    if [ "$PROXY_RESPONSE" = "404" ]; then
        echo ""
        echo "🔧 Nginx proxy issue:"
        echo "   1. The nginx.conf has been updated"
        echo "   2. Rebuild frontend: ./FINAL-FIX.sh"
        echo "   3. This will fix the proxy configuration"
    fi
fi
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Show logs if there are issues
if [ $ISSUES -gt 0 ]; then
    echo -e "${YELLOW}📋 Recent logs:${NC}"
    echo ""
    echo "Backend logs (last 10 lines):"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    docker compose logs --tail=10 backend
    echo ""
    echo "Frontend logs (last 10 lines):"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    docker compose logs --tail=10 frontend
    echo ""
fi

exit $ISSUES
