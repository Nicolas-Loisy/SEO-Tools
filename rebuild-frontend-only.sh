#!/bin/bash
set -e

echo "🎨 Rebuild Frontend Only (Fix Styles)"
echo "======================================"
echo ""

# Step 1: Stop frontend
echo "📦 Stopping frontend container..."
docker compose stop frontend
echo "✓ Frontend stopped"
echo ""

# Step 2: Remove old image
echo "🗑️  Removing old frontend image..."
docker rmi seo-tools-frontend:latest 2>/dev/null || true
docker rmi seosaas-frontend:latest 2>/dev/null || true
echo "✓ Old images removed"
echo ""

# Step 3: Rebuild without cache
echo "🔨 Building frontend (no cache)..."
echo "⏳ This will take 2-3 minutes..."
echo ""
docker compose build --no-cache frontend
echo ""
echo "✓ Frontend built successfully"
echo ""

# Step 4: Start frontend
echo "🚀 Starting frontend..."
docker compose up -d frontend
echo "✓ Frontend started"
echo ""

# Step 5: Wait and check
echo "⏳ Waiting for frontend to be ready..."
sleep 5
echo ""

# Show logs
echo "📋 Frontend logs (last 20 lines):"
echo "=================================="
docker compose logs --tail=20 frontend
echo ""

# Final instructions
echo ""
echo "✅ Frontend rebuild complete!"
echo ""
echo "🌐 Open: http://localhost"
echo ""
echo "🔄 IMPORTANT: Clear your browser cache!"
echo "   - Chrome/Edge: Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)"
echo "   - Firefox: Ctrl+F5 (Windows) or Cmd+Shift+R (Mac)"
echo ""
echo "   Or manually:"
echo "   1. Press F12 (open DevTools)"
echo "   2. Right-click on refresh button"
echo "   3. Select 'Empty Cache and Hard Reload'"
echo ""
echo "✨ You should now see the styled login page!"
