"""
集成示例 - 展示如何在主程序中集成消息推送和更新系统
"""
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QMenuBar, QMenu, QAction, QToolBar
from PyQt5.QtCore import QTimer

from notification_system import NotificationManager, NotificationWidget, NotificationFetcher
from update_system import UpdateChecker, UpdateDialog, CURRENT_VERSION
from system_config import NOTIFICATION_CONFIG, UPDATE_CONFIG, APP_VERSION


class IntegratedMainWindow(QMainWindow):
    """集成了消息推送和更新系统的主窗口示例"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"CAD工具包 v{APP_VERSION}")
        self.setGeometry(100, 100, 1200, 800)
        
        # 初始化通知管理器
        self.notification_manager = NotificationManager(
            api_url=NOTIFICATION_CONFIG['api_url'],
            cache_file=NOTIFICATION_CONFIG['cache_file']
        )
        
        self.init_ui()
        self.init_notification_system()
        self.init_update_system()
    
    def init_ui(self):
        """初始化UI"""
        # 创建菜单栏
        menubar = self.menuBar()
        
        # 帮助菜单
        help_menu = menubar.addMenu('帮助(&H)')
        
        # 检查更新
        check_update_action = QAction('检查更新', self)
        check_update_action.triggered.connect(self.manual_check_update)
        help_menu.addAction(check_update_action)
        
        # 通知中心
        notification_action = QAction('通知中心', self)
        notification_action.triggered.connect(self.show_notification_center)
        help_menu.addAction(notification_action)
        
        help_menu.addSeparator()
        
        # 关于
        about_action = QAction('关于', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
        # 创建工具栏
        toolbar = QToolBar()
        self.addToolBar(toolbar)
        
        # 添加通知小部件到工具栏
        self.notification_widget = NotificationWidget(self.notification_manager, self)
        toolbar.addWidget(self.notification_widget)
    
    def init_notification_system(self):
        """初始化通知系统"""
        if not NOTIFICATION_CONFIG['enabled']:
            return
        
        # 首次获取通知
        self.fetch_notifications()
        
        # 设置定时器定期检查
        self.notification_timer = QTimer(self)
        self.notification_timer.timeout.connect(self.fetch_notifications)
        self.notification_timer.start(NOTIFICATION_CONFIG['check_interval'] * 1000)
    
    def fetch_notifications(self):
        """获取通知"""
        fetcher = NotificationFetcher(NOTIFICATION_CONFIG['api_url'])
        fetcher.notifications_received.connect(self.on_notifications_received)
        fetcher.error_occurred.connect(self.on_notification_error)
        fetcher.start()
    
    def on_notifications_received(self, notifications):
        """收到通知"""
        self.notification_manager.notifications = notifications
        if hasattr(self, 'notification_widget'):
            self.notification_widget.update_badge()
    
    def on_notification_error(self, error_msg):
        """通知获取失败"""
        print(f"获取通知失败: {error_msg}")
    
    def show_notification_center(self):
        """显示通知中心"""
        from notification_system import NotificationDialog
        dialog = NotificationDialog(self.notification_manager, self)
        dialog.exec_()
        if hasattr(self, 'notification_widget'):
            self.notification_widget.update_badge()
    
    def init_update_system(self):
        """初始化更新系统"""
        if not UPDATE_CONFIG['enabled']:
            return
        
        # 启动时检查更新
        if UPDATE_CONFIG['check_on_startup']:
            QTimer.singleShot(3000, self.check_update)  # 延迟3秒检查
        
        # 设置定时器定期检查
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.check_update)
        self.update_timer.start(UPDATE_CONFIG['auto_check_interval'] * 1000)
    
    def check_update(self, silent=True):
        """检查更新"""
        self.update_checker = UpdateChecker(
            api_url=UPDATE_CONFIG['api_url'],
            current_version=APP_VERSION
        )
        self.update_checker.update_available.connect(
            lambda info: self.on_update_available(info, silent)
        )
        self.update_checker.no_update.connect(
            lambda: self.on_no_update(silent)
        )
        self.update_checker.error_occurred.connect(
            lambda err: self.on_update_error(err, silent)
        )
        self.update_checker.start()
    
    def manual_check_update(self):
        """手动检查更新"""
        self.check_update(silent=False)
    
    def on_update_available(self, update_info, silent):
        """有可用更新"""
        # 检查是否跳过此版本
        import json
        import os
        
        config_file = UPDATE_CONFIG['config_file']
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    skipped_version = config.get('skipped_version', '')
                    if skipped_version == update_info.get('version'):
                        if not silent:
                            from PyQt5.QtWidgets import QMessageBox
                            QMessageBox.information(self, "检查更新", 
                                                   "当前已是最新版本（已跳过的版本）")
                        return
            except:
                pass
        
        # 显示更新对话框
        dialog = UpdateDialog(update_info, APP_VERSION, self)
        dialog.exec_()
    
    def on_no_update(self, silent):
        """无可用更新"""
        if not silent:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.information(self, "检查更新", "当前已是最新版本")
    
    def on_update_error(self, error_msg, silent):
        """更新检查失败"""
        if not silent:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self, "检查更新", f"检查更新失败:\n{error_msg}")
    
    def show_about(self):
        """显示关于对话框"""
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.about(self, "关于", 
                         f"CAD工具包 v{APP_VERSION}\n\n"
                         f"一个功能强大的CAD辅助工具集合")


def main():
    """主函数"""
    app = QApplication(sys.argv)
    window = IntegratedMainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
