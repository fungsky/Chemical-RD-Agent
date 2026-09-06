@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

echo ============================================================
echo    ChemAgent - Docker 镜像加速配置
echo ============================================================
echo.
echo 此脚本将为 Docker Desktop 配置国内镜像加速源。
echo 配置后需要重启 Docker Desktop 生效。
echo.

:: Docker Desktop daemon.json 路径
set DOCKER_CONFIG_DIR=%USERPROFILE%\.docker
set DAEMON_JSON=%DOCKER_CONFIG_DIR%\daemon.json

:: 确保目录存在
if not exist "%DOCKER_CONFIG_DIR%" mkdir "%DOCKER_CONFIG_DIR%"

:: 备份旧配置
if exist "%DAEMON_JSON%" (
    echo [信息] 备份原配置到 daemon.json.bak ...
    copy /y "%DAEMON_JSON%" "%DAEMON_JSON%.bak" >nul
)

:: 写入新的 daemon.json
echo [信息] 写入镜像加速配置...
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

echo.
echo [完成] 镜像加速已配置，写入: %DAEMON_JSON%
echo.
echo    配置的镜像源:
echo      1. DaoCloud   (docker.m.daocloud.io)
echo      2. 腾讯云     (mirror.ccs.tencentyun.com)
echo      3. 网易       (hub-mirror.c.163.com)
echo      4. 南京大学   (docker.nju.edu.cn)
echo.
echo ============================================================
echo    请手动重启 Docker Desktop 使配置生效!
echo.
echo    方法: 右键系统托盘 Docker 图标 ^> Restart
echo    或者: 关闭 Docker Desktop 后重新打开
echo ============================================================
echo.
pause
