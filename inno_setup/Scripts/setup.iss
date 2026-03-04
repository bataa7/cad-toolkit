; Inno Setup 安装脚本 - CAD工具包
; 编码: UTF-8

#define MyAppName "CAD工具包"
#define MyAppVersion "3.0"
#define MyAppPublisher "CAD工具包开发团队"
#define MyAppExeName "CAD工具包.exe"

[Setup]
; 应用程序基本信息
AppId={{CAD-TOOLKIT-2025}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
OutputDir=..\Output
OutputBaseFilename=CAD工具包安装程序_v{#MyAppVersion}
Compression=lzma
SolidCompression=yes
WizardStyle=modern

; 权限设置
PrivilegesRequired=admin

; 语言和界面
ShowLanguageDialog=no
LanguageDetectionMethod=none

; 图标和界面
SetupIconFile=compiler:SetupClassicIcon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "chinesesimplified"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "附加图标:"; Flags: unchecked

[Files]
Source: "..\Files\CAD工具包.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\Files\启动主程序.bat"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\Files\README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\Files\CAD工具包使用说明.md"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\使用说明"; Filename: "{app}\CAD工具包使用说明.md"
Name: "{group}\卸载 {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "启动 {#MyAppName}"; Flags: nowait postinstall skipifsilent
