@echo off
chcp 65001 >nul 2>&1
echo ============================================================
echo    ChemAgent - 停止所有服务
echo ============================================================
echo.
cd /d "%~dp0"
docker compose down
echo.
echo 所有服务已停止。
pause
