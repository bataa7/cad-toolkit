#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CAD工具包 - 安装程序配置
使用 Inno Setup 创建专业的 Windows 安装程序
"""

INNO_SETUP_SCRIPT = """
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
DefaultDirName={autopf}\\{#MyAppName}
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
Name: "chinesesimplified"; MessagesFile: "compiler:Languages\\ChineseSimplified.isl"

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "附加图标:"; Flags: unchecked
Name: "quicklaunchicon"; Description: "创建快速启动栏图标"; GroupDescription: "附加图标:"; Flags: unchecked

[Files]
; 主程序
Source: "dist\\CAD工具包.exe"; DestDir: "{app}"; Flags: ignoreversion
; 文档
Source: "CAD工具包使用说明.pdf"; DestDir: "{app}\\docs"; Flags: ignoreversion
Source: "CAD工具包功能模块说明.pdf"; DestDir: "{app}\\docs"; Flags: ignoreversion
; 配置文件
Source: "config.json"; DestDir: "{app}"; Flags: ignoreversion
; 更新检查模块
Source: "version_checker.py"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\\{#MyAppName}"; Filename: "{app}\\{#MyAppExeName}"
Name: "{group}\\使用说明"; Filename: "{app}\\docs\\CAD工具包使用说明.pdf"
Name: "{group}\\卸载 {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\\{#MyAppName}"; Filename: "{app}\\{#MyAppExeName}"; Tasks: desktopicon
Name: "{userappdata}\\Microsoft\\Internet Explorer\\Quick Launch\\{#MyAppName}"; Filename: "{app}\\{#MyAppExeName}"; Tasks: quicklaunchicon

[Registry]
; 注册表项 - 用于存储安装信息和版本
Root: HKLM; Subkey: "Software\\{#MyAppName}"; Flags: uninsdeletekeyifempty
Root: HKLM; Subkey: "Software\\{#MyAppName}"; ValueType: string; ValueName: "Version"; ValueData: "{#MyAppVersion}"
Root: HKLM; Subkey: "Software\\{#MyAppName}"; ValueType: string; ValueName: "InstallPath"; ValueData: "{app}"
Root: HKLM; Subkey: "Software\\{#MyAppName}"; ValueType: string; ValueName: "InstallDate"; ValueData: "{code:GetCurrentDate}"

[Run]
Filename: "{app}\\{#MyAppExeName}"; Description: "启动 {#MyAppName}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}\\logs"
Type: filesandordirs; Name: "{app}\\cache"

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
  if RegQueryStringValue(HKLM, 'Software\\{#MyAppName}', 'Version', OldVersion) then
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
"""

def create_installer_files():
    """创建安装程序所需的文件"""
    
    # 创建 LICENSE.txt
    license_text = """CAD工具包软件许可协议

版权所有 © 2026 CAD工具包开发团队

本软件按"原样"提供，不提供任何形式的明示或暗示担保。

使用条款：
1. 本软件免费提供给个人和企业使用
2. 允许复制和分发本软件
3. 不得用于非法用途
4. 开发者不对使用本软件造成的任何损失负责

如有问题，请访问：http://localhost:8000
"""
    
    with open('LICENSE.txt', 'w', encoding='utf-8') as f:
        f.write(license_text)
    
    # 创建 README.txt
    readme_text = """欢迎使用 CAD工具包 v3.0.0

这是一款专业的DXF文件批量处理工具。

主要功能：
• 块批量管理
• 智能筛寻合并
• 文本批量更新
• 自动排版
• BOM数量计算

安装说明：
1. 点击"下一步"继续安装
2. 选择安装目录
3. 选择是否创建桌面快捷方式
4. 点击"安装"开始安装
5. 安装完成后即可使用

系统要求：
• Windows 7/8/10/11
• 4GB RAM
• 100MB 磁盘空间

技术支持：
访问 http://localhost:8000 获取帮助文档和更新

感谢使用！
"""
    
    with open('README.txt', 'w', encoding='utf-8') as f:
        f.write(readme_text)
    
    # 创建 Inno Setup 脚本
    with open('installer.iss', 'w', encoding='utf-8-sig') as f:
        f.write(INNO_SETUP_SCRIPT)
    
    print("✓ 安装程序配置文件已创建")
    print("  - LICENSE.txt")
    print("  - README.txt")
    print("  - installer.iss")
    print("\n下一步：")
    print("1. 安装 Inno Setup: https://jrsoftware.org/isdl.php")
    print("2. 打开 installer.iss 文件")
    print("3. 点击 Build -> Compile 生成安装程序")

if __name__ == '__main__':
    create_installer_files()
