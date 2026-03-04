"""
测试主程序集成
"""
import sys
from PyQt5.QtWidgets import QApplication

# 导入主程序
from cad_toolkit_gui import MainWindow

def main():
    print("=" * 60)
    print("🧪 测试主程序集成")
    print("=" * 60)
    print()
    print("正在启动主程序...")
    print()
    print("请检查：")
    print("  1. 状态栏右侧是否有 '🔔 通知' 按钮")
    print("  2. 菜单栏 → 帮助 → 是否有 '检查更新' 和 '通知中心'")
    print("  3. 点击通知按钮是否能打开通知中心")
    print("  4. 点击检查更新是否能弹出更新对话框")
    print()
    print("=" * 60)
    print()
    
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
