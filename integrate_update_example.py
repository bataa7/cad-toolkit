"""
演示如何将更新管理器集成到现有的CAD工具包GUI中
"""
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QAction
from PyQt5.QtCore import QTimer

# 导入更新管理器
from update_manager import integrate_update_manager, CURRENT_VERSION


def integrate_to_existing_gui():
    """
    将更新功能集成到现有GUI的步骤说明
    """
    
    # 步骤1: 在 cad_toolkit_gui.py 的 MainWindow 类的 __init__ 方法中添加:
    """
    class MainWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            # ... 现有初始化代码 ...
            
            # 集成更新管理器
            from update_manager import integrate_update_manager
            integrate_update_manager(self)
            
            # 启动时自动检查更新（延迟3秒）
            QTimer.singleShot(3000, self.check_updates_on_startup)
    """
    
    # 步骤2: 在 MainWindow 类中添加自动检查更新的方法:
    """
    def check_updates_on_startup(self):
        '''启动时检查更新'''
        from update_manager import UpdateManager
        from datetime import datetime, timedelta
        
        # 检查上次检查时间，避免频繁检查
        last_check = UpdateManager.get_last_check_time()
        if last_check:
            # 如果距离上次检查不到24小时，跳过
            if datetime.now() - last_check < timedelta(hours=24):
                return
        
        # 静默检查更新
        def on_update_available(version_info):
            from PyQt5.QtWidgets import QMessageBox
            reply = QMessageBox.question(
                self, 
                '发现新版本',
                f'发现新版本 v{version_info.get("version")}\\n\\n是否查看详情？',
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                from update_manager import _show_update_dialog
                _show_update_dialog(self, version_info)
            
            # 保存检查时间
            UpdateManager.save_last_check_time()
        
        def on_check_failed(error_msg):
            # 静默失败，不打扰用户
            print(f'检查更新失败: {error_msg}')
        
        self.update_manager.check_for_updates(
            callback_available=on_update_available,
            callback_failed=on_check_failed
        )
    """
    
    # 步骤3: 确保帮助菜单存在（如果还没有）:
    """
    def create_menu_bar(self):
        '''创建菜单栏'''
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu('文件(&F)')
        # ... 添加文件菜单项 ...
        
        # 帮助菜单
        help_menu = menubar.addMenu('帮助(&H)')
        
        # 关于
        about_action = QAction('关于', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
        # 注意: 检查更新和查看通知菜单项会由 integrate_update_manager 自动添加
    """
    
    print("集成步骤说明已生成，请参考上述代码修改 cad_toolkit_gui.py")


def create_standalone_demo():
    """
    创建一个独立的演示程序
    """
    from PyQt5.QtWidgets import QMainWindow, QLabel, QVBoxLayout, QWidget, QPushButton
    
    class DemoWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle(f'CAD工具包更新系统演示 - v{CURRENT_VERSION}')
            self.setGeometry(100, 100, 600, 400)
            
            # 创建中心部件
            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            
            layout = QVBoxLayout(central_widget)
            
            # 标题
            title = QLabel('CAD工具包更新系统演示')
            title.setStyleSheet('font-size: 18px; font-weight: bold; padding: 20px;')
            layout.addWidget(title)
            
            # 版本信息
            version_label = QLabel(f'当前版本: v{CURRENT_VERSION}')
            version_label.setStyleSheet('font-size: 14px; padding: 10px;')
            layout.addWidget(version_label)
            
            # 按钮
            check_btn = QPushButton('手动检查更新')
            check_btn.clicked.connect(self.manual_check_update)
            layout.addWidget(check_btn)
            
            notif_btn = QPushButton('查看通知')
            notif_btn.clicked.connect(self.view_notifications)
            layout.addWidget(notif_btn)
            
            layout.addStretch()
            
            # 创建菜单栏
            self.create_menu_bar()
            
            # 集成更新管理器
            integrate_update_manager(self)
            
            # 启动时自动检查更新
            QTimer.singleShot(2000, self.check_updates_on_startup)
        
        def create_menu_bar(self):
            """创建菜单栏"""
            menubar = self.menuBar()
            
            # 帮助菜单
            help_menu = menubar.addMenu('帮助(&H)')
            
            about_action = QAction('关于', self)
            about_action.triggered.connect(self.show_about)
            help_menu.addAction(about_action)
        
        def manual_check_update(self):
            """手动检查更新"""
            from update_manager import _check_for_updates
            _check_for_updates(self)
        
        def view_notifications(self):
            """查看通知"""
            from update_manager import _view_notifications
            _view_notifications(self)
        
        def check_updates_on_startup(self):
            """启动时检查更新"""
            from update_manager import UpdateManager
            from datetime import datetime, timedelta
            from PyQt5.QtWidgets import QMessageBox
            
            # 检查上次检查时间
            last_check = UpdateManager.get_last_check_time()
            if last_check:
                if datetime.now() - last_check < timedelta(hours=24):
                    print('距离上次检查不到24小时，跳过自动检查')
                    return
            
            def on_update_available(version_info):
                reply = QMessageBox.question(
                    self, 
                    '发现新版本',
                    f'发现新版本 v{version_info.get("version")}\n\n是否查看详情？',
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply == QMessageBox.Yes:
                    from update_manager import _show_update_dialog
                    _show_update_dialog(self, version_info)
                
                UpdateManager.save_last_check_time()
            
            def on_no_update():
                print('当前已是最新版本')
                UpdateManager.save_last_check_time()
            
            def on_check_failed(error_msg):
                print(f'检查更新失败: {error_msg}')
            
            self.update_manager.check_for_updates(
                callback_available=on_update_available,
                callback_no_update=on_no_update,
                callback_failed=on_check_failed
            )
        
        def show_about(self):
            """显示关于对话框"""
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.about(
                self,
                '关于',
                f'CAD工具包 v{CURRENT_VERSION}\n\n'
                '一个功能强大的CAD文件处理工具\n\n'
                '功能特性:\n'
                '- 块批量导出\n'
                '- CAD文件读取\n'
                '- CAD块创建\n'
                '- Excel数据处理\n'
                '- 自动更新检查\n'
                '- 消息通知系统'
            )
    
    return DemoWindow


if __name__ == '__main__':
    # 显示集成步骤
    print("=" * 60)
    print("CAD工具包更新系统集成指南")
    print("=" * 60)
    integrate_to_existing_gui()
    print("\n" + "=" * 60)
    print("启动演示程序...")
    print("=" * 60 + "\n")
    
    # 运行演示程序
    app = QApplication(sys.argv)
    DemoWindowClass = create_standalone_demo()
    window = DemoWindowClass()
    window.show()
    sys.exit(app.exec_())
