#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CAD工具包 - 清除更新设置
用于测试时清除用户设置和缓存
"""

from PyQt5.QtCore import QSettings
import sys

def clear_settings():
    """清除所有更新相关设置"""
    print("=" * 60)
    print("CAD工具包 - 清除更新设置")
    print("=" * 60)
    print()
    
    settings = QSettings('CADToolkit', 'UpdateManager')
    
    # 显示当前设置
    print("当前设置：")
    print(f"  自动检查更新: {settings.value('auto_check', True)}")
    print(f"  上次检查时间: {settings.value('last_check', '未设置')}")
    print(f"  跳过的版本: {settings.value('skipped_version', '无')}")
    print(f"  已显示消息: {settings.value('shown_messages', [])}")
    print()
    
    # 询问确认
    confirm = input("是否清除所有设置？(y/n): ").strip().lower()
    
    if confirm == 'y':
        settings.clear()
        print("\n✓ 已清除所有设置")
        print()
        print("现在可以重新测试：")
        print("  - 首次启动体验")
        print("  - 欢迎消息")
        print("  - 更新检查")
        print("  - 消息推送")
    else:
        print("\n✗ 已取消")
    
    print()
    print("=" * 60)

if __name__ == '__main__':
    try:
        from PyQt5.QtWidgets import QApplication
        app = QApplication(sys.argv)
        clear_settings()
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
    
    input("\n按回车键退出...")
