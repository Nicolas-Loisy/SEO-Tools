#!/bin/bash

echo ""
echo "╔══════════════════════════════════════════════════════════╗"
echo "║         🔑 Generate New API Key                          ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# Check if backend is running
if ! docker compose ps | grep -q "seo-saas-backend.*Up"; then
    echo "❌ Backend is not running!"
    echo ""
    echo "Start it with:"
    echo "  docker compose up -d backend"
    echo ""
    exit 1
fi

echo "This will generate a NEW API key for your tenant."
echo ""
read -p "Press Enter to continue..."
echo ""

# Run the generation script
docker compose exec backend python scripts/generate_key.py

echo ""
echo "✅ Done!"
echo ""
echo "⚠️  Remember to:"
echo "   1. Copy the API key shown above"
echo "   2. Use it in the frontend login page"
echo "   3. Clear browser cache (Ctrl+Shift+R)"
echo ""
