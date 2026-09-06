@echo off
chcp 65001 >nul 2>&1
setlocal

echo ============================================================
echo    ChemAgent 部署包打包工具
echo ============================================================
echo.

set "SRC=%~dp0"
:: 去掉末尾的反斜杠
if "%SRC:~-1%"=="\" set "SRC=%SRC:~0,-1%"

:: 输出到上级目录
for %%I in ("%SRC%") do set "OUTDIR=%%~dpI"
set "ZIPPATH=%OUTDIR%ChemAgent-Deploy.zip"

echo    源目录: %SRC%
echo    输出到: %ZIPPATH%
echo.

echo [1/2] 正在打包...

:: 使用 PowerShell 的 Compress-Archive，直接从源目录打包，用 -Filter 排除
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "& { $src='%SRC%'; $zip='%ZIPPATH%'; if(Test-Path $zip){Remove-Item $zip -Force}; $tmp=Join-Path $env:TEMP ('ca_pack_'+(Get-Random)); New-Item $tmp -ItemType Directory -Force|Out-Null; $skip=@('.git','.venv','venv','__pycache__','.idea','.vscode','dist','build','node_modules'); $sf=@('.env','Thumbs.db','.DS_Store','pack.bat'); $n=0; Get-ChildItem $src -Recurse -File -Force|ForEach-Object{ $r=$_.FullName.Substring($src.Length).TrimStart('\'); $ok=$true; $r.Split('\')|ForEach-Object{ if($skip -contains $_){$ok=$false} }; if($sf -contains $_.Name){$ok=$false}; if($_.Extension -in '.pyc','.pyo','.pkl'){$ok=$false}; if($r -like '*.egg-info*'){$ok=$false}; if($ok){ $d=Join-Path $tmp $r; $p=Split-Path $d; if(!(Test-Path $p)){New-Item $p -ItemType Directory -Force|Out-Null}; Copy-Item $_.FullName $d; $n++ } }; Write-Host \"       收集了 $n 个文件\"; if($n -gt 0){ Compress-Archive -Path \"$tmp\*\" -DestinationPath $zip -Force; $s=[math]::Round((Get-Item $zip).Length/1MB,2); Write-Host \"       压缩完成: $s MB\" } else { Write-Host '[错误] 未找到文件' -ForegroundColor Red }; Remove-Item $tmp -Recurse -Force }"

echo.
echo [2/2] 完成！
echo.
echo    输出文件: %ZIPPATH%
echo.
echo    部署步骤:
echo      1. 将 ChemAgent-Deploy.zip 复制到目标电脑
echo      2. 解压到任意目录
echo      3. 双击运行 deploy.bat
echo ============================================================
echo.
pause
