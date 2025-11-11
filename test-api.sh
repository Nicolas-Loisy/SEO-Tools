#!/bin/bash

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║         🧪 API Test Script                                ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Test 1: Backend health (no auth)
echo -e "${BLUE}[1/4]${NC} Testing backend health endpoint..."
HEALTH=$(curl -s http://localhost:8000/health)
if echo "$HEALTH" | grep -q "healthy"; then
    echo -e "      ${GREEN}✓ Backend is healthy${NC}"
    echo "      Response: $HEALTH"
else
    echo -e "      ${RED}✗ Backend health check failed${NC}"
    echo "      Response: $HEALTH"
fi
echo ""

# Test 2: Backend root (no auth)
echo -e "${BLUE}[2/4]${NC} Testing backend root endpoint..."
ROOT=$(curl -s http://localhost:8000/)
if echo "$ROOT" | grep -q "SEO"; then
    echo -e "      ${GREEN}✓ Backend root responds${NC}"
    echo "      Response: $ROOT"
else
    echo -e "      ${RED}✗ Backend root failed${NC}"
    echo "      Response: $ROOT"
fi
echo ""

# Test 3: Frontend proxy to backend health
echo -e "${BLUE}[3/4]${NC} Testing nginx proxy (frontend -> backend health)..."
PROXY=$(curl -s http://localhost:3000/health 2>/dev/null)
if echo "$PROXY" | grep -q "healthy"; then
    echo -e "      ${GREEN}✓ Nginx can proxy to backend${NC}"
else
    echo -e "      ${RED}✗ Nginx proxy not working${NC}"
    echo "      Response: $PROXY"
    echo ""
    echo "      This is the issue - nginx can't reach backend"
    echo "      You need to rebuild frontend with updated nginx.conf"
fi
echo ""

# Test 4: API with key
echo -e "${BLUE}[4/4]${NC} Testing authenticated endpoint..."
echo "      Enter your API key (or press Enter to skip): "
read -s API_KEY
echo ""

if [ -z "$API_KEY" ]; then
    echo -e "      ${YELLOW}⊘ Skipped (no key provided)${NC}"
else
    # Test via frontend proxy
    QUOTA=$(curl -s -H "X-API-Key: $API_KEY" http://localhost:3000/api/v1/usage/quota)

    if echo "$QUOTA" | grep -q "plan"; then
        echo -e "      ${GREEN}✓ API key works!${NC}"
        echo "      Your plan: $(echo $QUOTA | grep -o '"plan":"[^"]*"' | cut -d'"' -f4)"
        echo ""
        echo -e "      ${GREEN}✅ Everything is working correctly!${NC}"
    elif echo "$QUOTA" | grep -q "401"; then
        echo -e "      ${RED}✗ Invalid API key${NC}"
        echo "      Generate a new one: ./generate-new-key.sh"
    elif echo "$QUOTA" | grep -q "404"; then
        echo -e "      ${RED}✗ API endpoint not found (404)${NC}"
        echo "      Nginx is not proxying correctly"
        echo "      Run: ./FINAL-FIX.sh to rebuild frontend"
    else
        echo -e "      ${YELLOW}⚠ Unexpected response${NC}"
        echo "      Response: $QUOTA"
    fi
fi
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${YELLOW}📝 Summary:${NC}"
echo ""
echo "Available endpoints:"
echo "  • http://localhost:8000/health        (backend health, no auth)"
echo "  • http://localhost:8000/docs          (API documentation)"
echo "  • http://localhost:3000/              (frontend app)"
echo "  • http://localhost:3000/api/v1/*      (API via nginx proxy)"
echo ""
echo "To test with curl:"
echo "  curl -H 'X-API-Key: YOUR_KEY' http://localhost:3000/api/v1/usage/quota"
echo ""
echo "Generate new API key:"
echo "  ./generate-new-key.sh"
echo ""
