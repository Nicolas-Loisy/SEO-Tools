@echo off
echo.
echo SEO SaaS - Complete Setup and Fix Script
echo ==========================================
echo.

REM Step 1: Stop everything
echo [Step 1] Stopping all containers...
docker compose down
echo [OK] Containers stopped
echo.

REM Step 2: Start database
echo [Step 2] Starting database...
docker compose up -d postgres redis
echo Waiting for PostgreSQL to be ready...
timeout /t 5 /nobreak > nul
echo [OK] Database started
echo.

REM Step 3: Run migrations
echo [Step 3] Running database migrations...
docker compose run --rm backend alembic upgrade head
echo [OK] Migrations completed
echo.

REM Step 4: Bootstrap
echo [Step 4] Creating tenant and API key...
echo.
echo ================================================
docker compose run --rm backend python scripts/bootstrap.py
echo ================================================
echo.
echo IMPORTANT: Copy the API key above! You'll need it to login.
echo.
pause
echo.

REM Step 5: Rebuild frontend
echo [Step 5] Rebuilding frontend (this may take 2-3 minutes)...
docker compose build --no-cache frontend
echo [OK] Frontend rebuilt
echo.

REM Step 6: Start all services
echo [Step 6] Starting all services...
docker compose up -d
echo [OK] All services started
echo.

REM Step 7: Show status
echo [Step 7] Checking service status...
timeout /t 3 /nobreak > nul
docker compose ps
echo.

REM Final instructions
echo.
echo ==========================================
echo SETUP COMPLETE!
echo ==========================================
echo.
echo Access your application:
echo    Frontend: http://localhost
echo    Backend:  http://localhost:8000
echo    API Docs: http://localhost:8000/docs
echo.
echo Next steps:
echo    1. Open http://localhost in your browser
echo    2. Clear browser cache (Ctrl+Shift+R)
echo    3. Enter the API key you copied earlier
echo    4. You should see the styled login page!
echo.
echo Troubleshooting:
echo    - If styles don't appear: Clear browser cache completely
echo    - If API key doesn't work: Check the key you copied
echo    - Check logs: docker compose logs -f frontend
echo    - Check logs: docker compose logs -f backend
echo.
echo Happy SEO analysis!
echo.
pause
