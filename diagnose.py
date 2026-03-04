"""
诊断脚本 - 检查主程序是否能正常启动
"""
import sys
import traceback

print("=" * 60)
print("CAD工具包诊断")
print("=" * 60)
print()

# 1. 检查Python版本
print("1. Python版本:")
print(f"   {sys.version}")
print()

# 2. 检查依赖
print("2. 检查依赖:")
dependencies = {
    'PyQt5': 'PyQt5.QtCore',
    'requests': 'requests',
    'ezdxf': 'ezdxf',
    'openpyxl': 'openpyxl',
    'pandas': 'pandas',
}

for name, module in dependencies.items():
    try:
        __import__(module)
        print(f"   [OK] {name}")
    except ImportError:
        print(f"   [X] {name} - 未安装")
print()

# 3. 检查消息推送和更新系统
print("3. 检查消息推送和更新系统:")
try:
    from notification_system import NotificationManager
    print("   [OK] notification_system")
except ImportError as e:
    print(f"   [X] notification_system - {e}")

try:
    from update_system import UpdateChecker
    print("   [OK] update_system")
except ImportError as e:
    print(f"   [X] update_system - {e}")

try:
    from system_config import APP_VERSION
    print(f"   [OK] system_config (版本: {APP_VERSION})")
except ImportError as e:
    print(f"   [X] system_config - {e}")
print()

# 4. 检查主程序导入
print("4. 检查主程序导入:")
try:
    from cad_toolkit_gui import MainWindow
    print("   [OK] cad_toolkit_gui 导入成功")
except Exception as e:
    print(f"   [X] cad_toolkit_gui 导入失败:")
    print(f"      {e}")
    traceback.print_exc()
print()

# 5. 尝试创建主窗口
print("5. 尝试创建主窗口:")
try:
    from PyQt5.QtWidgets import QApplication
    from cad_toolkit_gui import MainWindow
    
    app = QApplication(sys.argv)
    window = MainWindow()
    print("   [OK] 主窗口创建成功")
    
    # 检查通知功能
    if hasattr(window, 'notification_manager'):
        if window.notification_manager:
            print("   [OK] 通知管理器已初始化")
        else:
            print("   [!] 通知管理器未初始化（可能已禁用）")
    else:
        print("   [!] 没有通知管理器属性")
    
    # 检查通知小部件
    if hasattr(window, 'notification_widget'):
        print("   [OK] 通知小部件已添加")
    else:
        print("   [!] 通知小部件未添加")
    
    window.close()
    
except Exception as e:
    print(f"   [X] 主窗口创建失败:")
    print(f"      {e}")
    traceback.print_exc()
print()

# 6. 检查配置
print("6. 检查配置:")
try:
    from system_config import NOTIFICATION_CONFIG, UPDATE_CONFIG
    print(f"   通知系统: {'启用' if NOTIFICATION_CONFIG['enabled'] else '禁用'}")
    print(f"   更新系统: {'启用' if UPDATE_CONFIG['enabled'] else '禁用'}")
    print(f"   启动时检查更新: {'是' if UPDATE_CONFIG['check_on_startup'] else '否'}")
except Exception as e:
    print(f"   [X] 配置检查失败: {e}")
print()

print("=" * 60)
print("诊断完成")
print("=" * 60)
print()

# 询问是否启动主程序
try:
    response = input("是否启动主程序? (y/n): ")
    if response.lower() == 'y':
        print()
        print("正在启动主程序...")
        from PyQt5.QtWidgets import QApplication
        from cad_toolkit_gui import MainWindow
        
        app = QApplication(sys.argv)
        window = MainWindow()
        window.show()
        sys.exit(app.exec_())
except KeyboardInterrupt:
    print("\n已取消")
except Exception as e:
    print(f"\n启动失败: {e}")
    traceback.print_exc()
