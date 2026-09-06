@echo off
chcp 65001 >nul 2>&1
echo ============================================
echo   ChemAgent 服务诊断工具
echo ============================================
echo.

echo [1/5] 检查 Docker 服务状态...
docker ps -a --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo.

echo [2/5] 检查 Neo4j 容器日志（最近 30 行）...
echo --- Neo4j Logs ---
docker logs --tail 30 chemagent-neo4j 2>&1
echo.

echo [3/5] 检查 API 容器日志（最近 30 行）...
echo --- API Logs ---
docker logs --tail 30 chemagent-api 2>&1
echo.

echo [4/5] 检查 UI 容器日志（最近 15 行）...
echo --- UI Logs ---
docker logs --tail 15 chemagent-ui 2>&1
echo.

echo [5/5] 测试 API 端口连通性...
curl -s -o nul -w "API Health Check HTTP Status: %%{http_code}" http://localhost:8000/health 2>&1 || echo API 端口 8000 无法连通
echo.
echo.

echo ============================================
echo   诊断完成，请将以上输出反馈给我
echo ============================================
pause
