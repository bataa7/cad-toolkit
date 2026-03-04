#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CAD工具包 - 更新系统演示
演示自动更新检查和消息推送功能
"""

import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel, QMenuBar
from PyQt5.QtCore import Qt
from update_manager import integrate_update_manager, CURRENT_VERSION

class DemoMainWindow(QMainWindow):
    """演示主窗口"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        
        # 集成更新管理器
        integrate_update_manager(self)
        
        # 设置窗口标题显示版本号
        self.setWindowTitle(f"CAD工具包 v{CURRENT_VERSION} - 更新系统演示")
    
    def init_ui(self):
        """初始化界面"""
        self.setGeometry(100, 100, 600, 400)
        
        # 中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        
        # 标题
        title = QLabel("CAD工具包 - 更新系统演示")
        title.setStyleSheet("font-size: 20px; font-weight: bold; padding: 20px;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # 版本信息
        version_label = QLabel(f"当前版本: v{CURRENT_VERSION}")
        version_label.setStyleSheet("font-size: 14px; padding: 10px;")
        version_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(version_label)
        
        # 说明
        info = QLabel("""
<div style="padding: 20px; line-height: 1.8;">
<p><b>功能演示：</b></p>
<ul>
<li>✓ 自动更新检查（启动时）</li>
<li>✓ 手动检查更新（帮助菜单）</li>
<li>✓ 消息推送通知</li>
<li>✓ 版本比较和更新提示</li>
<li>✓ 用户偏好设置</li>
</ul>
<br>
<p><b>使用方法：</b></p>
<ol>
<li>确保版本服务器已启动（website目录）</li>
<li>点击"帮助 -> 检查更新"测试更新功能</li>
<li>点击"帮助 -> 关于"查看版本信息</li>
</ol>
<br>
<p style="color: #666;">
提示：修改 update_manager.py 中的 CURRENT_VERSION 为旧版本（如 2.5.0）<br>
可以测试发现新版本的功能。
</p>
</div>
        """)
        info.setWordWrap(True)
        layout.addWidget(info)
        
        # 测试按钮
        test_btn = QPushButton("立即检查更新")
        test_btn.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
        """)
        test_btn.clicked.connect(self.manual_check_update)
        layout.addWidget(test_btn)
        
        layout.addStretch()
        
        central_widget.setLayout(layout)
    
    def manual_check_update(self):
        """手动检查更新"""
        if hasattr(self, 'update_manager'):
            self.update_manager.check_for_updates(silent=False)


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用程序信息
    app.setApplicationName("CAD工具包")
    app.setOrganizationName("CADToolkit")
    
    window = DemoMainWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    print("=" * 60)
    print("CAD工具包 - 更新系统演示")
    print("=" * 60)
    print()
    print("启动演示程序...")
    print()
    print("注意事项：")
    print("1. 确保版本服务器已启动：")
    print("   cd website")
    print("   python -m http.server 8000")
    print()
    print("2. 测试发现新版本功能：")
    print("   在 update_manager.py 中将 CURRENT_VERSION 改为 '2.5.0'")
    print()
    print("3. 查看消息推送：")
    print("   清除设置：删除注册表项或运行清除脚本")
    print()
    print("=" * 60)
    print()
    
    main()
