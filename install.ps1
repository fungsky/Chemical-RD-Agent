# ============================================================
#  ChemAgent - Windows 原生一键安装 & 启动脚本
#  用法: .\install.ps1
#        .\install.ps1 -SkipDocker    (跳过 Docker，本地模式)
#        .\install.ps1 -InstallOnly   (仅安装，不启动)
# ============================================================

param(
    [switch]$Desktop,     # 桌面应用模式
    [switch]$Build,       # 打包为 EXE（需 -Desktop）

    [switch]$SkipDocker,    # 跳过 Docker，使用本地 Neo4j
    [switch]$InstallOnly,   # 仅安装依赖，不启动服务
    [switch]$Force          # 跳过确认提示
)

$ErrorActionPreference = "Stop"
$Host.UI.RawUI.WindowTitle = "ChemAgent Installer"

# ============ 配色 ============
function Write-Info  { Write-Host "[INFO]  $args" -ForegroundColor Green }
function Write-Warn  { Write-Host "[WARN]  $args" -ForegroundColor Yellow }
function Write-ErrorMsg { Write-Host "[ERROR] $args" -ForegroundColor Red }
function Write-Step  { Write-Host "`n============================================================" -ForegroundColor Cyan; Write-Host "  $args" -ForegroundColor Cyan; Write-Host "============================================================" -ForegroundColor Cyan }

# ============ Banner ============
Clear-Host
Write-Host @"

   ____ _                       _                _
  / ___| |__   ___ _ __ ___    / \   __ _  ___ _(_)_ __   __ _
 | |   | '_ \ / _ \ '_ ` _ \  / _ \ / _` |/ _ \ / | '_ \ / _` |
 | |___| | | |  __/ | | | | |/ ___ \ (_| |  __/ /| | | | | (_| |
  \____|_| |_|\___|_| |_| |_/_/   \_\__,_|\___|_/|_|_| |_|\__,_|

        化工研发智能体 - Windows 原生一键安装器
"@ -ForegroundColor Cyan

Write-Host ""
Write-Info "此脚本将自动检测环境、安装缺失组件、配置 LLM、启动服务"
Write-Info "支持本地模式和 Docker 模式"
Write-Host ""

if (-not $Force) {
    $confirm = Read-Host "按 Enter 继续，或输入 q 退出"
    if ($confirm -eq "q") { exit 0 }
}

# ============ Step 1: 环境检测 ============
Write-Step "Step 1/6: 环境检测"

$NEED_RESTART = $false

# --- Python ---
Write-Info "检测 Python..."
$pythonPath = $null
try {
    $pythonPath = (Get-Command python -ErrorAction Stop).Source
    $pythonVer = & python --version 2>&1
    Write-Info "  Python: $pythonVer  ($pythonPath)"
} catch {
    try {
        $pythonPath = (Get-Command python3 -ErrorAction Stop).Source
        $pythonVer = & python3 --version 2>&1
        Write-Info "  Python: $pythonVer  ($pythonPath)"
    } catch {
        Write-Warn "  Python 未安装"
    }
}

# --- Docker ---
$hasDocker = $false
if (-not $SkipDocker) {
    Write-Info "检测 Docker..."
    try {
        $dockerVer = & docker --version 2>&1
        Write-Info "  Docker: $dockerVer"
        $hasDocker = $true
    } catch {
        Write-Warn "  Docker 未安装"
    }
}

# --- Git ---
Write-Info "检测 Git..."
try {
    $gitVer = & git --version 2>&1
    Write-Info "  Git: $gitVer"
} catch {
    Write-Warn "  Git 未安装"
}

# --- winget ---
$hasWinget = $false
try {
    $wingetVer = & winget --version 2>&1
    Write-Info "  winget: $wingetVer"
    $hasWinget = $true
} catch {
    Write-Warn "  winget 不可用，将尝试其他安装方式"
}

# ============ Step 2: 安装缺失组件 ============
Write-Step "Step 2/6: 安装缺失组件"

if (-not $pythonPath) {
    Write-Info "安装 Python 3.11..."
    if ($hasWinget) {
        winget install Python.Python.3.11 --accept-package-agreements --accept-source-agreements
        Write-Warn "  >>> 请关闭此窗口，重新打开后再次运行 .\install.ps1"
        Write-Warn "  >>> (Python 安装后需要刷新 PATH 环境变量)"
        $NEED_RESTART = $true
    } else {
        Write-ErrorMsg "请手动安装 Python 3.11+: https://www.python.org/downloads/"
        Start-Process "https://www.python.org/downloads/"
        exit 1
    }
}

if ($NEED_RESTART) { exit 0 }

# 确定 Python 命令
if ($pythonPath) {
    $PY = "python"
} else {
    $PY = "python3"
}

# --- Git ---
try { & git --version 2>&1 | Out-Null } catch {
    if ($hasWinget) {
        Write-Info "安装 Git..."
        winget install Git.Git --accept-package-agreements --accept-source-agreements
    }
}

# --- Docker ---
if (-not $SkipDocker -and -not $hasDocker) {
    Write-Info "安装 Docker Desktop..."
    if ($hasWinget) {
        winget install Docker.DockerDesktop --accept-package-agreements --accept-source-agreements
        Write-Warn "  >>> Docker Desktop 安装完成后，请手动启动它并完成首次设置"
        Write-Warn "  >>> 然后重新运行 .\install.ps1"
        exit 0
    } else {
        Write-Warn "请手动安装 Docker Desktop: https://www.docker.com/products/docker-desktop/"
        Start-Process "https://www.docker.com/products/docker-desktop/"
    }
}

# ============ Step 3: Python 虚拟环境 & 依赖 ============
Write-Step "Step 3/6: 安装 Python 依赖"

$PROJECT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $PROJECT_DIR

if (-not (Test-Path ".venv")) {
    Write-Info "创建虚拟环境..."
    & $PY -m venv .venv
}
Write-Info "激活虚拟环境..."
. .\.venv\Scripts\Activate.ps1

Write-Info "安装依赖包（可能需要几分钟）..."
& $PY -m pip install --upgrade pip -q
& $PY -m pip install -r requirements.txt -q
Write-Info "  Python 依赖安装完成"

# ============ Step 4: 环境配置 ============
Write-Step "Step 4/6: 配置环境变量"

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Info "已从 .env.example 创建 .env"
} else {
    Write-Info ".env 已存在，跳过"
}

# ============ Step 5: LLM 接入配置 ============
Write-Step "Step 5/6: 大模型接入配置"

Write-Host ""
Write-Host "  ChemAgent 支持 12+ 大模型服务商。请选择：" -ForegroundColor White
Write-Host ""
Write-Host "  1. Ollama (本地部署，免费，推荐)    7. 通义千问 / Qwen"
Write-Host "  2. OpenAI (GPT-4o/4/3.5)           8. 月之暗面 / Kimi"
Write-Host "  3. DeepSeek                         9. 零一万物 / Yi"
Write-Host "  4. 智谱 AI / GLM                    10. Google Gemini"
Write-Host "  5. Azure OpenAI                     11. Anthropic Claude"
Write-Host "  6. LM Studio (本地)                 12. 自定义 OpenAI 兼容"
Write-Host "  0. 跳过，稍后在管理后台配置"
Write-Host ""

$providerMap = @{
    "1" = @{provider="ollama";      base="http://localhost:11434/v1"; model="qwen2.5:7b"}
    "2" = @{provider="openai";      base="https://api.openai.com/v1";  model="gpt-4o-mini"}
    "3" = @{provider="deepseek";    base="https://api.deepseek.com/v1"; model="deepseek-chat"}
    "4" = @{provider="zhipu";       base="https://open.bigmodel.cn/api/paas/v4"; model="glm-4-flash"}
    "5" = @{provider="azure_openai";base=""; model=""}
    "6" = @{provider="lm_studio";   base="http://localhost:1234/v1"; model="local-model"}
    "7" = @{provider="qwen";        base="https://dashscope.aliyuncs.com/compatible-mode/v1"; model="qwen-plus"}
    "8" = @{provider="moonshot";    base="https://api.moonshot.cn/v1"; model="moonshot-v1-8k"}
    "9" = @{provider="yi";          base="https://api.lingyiwanwu.com/v1"; model="yi-large"}
    "10"= @{provider="gemini";      base="https://generativelanguage.googleapis.com/v1beta"; model="gemini-1.5-flash"}
    "11"= @{provider="anthropic";   base="https://api.anthropic.com/v1"; model="claude-3-haiku-20240307"}
    "12"= @{provider="custom_openai";base=""; model=""}
}

$choice = Read-Host "请输入编号 (0-12)"
if ($choice -ne "0" -and $providerMap.ContainsKey($choice)) {
    $p = $providerMap[$choice]
    $apiKey = Read-Host "API Key（本地模型可跳过）"

    $envContent = Get-Content ".env" -Raw

    $envContent = $envContent -replace "CHEM_LLM_PROVIDER=.*", "CHEM_LLM_PROVIDER=$($p.provider)"
    $envContent = $envContent -replace "CHEM_LLM_BASE_URL=.*", "CHEM_LLM_BASE_URL=$($p.base)"
    $envContent = $envContent -replace "CHEM_LLM_MODEL=.*", "CHEM_LLM_MODEL=$($p.model)"
    if ($apiKey) {
        $envContent = $envContent -replace "CHEM_LLM_API_KEY=.*", "CHEM_LLM_API_KEY=$apiKey"
    }
    # Embedding 默认复用 LLM
    $envContent = $envContent -replace "CHEM_EMBEDDING_PROVIDER=.*", "CHEM_EMBEDDING_PROVIDER=same_as_llm"

    [System.IO.File]::WriteAllText("$PROJECT_DIR\.env", $envContent)
    Write-Info "  已配置 LLM: $($p.provider) / $($p.model)"
} elseif ($choice -eq "0") {
    Write-Info "  跳过 LLM 配置，稍后可在管理后台 UI 中设置"
} else {
    Write-Warn "  无效选择，跳过"
}

# ============ Step 6: 启动服务 ============
if (-not $InstallOnly) {
    Write-Step "Step 6/6: 启动 ChemAgent"

    if ($SkipDocker) {
        Write-Info "本地开发模式启动..."
        Write-Info "启动 API 服务 (端口 8000)..."
        Start-Process -NoNewWindow -FilePath $PY -ArgumentList "-m", "uvicorn", "chem_agent.api.main:app", "--host", "0.0.0.0", "--port", "8000"

        Write-Info "启动 Streamlit UI (端口 8501)..."
        Start-Process -NoNewWindow -FilePath $PY -ArgumentList "-m", "streamlit", "run", "chem_agent/ui/app.py", "--server.port", "8501", "--server.address", "0.0.0.0"
    } else {
        Write-Info "Docker Compose 模式启动..."
        if ($hasDocker) {
            docker compose up -d
            Write-Info "等待服务就绪..."
            Start-Sleep 8
            docker compose ps
        } else {
            Write-Warn "Docker 不可用，切换到本地模式..."
            Write-Warn "请先安装 Docker 或使用 -SkipDocker 参数"
        }
    }

    # 打开浏览器
    Start-Sleep 2
    Write-Info "打开浏览器..."
    Start-Process "http://localhost:8501"
}


# ============ 桌面模式：打包 + 启动原生窗口 ============
if ($Desktop) {
    Write-Step "桌面模式：安装桌面依赖"

    Write-Info "安装桌面组件..."
    & $PY -m pip install -q PyQt6 Pillow pyinstaller

    if ($Build) {
        Write-Step "打包为 EXE"
        Write-Info "正在打包（首次需要 3-5 分钟）..."
        & $PY -m PyInstaller chemagent.spec --clean --noconfirm 2>&1 | Select-Object -Last 5
        $exe = Join-Path $PROJECT_DIR "dist\ChemAgent\ChemAgent.exe"
        if (Test-Path $exe) {
            Write-Info "打包完成: $exe"
            Write-Info "启动桌面应用..."
            Start-Process $exe
        } else {
            Write-Warn "打包可能失败，尝试直接启动桌面模式..."
            & $PY desktop_app.py
        }
    } else {
        Write-Info "直接启动桌面模式..."
        & $PY desktop_app.py
    }
    return
}

# ============ 完成 ============
Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "   ChemAgent 安装完成！" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "  前端 UI:   http://localhost:8501" -ForegroundColor White
Write-Host "  API 文档:  http://localhost:8000/docs" -ForegroundColor White
Write-Host "  Neo4j:     http://localhost:7474" -ForegroundColor White
Write-Host ""
Write-Host "  默认账户:  admin / admin123" -ForegroundColor Yellow
Write-Host "  首次登录后请在管理后台修改密码" -ForegroundColor Yellow
Write-Host ""
Write-Host "  常用命令:" -ForegroundColor White
Write-Host "    查看日志:  .\logs.bat                docker compose logs -f" -ForegroundColor Gray
Write-Host "    停止服务:  .\stop.bat                docker compose down" -ForegroundColor Gray
Write-Host "    重新安装:  .\install.ps1" -ForegroundColor Gray