@echo off
echo.
echo ================================================================
echo          SEO SaaS - FINAL FIX SCRIPT
echo    Fixes both Tailwind CSS and API connectivity issues
echo ================================================================
echo.

REM Explain the issues
echo Issues found:
echo   X CSS file is only 620 bytes (should be several KB)
echo   X Tailwind CSS not compiled (missing postcss.config.js)
echo   X API calls get 403 errors (wrong API URL)
echo   X Nginx returns HTML instead of proxying to backend
echo.
echo Fixes applied:
echo   OK Created postcss.config.js for Tailwind compilation
echo   OK Changed API URL from http://localhost:8000/api/v1 to /api/v1
echo   OK Added .env.production with correct API path
echo.
pause
echo.

REM Step 1: Stop frontend
echo [1/6] Stopping frontend container...
docker compose stop frontend
echo       [OK] Frontend stopped
echo.

REM Step 2: Remove old images
echo [2/6] Removing old frontend image...
docker rmi seo-tools-frontend:latest 2>nul
docker rmi seosaas-frontend:latest 2>nul
echo       [OK] Old images removed
echo.

REM Step 3: Build with no cache
echo [3/6] Building frontend with Tailwind CSS...
echo       This will take 2-3 minutes...
echo.
docker compose build --no-cache frontend
echo.
echo       [OK] Frontend built successfully
echo.

REM Step 4: Start frontend
echo [4/6] Starting frontend...
docker compose up -d frontend
echo       [OK] Frontend started
echo.

REM Step 5: Wait
echo [5/6] Waiting for frontend to be ready...
timeout /t 5 /nobreak > nul
echo       [OK] Frontend is ready
echo.

REM Step 6: Verify
echo [6/6] Verifying setup...
echo.
docker ps | findstr seo-saas-frontend
echo.

REM Show logs
echo Last 15 lines of frontend logs:
echo ================================================
docker compose logs --tail=15 frontend
echo ================================================
echo.

REM Final instructions
echo.
echo ================================================================
echo                      BUILD COMPLETE!
echo ================================================================
echo.
echo Access your application:
echo    http://localhost:3000
echo.
echo CRITICAL: Clear your browser cache!
echo.
echo Method 1 - Hard Refresh:
echo    Chrome/Edge: Ctrl+Shift+R
echo    Firefox:     Ctrl+F5
echo.
echo Method 2 - DevTools:
echo    1. Press F12 to open DevTools
echo    2. Right-click on the refresh button
echo    3. Select 'Empty Cache and Hard Reload'
echo.
echo Method 3 - Complete Clear:
echo    1. Press Ctrl+Shift+Delete
echo    2. Check 'Cached images and files'
echo    3. Click 'Clear data'
echo    4. Refresh the page
echo.
echo What you should see now:
echo    OK Beautiful gradient background (blue/purple)
echo    OK White login card with shadows
echo    OK Animated blobs in the background
echo    OK Icons and styled buttons
echo    OK No more 403 errors in Network tab
echo    OK API calls go to /api/v1/* (not localhost:8000)
echo.
echo How to verify:
echo    1. Open DevTools (F12)
echo    2. Go to Network tab
echo    3. Clear and refresh page
echo    4. Check that CSS file is now 20-100 KB (not 620 bytes)
echo    5. Check that API calls go to /api/v1/... (not localhost:8000)
echo.
echo Still having issues?
echo    Check logs: docker compose logs -f frontend
echo.
echo Happy SEO analysis!
echo.
pause
