@echo off
chcp 65001 >nul 2>&1

echo === Step 1: Configure Docker mirrors ===
if not exist "%USERPROFILE%\.docker" mkdir "%USERPROFILE%\.docker"
set DAEMON_JSON=%USERPROFILE%\.docker\daemon.json

findstr /i "registry-mirrors" "%DAEMON_JSON%" >nul 2>&1
if %errorlevel% neq 0 (
    echo Writing daemon.json with mirror config...
    (
    echo {
    echo   "registry-mirrors": [
    echo     "https://docker.m.daocloud.io",
    echo     "https://mirror.ccs.tencentyun.com",
    echo     "https://hub-mirror.c.163.com",
    echo     "https://docker.nju.edu.cn"
    echo   ]
    echo }
    ) > "%DAEMON_JSON%"
    echo Mirrors configured. Restarting Docker Desktop...
    taskkill /f /im "Docker Desktop.exe" >nul 2>&1
    timeout /t 5 /nobreak >nul
    start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    echo Waiting for Docker to restart...
    :wait_loop
    timeout /t 5 /nobreak >nul
    docker info >nul 2>&1
    if %errorlevel% neq 0 goto wait_loop
    echo Docker restarted OK.
) else (
    echo Mirrors already configured.
)

echo.
echo === Step 2: Build Docker images ===
cd /d "e:\QuestWork\chem-ai-agent"
docker compose build
if %errorlevel% neq 0 (
    echo BUILD FAILED
    exit /b 1
)

echo.
echo === Step 3: Start services ===
docker compose up -d
if %errorlevel% neq 0 (
    echo START FAILED
    exit /b 1
)

echo Waiting for services to be ready...
timeout /t 20 /nobreak >nul

echo.
echo === Step 4: Init sample data ===
docker compose --profile init run --rm init-data

echo.
echo === Step 5: Verify ===
docker compose ps
echo.
curl -s http://localhost:8000/health
echo.
echo === DONE ===
