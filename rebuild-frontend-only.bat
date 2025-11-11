@echo off
echo.
echo Rebuild Frontend Only (Fix Styles)
echo ======================================
echo.

REM Step 1: Stop frontend
echo [1/5] Stopping frontend container...
docker compose stop frontend
echo [OK] Frontend stopped
echo.

REM Step 2: Remove old image
echo [2/5] Removing old frontend image...
docker rmi seo-tools-frontend:latest 2>nul
docker rmi seosaas-frontend:latest 2>nul
echo [OK] Old images removed
echo.

REM Step 3: Rebuild without cache
echo [3/5] Building frontend (no cache)...
echo This will take 2-3 minutes...
echo.
docker compose build --no-cache frontend
echo.
echo [OK] Frontend built successfully
echo.

REM Step 4: Start frontend
echo [4/5] Starting frontend...
docker compose up -d frontend
echo [OK] Frontend started
echo.

REM Step 5: Wait and check
echo [5/5] Waiting for frontend to be ready...
timeout /t 5 /nobreak > nul
echo.

REM Show logs
echo Frontend logs (last 20 lines):
echo ==================================
docker compose logs --tail=20 frontend
echo.

REM Final instructions
echo.
echo ==========================================
echo Frontend rebuild complete!
echo ==========================================
echo.
echo Open: http://localhost
echo.
echo IMPORTANT: Clear your browser cache!
echo    - Press Ctrl+Shift+R for hard refresh
echo.
echo    Or manually:
echo    1. Press F12 (open DevTools)
echo    2. Right-click on refresh button
echo    3. Select 'Empty Cache and Hard Reload'
echo.
echo You should now see the styled login page!
echo.
pause
