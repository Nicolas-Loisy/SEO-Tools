#!/bin/bash

echo "╔═══════════════════════════════════════════════════════════╗"
echo "║        Resetting Database with New Schema                 ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""
echo "⚠️  WARNING: This will delete ALL data in the database!"
echo ""
read -p "Are you sure you want to continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Aborted."
    exit 0
fi

echo ""
echo "Stopping services..."
docker compose stop backend celery-worker

echo ""
echo "Dropping existing tables..."
docker compose exec -T postgres psql -U seouser -d seosaas << 'EOF'
-- Drop all tables in cascade
DROP TABLE IF EXISTS schema_suggestions CASCADE;
DROP TABLE IF EXISTS links CASCADE;
DROP TABLE IF EXISTS pages CASCADE;
DROP TABLE IF EXISTS crawl_jobs CASCADE;
DROP TABLE IF EXISTS projects CASCADE;
DROP TABLE IF EXISTS api_keys CASCADE;
DROP TABLE IF EXISTS usage_logs CASCADE;
DROP TABLE IF EXISTS tenants CASCADE;

-- Recreate pgvector extension if needed
CREATE EXTENSION IF NOT EXISTS vector;

\echo 'Tables dropped successfully!'
EOF

echo ""
echo "Restarting backend to recreate tables..."
docker compose up -d backend

echo ""
echo "Waiting for backend to initialize (10 seconds)..."
sleep 10

echo ""
echo "Checking backend logs..."
docker compose logs backend --tail=20 | grep -E "CREATE TABLE|Starting|ready"

echo ""
echo "Restarting celery-worker..."
docker compose up -d celery-worker

echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║                Database Reset Complete!                    ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""
echo "✅ All tables have been recreated with the new schema"
echo "✅ You can now create a new tenant and start crawling"
echo ""
echo "Note: You'll need to register a new user to get a new API key"
