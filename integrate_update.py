#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CAD工具包 - 一键集成更新系统
自动将更新管理器集成到主程序中
"""

import os
import shutil

def integrate_update_system():
    """一键集成更新系统"""
    
    print("=" * 60)
    print("CAD工具包 - 更新系统集成工具")
    print("=" * 60)
    print()
    
    # 检查文件是否存在
    files_to_check = {
        'update_manager.py': '更新管理器模块',
        'cad_toolkit_gui.py': '主程序文件',
        'website/version.json': '版本信息文件'
    }
    
    print("检查必要文件...")
    all_files_exist = True
    for file_path, description in files_to_check.items():
        if os.path.exists(file_path):
            print(f"  ✓ {description}: {file_path}")
        else:
            print(f"  ✗ {description}: {file_path} (未找到)")
            all_files_exist = False
    
    if not all_files_exist:
        print("\n错误：缺少必要文件，请确保所有文件都已创建")
        return
    
    print("\n" + "=" * 60)
    print("开始集成...")
    print("=" * 60)
    
    # 1. 备份主程序
    print("\n1. 备份主程序...")
    backup_file = 'cad_toolkit_gui.py.backup'
    if not os.path.exists(backup_file):
        shutil.copy('cad_toolkit_gui.py', backup_file)
        print(f"  ✓ 已备份到: {backup_file}")
    else:
        print(f"  ℹ 备份文件已存在: {backup_file}")
    
    # 2. 读取主程序内容
    print("\n2. 读取主程序...")
    with open('cad_toolkit_gui.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 3. 检查是否已集成
    if 'from update_manager import' in content:
        print("  ℹ 更新管理器已经集成，跳过")
    else:
        print("  → 添加导入语句...")
        
        # 在导入部分添加
        import_line = "from update_manager import integrate_update_manager, CURRENT_VERSION\n"
        
        # 找到合适的位置插入（在其他导入之后）
        lines = content.split('\n')
        insert_index = 0
        for i, line in enumerate(lines):
            if line.startswith('from PyQt5') or line.startswith('import'):
                insert_index = i + 1
        
        lines.insert(insert_index, import_line)
        content = '\n'.join(lines)
        
        print("  ✓ 已添加导入语句")
    
    # 4. 检查是否已在MainWindow中集成
    if 'integrate_update_manager(self)' in content:
        print("  ℹ MainWindow 已集成更新管理器")
    else:
        print("  → 在 MainWindow.__init__ 中集成...")
        print("  ⚠ 需要手动添加以下代码到 MainWindow.__init__ 方法末尾：")
        print()
        print("    # 集成更新管理器")
        print("    integrate_update_manager(self)")
        print("    self.setWindowTitle(f'CAD工具包 v{CURRENT_VERSION}')")
        print()
    
    # 5. 保存修改
    if 'from update_manager import' not in content:
        print("\n3. 保存修改...")
        with open('cad_toolkit_gui.py', 'w', encoding='utf-8') as f:
            f.write(content)
        print("  ✓ 已保存")
    
    # 6. 生成安装程序配置
    print("\n4. 生成安装程序配置...")
    try:
        import installer_config
        installer_config.create_installer_files()
        print("  ✓ 安装程序配置已生成")
    except Exception as e:
        print(f"  ✗ 生成失败: {e}")
    
    # 7. 创建启动脚本
    print("\n5. 创建测试启动脚本...")
    
    test_script = """@echo off
chcp 65001 >nul
echo ========================================
echo    CAD工具包 - 测试更新功能
echo ========================================
echo.
echo 正在启动程序...
echo.

python cad_toolkit_gui.py

pause
"""
    
    with open('测试更新功能.bat', 'w', encoding='utf-8') as f:
        f.write(test_script)
    
    print("  ✓ 已创建: 测试更新功能.bat")
    
    # 完成
    print("\n" + "=" * 60)
    print("集成完成！")
    print("=" * 60)
    print()
    print("下一步操作：")
    print()
    print("1. 手动集成（如果尚未集成）：")
    print("   在 cad_toolkit_gui.py 的 MainWindow.__init__ 末尾添加：")
    print("   ")
    print("   # 集成更新管理器")
    print("   integrate_update_manager(self)")
    print("   self.setWindowTitle(f'CAD工具包 v{CURRENT_VERSION}')")
    print()
    print("2. 测试更新功能：")
    print("   双击运行: 测试更新功能.bat")
    print()
    print("3. 启动版本服务器：")
    print("   cd website")
    print("   python -m http.server 8000")
    print()
    print("4. 创建安装程序：")
    print("   - 安装 Inno Setup")
    print("   - 打开 installer.iss")
    print("   - 点击编译")
    print()
    print("5. 查看完整文档：")
    print("   集成更新系统指南.md")
    print()
    print("=" * 60)
    
    # 显示文件清单
    print("\n生成的文件：")
    generated_files = [
        'update_manager.py',
        'installer_config.py',
        'LICENSE.txt',
        'README.txt',
        'installer.iss',
        '测试更新功能.bat',
        'cad_toolkit_gui.py.backup'
    ]
    
    for file in generated_files:
        if os.path.exists(file):
            print(f"  ✓ {file}")
    
    print()
    print("备份文件：")
    print(f"  ✓ {backup_file}")
    print()

if __name__ == '__main__':
    try:
        integrate_update_system()
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
    
    input("\n按回车键退出...")
