@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

echo ============================================================
echo    ChemAgent 化工研发智能体 - 一键部署脚本
echo ============================================================
echo.

:: ============ 检查 winget 是否可用 ============
set WINGET_OK=0
where winget >nul 2>&1
if %errorlevel% equ 0 set WINGET_OK=1

:: ============ 第一步: 检查并安装 Docker Desktop ============
echo [1/7] 检查 Docker Desktop...

where docker >nul 2>&1
if %errorlevel% neq 0 (
    echo        未找到 Docker Desktop，正在自动安装...
    if !WINGET_OK! equ 1 (
        winget install -e --id Docker.DockerDesktop --accept-source-agreements --accept-package-agreements
        if !errorlevel! neq 0 (
            echo [错误] Docker Desktop 自动安装失败
            echo        请手动下载安装: https://www.docker.com/products/docker-desktop/
            pause
            exit /b 1
        )
        echo.
        echo        Docker Desktop 已安装，需要重启电脑后再运行此脚本。
        echo        请重启电脑，确保 Docker Desktop 启动后，重新运行 deploy.bat
        pause
        exit /b 0
    ) else (
        echo [错误] 未找到 winget 包管理器，无法自动安装
        echo        请手动下载安装 Docker Desktop:
        echo        https://www.docker.com/products/docker-desktop/
        pause
        exit /b 1
    )
)
echo        Docker .................. OK

:: 检查 Docker 是否正在运行
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo        Docker 未运行，正在尝试启动 Docker Desktop...
    start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe" 2>nul
    if !errorlevel! neq 0 (
        start "" "%LOCALAPPDATA%\Docker\Docker Desktop.exe" 2>nul
    )

    echo        等待 Docker 启动就绪（最多 120 秒）...
    set WAIT_COUNT=0
    :wait_docker_start
    if !WAIT_COUNT! geq 24 (
        echo [错误] Docker 启动超时，请手动启动 Docker Desktop 后重新运行此脚本
        pause
        exit /b 1
    )
    timeout /t 5 /nobreak >nul
    docker info >nul 2>&1
    if !errorlevel! neq 0 (
        set /a WAIT_COUNT+=1
        echo        等待中... ^(!WAIT_COUNT!/24^)
        goto wait_docker_start
    )
    echo        Docker 已启动 ........... OK
)

docker compose version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到 docker compose，请更新 Docker Desktop 到最新版本
    pause
    exit /b 1
)
echo        Docker Compose ......... OK
echo.

:: ============ 第二步: 检查 Docker 镜像加速 ============
echo [2/7] 检查 Docker 镜像加速配置...

set DAEMON_JSON=%USERPROFILE%\.docker\daemon.json
set NEED_MIRROR=0

if not exist "%DAEMON_JSON%" (
    set NEED_MIRROR=1
) else (
    findstr /i "registry-mirrors" "%DAEMON_JSON%" >nul 2>&1
    if !errorlevel! neq 0 set NEED_MIRROR=1
)

if !NEED_MIRROR! equ 1 (
    echo [信息] 未检测到镜像加速配置，正在自动配置国内镜像源...

    if not exist "%USERPROFILE%\.docker" mkdir "%USERPROFILE%\.docker"
    if exist "%DAEMON_JSON%" copy /y "%DAEMON_JSON%" "%DAEMON_JSON%.bak" >nul

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

    echo        镜像加速已配置，正在重启 Docker...
    echo.
    echo        *** 请等待 Docker Desktop 完全重启 ***
    echo.

    taskkill /f /im "Docker Desktop.exe" >nul 2>&1
    timeout /t 5 /nobreak >nul
    start "" "C:\Program Files\Docker\Docker\Docker Desktop.exe" 2>nul
    if !errorlevel! neq 0 (
        start "" "%LOCALAPPDATA%\Docker\Docker Desktop.exe" 2>nul
    )

    echo        等待 Docker 重启就绪（最多等待 60 秒）...
    set WAIT_COUNT=0
    :wait_docker
    if !WAIT_COUNT! geq 12 (
        echo [错误] Docker 重启超时，请手动重启 Docker Desktop 后再运行此脚本
        pause
        exit /b 1
    )
    timeout /t 5 /nobreak >nul
    docker info >nul 2>&1
    if !errorlevel! neq 0 (
        set /a WAIT_COUNT+=1
        echo        等待中... ^(!WAIT_COUNT!/12^)
        goto wait_docker
    )
    echo        Docker 重启完成 ........ OK
) else (
    echo        镜像加速 ............... 已配置
)

echo.

:: ============ 第三步: 检查并安装 Ollama ============
echo [3/7] 检查 Ollama 本地大模型服务...

where ollama >nul 2>&1
if %errorlevel% neq 0 (
    echo        未找到 Ollama，正在自动安装...
    if !WINGET_OK! equ 1 (
        winget install -e --id Ollama.Ollama --accept-source-agreements --accept-package-agreements
        if !errorlevel! neq 0 (
            echo [错误] Ollama 自动安装失败
            echo        请手动下载安装: https://ollama.com/download
            pause
            exit /b 1
        )
        echo        Ollama 安装完成，刷新环境变量...
        :: 刷新 PATH（winget 安装后 PATH 可能需要刷新）
        set "PATH=%LOCALAPPDATA%\Programs\Ollama;%PATH%"
        where ollama >nul 2>&1
        if !errorlevel! neq 0 (
            echo.
            echo        Ollama 已安装，但需要重新打开命令行窗口使环境变量生效。
            echo        请关闭此窗口，重新运行 deploy.bat
            pause
            exit /b 0
        )
    ) else (
        echo [错误] 未找到 winget 包管理器，无法自动安装
        echo        请手动下载安装 Ollama: https://ollama.com/download
        pause
        exit /b 1
    )
)
echo        Ollama ................. OK

:: ============ 第四步: 确保 Ollama 服务运行 ============
echo [4/7] 确保 Ollama 服务运行中...

:: 检查 Ollama 是否在运行
ollama list >nul 2>&1
if %errorlevel% neq 0 (
    echo        Ollama 服务未运行，正在启动...
    start "" ollama serve
    timeout /t 3 /nobreak >nul

    set OL_WAIT=0
    :wait_ollama
    if !OL_WAIT! geq 6 (
        echo [警告] Ollama 服务启动超时，模型拉取可能失败
        goto pull_models
    )
    ollama list >nul 2>&1
    if !errorlevel! neq 0 (
        set /a OL_WAIT+=1
        timeout /t 2 /nobreak >nul
        goto wait_ollama
    )
)
echo        Ollama 服务 ............ 运行中

:: ============ 第五步: 拉取 Ollama 模型 ============
:pull_models
echo [5/7] 拉取 Ollama 模型（首次需要下载，请耐心等待）...

echo        检查 qwen3:4b 模型...
ollama list 2>nul | findstr /i "qwen3:4b" >nul 2>&1
if !errorlevel! neq 0 (
    echo        正在拉取 qwen3:4b（约 2.6GB）...
    ollama pull qwen3:4b
    if !errorlevel! neq 0 (
        echo [警告] qwen3:4b 拉取失败，AI 对话功能可能受限
    ) else (
        echo        qwen3:4b .................. OK
    )
) else (
    echo        qwen3:4b .................. 已存在
)

echo        检查 nomic-embed-text 模型...
ollama list 2>nul | findstr /i "nomic-embed-text" >nul 2>&1
if !errorlevel! neq 0 (
    echo        正在拉取 nomic-embed-text（约 274MB）...
    ollama pull nomic-embed-text
    if !errorlevel! neq 0 (
        echo [警告] nomic-embed-text 拉取失败，向量检索功能可能受限
    ) else (
        echo        nomic-embed-text ...... OK
    )
) else (
    echo        nomic-embed-text ...... 已存在
)
echo.

:: ============ 第六步: 构建 Docker 镜像 ============
echo [6/7] 构建 Docker 镜像（首次构建需要几分钟）...
docker compose build --no-cache
if %errorlevel% neq 0 (
    echo.
    echo [错误] Docker 镜像构建失败
    echo        可能原因:
    echo          1. 网络问题 - 请检查是否能访问外网
    echo          2. 镜像源问题 - 请检查 Docker 镜像加速配置
    echo          3. 磁盘空间不足
    echo.
    echo        排查命令: docker compose build 2^>^&1
    pause
    exit /b 1
)
echo        镜像构建 ............... OK
echo.

:: ============ 第七步: 启动所有服务 ============
echo [7/7] 启动所有服务...
docker compose up -d
if %errorlevel% neq 0 (
    echo [错误] 服务启动失败
    pause
    exit /b 1
)

echo        等待服务就绪...
timeout /t 15 /nobreak >nul

:: 导入示例数据
echo        导入示例数据到知识图谱...
docker compose --profile init run --rm init-data
if %errorlevel% neq 0 (
    echo [警告] 示例数据导入可能失败，可稍后手动运行:
    echo        docker compose --profile init run --rm init-data
) else (
    echo        示例数据导入 ........... OK
)

echo.
echo ============================================================
echo    部署完成！
echo ============================================================
echo.
echo    前端界面:  http://localhost:8501
echo    API 文档:  http://localhost:8000/docs
echo    Neo4j:     http://localhost:7474 (neo4j/chemagent2024)
echo.
echo    默认管理员:  admin / admin123
echo.
echo    LLM 模型:   qwen3:4b
echo    向量模型:    nomic-embed-text
echo.
echo    常用命令:
echo      查看日志:    docker compose logs -f
echo      停止服务:    docker compose down
echo      重启服务:    docker compose restart
echo      查看状态:    docker compose ps
echo ============================================================
echo.
pause
