; ============================================================
;  ChemAgent Windows 安装包脚本 (Inno Setup 6)
;  用法: 安装 Inno Setup 后，右键此文件 → Compile
;  下载: https://jrsoftware.org/isdl.php
; ============================================================

#define MyAppName "ChemAgent"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "ChemAgent Contributors"
#define MyAppURL "https://github.com/<org>/chem-ai-agent"
#define MyAppExeName "ChemAgent.exe"

[Setup]
AppId={{C1E2A3F4-5678-9ABC-DEF0-123456789ABC}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
OutputDir=dist\installer
OutputBaseFilename=ChemAgent-Setup-{#MyAppVersion}
SetupIconFile=assets\chemagent.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "chinese"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "附加图标:"; Flags: checkedonce
Name: "startup"; Description: "开机自动启动 ChemAgent"; GroupDescription: "自动启动:"
Name: "startmenu"; Description: "创建开始菜单文件夹"; GroupDescription: "附加图标:"

[Files]
Source: "dist\ChemAgent\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\卸载 ChemAgent"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{userstartup}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: startup; Parameters: "--minimized"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "启动 ChemAgent"; Flags: nowait postinstall skipifsilent

[UninstallRun]
Filename: "taskkill"; Parameters: "/f /im ChemAgent.exe"; Flags: runhidden

[Code]
function InitializeSetup: Boolean;
begin
  Result := True;
end;