@echo off
chcp 65001 >nul 2>&1
echo ============================================
echo   ChemAgent - 修复并重新部署
echo ============================================
echo.

echo [1/6] 停止所有旧容器...
cd /d e:\QuestWork\chem-ai-agent
docker compose down
echo     已停止
echo.

echo [2/6] 清理旧镜像缓存（确保使用最新代码）...
docker rmi chemagent-api chemagent-ui chem-ai-agent-api chem-ai-agent-ui chem-ai-agent-init-data 2>nul
echo     已清理
echo.

echo [3/6] 重新构建并启动所有服务...
echo     启动顺序: Neo4j -> API -> UI
echo     首次构建可能需要几分钟，请耐心等待...
docker compose up -d --build
echo.

echo [4/6] 等待 Neo4j 就绪（最多 120 秒）...
set /a counter=0
:wait_neo4j
set /a counter+=5
if %counter% gtr 120 (
    echo     Neo4j 超时，请检查日志: docker logs chemagent-neo4j
    goto check_status
)
curl -s -o nul http://localhost:7474 2>nul
if errorlevel 1 (
    echo     等待中... %counter%s
    timeout /t 5 /nobreak >nul
    goto wait_neo4j
)
echo     Neo4j 已就绪!
echo.

echo [5/6] 等待 API 就绪（最多 90 秒）...
set /a counter=0
:wait_api
set /a counter+=5
if %counter% gtr 90 (
    echo     API 超时，查看日志:
    docker logs --tail 20 chemagent-api
    goto check_status
)
curl -s -o nul http://localhost:8000/health 2>nul
if errorlevel 1 (
    echo     等待中... %counter%s
    timeout /t 5 /nobreak >nul
    goto wait_api
)
echo     API 已就绪!
echo.

:check_status
echo [6/6] 检查所有服务状态...
echo.
echo --- 容器状态 ---
docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo.
echo --- API 健康检查 ---
curl -s http://localhost:8000/health 2>nul || echo API 不可用
echo.
echo.

echo ============================================
echo   部署完成!
echo   - Neo4j 管理界面: http://localhost:7474
echo   - API 文档:       http://localhost:8000/docs
echo   - Streamlit UI:   http://localhost:8501
echo ============================================
echo.
echo 如果仍有问题，请运行以下命令查看日志:
echo   docker logs chemagent-neo4j --tail 50
echo   docker logs chemagent-api --tail 50
echo   docker logs chemagent-ui --tail 50
echo.
pause
