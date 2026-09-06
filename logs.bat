@echo off
chcp 65001 >nul 2>&1
echo ============================================================
echo    ChemAgent - 查看服务状态和日志
echo ============================================================
echo.
cd /d "%~dp0"

echo --- 服务状态 ---
docker compose ps
echo.

echo --- 最近日志 (按 Ctrl+C 退出) ---
docker compose logs -f --tail=50
