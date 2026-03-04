
; CAD工具包安装脚本
; 使用 Inno Setup 编译

#define MyAppName "CAD工具包"
#define MyAppVersion "3.0.0"
#define MyAppPublisher "CAD工具包开发团队"
#define MyAppURL "http://localhost:8000"
#define MyAppExeName "CAD工具包.exe"

[Setup]
; 应用程序基本信息
AppId={{CAD-TOOLKIT-2026}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
LicenseFile=LICENSE.txt
InfoBeforeFile=README.txt
OutputDir=installer_output
OutputBaseFilename=CAD工具包安装程序_v{#MyAppVersion}
SetupIconFile=icon.ico
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64

; 界面设置
WizardImageFile=installer_banner.bmp
WizardSmallImageFile=installer_icon.bmp

[Languages]
Name: "chinesesimplified"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "附加图标:"; Flags: unchecked
Name: "quicklaunchicon"; Description: "创建快速启动栏图标"; GroupDescription: "附加图标:"; Flags: unchecked

[Files]
; 主程序
Source: "dist\CAD工具包.exe"; DestDir: "{app}"; Flags: ignoreversion
; 文档
Source: "CAD工具包使用说明.pdf"; DestDir: "{app}\docs"; Flags: ignoreversion
Source: "CAD工具包功能模块说明.pdf"; DestDir: "{app}\docs"; Flags: ignoreversion
; 配置文件
Source: "config.json"; DestDir: "{app}"; Flags: ignoreversion
; 更新检查模块
Source: "version_checker.py"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\使用说明"; Filename: "{app}\docs\CAD工具包使用说明.pdf"
Name: "{group}\卸载 {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon

[Registry]
; 注册表项 - 用于存储安装信息和版本
Root: HKLM; Subkey: "Software\{#MyAppName}"; Flags: uninsdeletekeyifempty
Root: HKLM; Subkey: "Software\{#MyAppName}"; ValueType: string; ValueName: "Version"; ValueData: "{#MyAppVersion}"
Root: HKLM; Subkey: "Software\{#MyAppName}"; ValueType: string; ValueName: "InstallPath"; ValueData: "{app}"
Root: HKLM; Subkey: "Software\{#MyAppName}"; ValueType: string; ValueName: "InstallDate"; ValueData: "{code:GetCurrentDate}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "启动 {#MyAppName}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}\logs"
Type: filesandordirs; Name: "{app}\cache"

[Code]
function GetCurrentDate(Param: String): String;
begin
  Result := GetDateTimeString('yyyy-mm-dd', #0, #0);
end;

// 检查是否已安装旧版本
function InitializeSetup(): Boolean;
var
  OldVersion: String;
  ResultCode: Integer;
begin
  Result := True;
  
  // 检查注册表中的版本信息
  if RegQueryStringValue(HKLM, 'Software\{#MyAppName}', 'Version', OldVersion) then
  begin
    if MsgBox('检测到已安装版本 ' + OldVersion + '。' + #13#10 + 
              '是否要升级到版本 {#MyAppVersion}？', 
              mbConfirmation, MB_YESNO) = IDYES then
    begin
      Result := True;
    end
    else
    begin
      Result := False;
    end;
  end;
end;

// 安装完成后的操作
procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    // 这里可以添加安装后的自定义操作
    // 例如：创建配置文件、初始化数据库等
  end;
end;
