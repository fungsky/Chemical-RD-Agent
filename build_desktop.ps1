# ============================================================
#  ChemAgent Desktop - 打包为 Windows 绿色版文件夹
#  用法: .\build_desktop.ps1
#        .\build_desktop.ps1 -Clean      # 清理旧构建
#        .\build_desktop.ps1 -Zip        # 打包后生成 ZIP
#  产出: dist\ChemAgent\  （复制到任意 Win10/11 机器双击即可运行）
# ============================================================

param(
    [switch]$Clean,       # 清理旧构建
    [switch]$Zip,         # 打包后压缩为 ChemAgent-Win11.zip
    [switch]$Console      # 显示控制台窗口(调试)
)

$ErrorActionPreference = "Stop"
$PROJECT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $PROJECT_DIR

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  ChemAgent Desktop - 绿色版打包工具" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# ============ Step 1: 检查环境 ============
Write-Host "[1/5] 检查环境..." -ForegroundColor Green

if (-not (Test-Path ".venv")) {
    Write-Host "  创建虚拟环境..." -ForegroundColor Yellow
    python -m venv .venv
}
. .\.venv\Scripts\Activate.ps1

Write-Host "  安装打包依赖..." -ForegroundColor Yellow
pip install -q pyinstaller pillow

# ============ Step 2: 图标 ============
Write-Host "[2/5] 生成图标..." -ForegroundColor Green

if (-not (Test-Path "assets")) {
    New-Item -ItemType Directory -Path "assets" | Out-Null
}

if (-not (Test-Path "assets\chemagent.ico")) {
    python -c "
from PIL import Image, ImageDraw

sizes = [256, 128, 64, 48, 32, 16]
images = []
for s in sizes:
    img = Image.new('RGBA', (s, s), (26, 115, 232, 255))
    draw = ImageDraw.Draw(img)
    margin = s // 8
    draw.rectangle([margin, margin, s - margin, s - margin], fill='white')
    draw.rectangle([margin*2, margin*3, s//3, s-margin*3], fill=(26, 115, 232, 255))
    draw.rectangle([s//2, margin*3, s-margin*2, s-margin*3], fill=(26, 115, 232, 255))
    images.append(img)

images[0].save('assets/chemagent.ico', format='ICO', sizes=[(s, s) for s in sizes], append_images=images[1:])
print('  assets/chemagent.ico generated')
" 2>&1
}

# ============ Step 3: 清理 ============
if ($Clean) {
    Write-Host "[3/5] 清理旧构建..." -ForegroundColor Green
    Remove-Item -Recurse -Force build, dist, *.spec -ErrorAction SilentlyContinue
}

# ============ Step 4: PyInstaller 打包(目录模式) ============
Write-Host "[4/5] PyInstaller 打包..." -ForegroundColor Green

$consoleBool = if ($Console) { "True" } else { "False" }

$specContent = @"
# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['desktop_app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('data', 'data'),
        ('.env.example', '.env.example'),
        ('assets/chemagent.ico', 'assets'),
    ],
    hiddenimports=[
        # uvicorn 动态导入的循环/协议实现
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.loops.asyncio',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.http.h11_impl',
        'uvicorn.protocols.http.httptools_impl',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.protocols.websockets.wsproto_impl',
        'uvicorn.protocols.websockets.websockets_impl',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        # 内置示例数据模块（函数内动态导入）
        'data.sample_data',
        'data.formulas_data',
        'data.init_data',
        'data.materials_data',
        # 常用依赖
        'pydantic',
        'pydantic_settings',
        'chromadb',
        'neo4j',
        'passlib',
        'bcrypt',
        'jose',
        'requests',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'streamlit', 'plotly', 'IPython', 'jupyter', 'matplotlib',
        'tkinter', 'pytest', 'PyQt5', 'PySide6',
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ChemAgent',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=$consoleBool,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/chemagent.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ChemAgent',
)
"@

$specContent | Set-Content -Path "chemagent.spec" -Encoding UTF8

pyinstaller chemagent.spec --clean --noconfirm 2>&1

# ============ Step 5: 完成 ============
Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "  打包完成！" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green

$distDir = Join-Path $PROJECT_DIR "dist\ChemAgent"
if (Test-Path (Join-Path $distDir "ChemAgent.exe")) {
    $sizeMB = [math]::Round((Get-ChildItem $distDir -Recurse -File | Measure-Object Length -Sum).Sum / 1MB, 1)
    Write-Host "  绿色版目录: $distDir" -ForegroundColor White
    Write-Host "  体积: $sizeMB MB" -ForegroundColor White
    Write-Host ""
    Write-Host "  使用: 整个目录复制到 Windows 10/11 电脑，双击 ChemAgent.exe" -ForegroundColor Yellow
    Write-Host "  数据保存在 %LOCALAPPDATA%\ChemAgent" -ForegroundColor Yellow
    Write-Host ""

    if ($Zip) {
        Write-Host "  压缩 ZIP..." -ForegroundColor Green
        $zipPath = Join-Path $PROJECT_DIR "dist\ChemAgent-Win11.zip"
        Remove-Item $zipPath -Force -ErrorAction SilentlyContinue
        Compress-Archive -Path (Join-Path $distDir "*") -DestinationPath $zipPath -CompressionLevel Optimal
        $zipMB = [math]::Round((Get-Item $zipPath).Length / 1MB, 1)
        Write-Host "  ZIP: $zipPath ($zipMB MB)" -ForegroundColor White
    }
} else {
    Write-Host "  打包可能失败，请检查上方输出" -ForegroundColor Red
}
