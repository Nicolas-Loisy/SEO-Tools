@echo off
echo.
echo ================================================================
echo              Generate New API Key
echo ================================================================
echo.

REM Check if backend is running
docker compose ps | findstr "seo-saas-backend" | findstr "Up" > nul
if errorlevel 1 (
    echo [ERROR] Backend is not running!
    echo.
    echo Start it with:
    echo   docker compose up -d backend
    echo.
    pause
    exit /b 1
)

echo This will generate a NEW API key for your tenant.
echo.
pause
echo.

REM Run the generation script
docker compose exec backend python scripts/generate_key.py

echo.
echo [OK] Done!
echo.
echo Remember to:
echo    1. Copy the API key shown above
echo    2. Use it in the frontend login page
echo    3. Clear browser cache (Ctrl+Shift+R)
echo.
pause
