#!/bin/bash

echo "🛑 Stopping all containers..."
docker compose down

echo "🗑️  Removing old frontend images..."
docker rmi seosaas-frontend:latest 2>/dev/null || true
docker rmi seo-tools-frontend:latest 2>/dev/null || true

echo "🔨 Building frontend without cache..."
docker compose build --no-cache frontend

echo "🚀 Starting all services..."
docker compose up -d

echo ""
echo "✅ Done! Wait 10-20 seconds for all services to start."
echo ""
echo "📱 Access your application at:"
echo "   Frontend: http://localhost"
echo "   Backend:  http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
echo ""
echo "💡 Don't forget to clear your browser cache (Ctrl+Shift+R or Cmd+Shift+R)"
