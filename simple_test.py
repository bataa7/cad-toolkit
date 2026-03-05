"""
简单测试脚本 - 测试消息推送和更新系统的基本功能
"""
import sys
import requests
try:
    import certifi
except Exception:
    certifi = None
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QTextEdit
from PyQt5.QtCore import Qt

from notification_system import NotificationManager, NotificationDialog, NotificationFetcher
from update_system import UpdateChecker, UpdateDialog
from system_config import NOTIFICATION_CONFIG, UPDATE_CONFIG, APP_VERSION


def _normalize_urls(urls):
    if isinstance(urls, (list, tuple)):
        return [u for u in urls if u]
    if isinstance(urls, str) and urls:
        return [urls]
    return []


def _resolve_verify(verify_value, ca_bundle):
    if isinstance(ca_bundle, str) and ca_bundle:
        return ca_bundle
    if verify_value is False:
        return False
    if verify_value is True and certifi:
        return certifi.where()
    return True


class SimpleTestWindow(QMainWindow):
    """简单测试窗口"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"消息推送和更新系统测试 v{APP_VERSION}")
        self.setGeometry(100, 100, 600, 400)
        
        # 初始化通知管理器
        self.notification_manager = NotificationManager(
            api_url=NOTIFICATION_CONFIG['api_url']
        )
        
        self.init_ui()
        
        # 首次获取通知
        self.fetch_notifications()
    
    def init_ui(self):
        """初始化UI"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout(central_widget)
        
        # 日志显示
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)
        
        # 测试按钮
        btn_test_api = QPushButton("1. 测试API连接")
        btn_test_api.clicked.connect(self.test_api)
        layout.addWidget(btn_test_api)
        
        btn_fetch_notif = QPushButton("2. 获取通知")
        btn_fetch_notif.clicked.connect(self.fetch_notifications)
        layout.addWidget(btn_fetch_notif)
        
        btn_show_notif = QPushButton("3. 显示通知中心")
        btn_show_notif.clicked.connect(self.show_notification_center)
        layout.addWidget(btn_show_notif)
        
        btn_check_update = QPushButton("4. 检查更新")
        btn_check_update.clicked.connect(self.check_update)
        layout.addWidget(btn_check_update)
        
        self.log("✅ 测试窗口初始化完成")
        self.log(f"📍 通知API: {NOTIFICATION_CONFIG['api_url']}")
        self.log(f"📍 更新API: {UPDATE_CONFIG['api_url']}")
        self.log(f"📍 当前版本: {APP_VERSION}")
        self.log("")
    
    def log(self, message):
        """添加日志"""
        self.log_text.append(message)
    
    def test_api(self):
        """测试API连接"""
        self.log("🔍 测试API连接...")
        
        try:
            notif_verify = _resolve_verify(NOTIFICATION_CONFIG.get("ssl_verify", True), NOTIFICATION_CONFIG.get("ssl_ca_bundle", ""))
            update_verify = _resolve_verify(UPDATE_CONFIG.get("ssl_verify", True), UPDATE_CONFIG.get("ssl_ca_bundle", ""))
            notif_urls = _normalize_urls(NOTIFICATION_CONFIG['api_url'])
            update_urls = _normalize_urls(UPDATE_CONFIG['api_url'])

            notif_ok = False
            for url in notif_urls:
                try:
                    r1 = requests.get(url, timeout=5, verify=notif_verify)
                    if r1.status_code == 200:
                        data = r1.json()
                        count = len(data.get('notifications', []))
                        self.log(f"✅ 通知API正常 - 获取到 {count} 条通知")
                        notif_ok = True
                        break
                    self.log(f"❌ 通知API错误 - 状态码: {r1.status_code}")
                except Exception as e:
                    self.log(f"❌ 通知API错误 - {e}")

            if not notif_ok and not notif_urls:
                self.log("❌ 通知API未配置")

            update_ok = False
            for url in update_urls:
                try:
                    r2 = requests.get(url, timeout=5, verify=update_verify)
                    if r2.status_code == 200:
                        data = r2.json()
                        version = data.get('version', 'Unknown')
                        self.log(f"✅ 更新API正常 - 最新版本: {version}")
                        update_ok = True
                        break
                    self.log(f"❌ 更新API错误 - 状态码: {r2.status_code}")
                except Exception as e:
                    self.log(f"❌ 更新API错误 - {e}")

            if not update_ok and not update_urls:
                self.log("❌ 更新API未配置")
        except Exception as e:
            self.log(f"❌ API连接失败: {e}")
        
        self.log("")
    
    def fetch_notifications(self):
        """获取通知"""
        self.log("📥 正在获取通知...")
        
        try:
            verify = _resolve_verify(NOTIFICATION_CONFIG.get("ssl_verify", True), NOTIFICATION_CONFIG.get("ssl_ca_bundle", ""))
            urls = _normalize_urls(NOTIFICATION_CONFIG['api_url'])
            response = None
            for url in urls:
                try:
                    response = requests.get(url, timeout=5, verify=verify)
                    response.raise_for_status()
                    break
                except Exception:
                    response = None
            if response is None:
                raise Exception("无法获取通知")
            data = response.json()
            
            notifications = data.get('notifications', [])
            self.notification_manager.notifications = notifications
            
            total = len(notifications)
            unread = self.notification_manager.get_unread_count()
            
            self.log(f"✅ 获取成功 - 总计: {total} 条, 未读: {unread} 条")
            
            # 显示通知标题
            for notif in notifications[:3]:  # 只显示前3条
                title = notif.get('title', '无标题')
                level = notif.get('level', 'info')
                icon = {'info': 'ℹ️', 'warning': '⚠️', 'critical': '🔴', 'success': '✅'}.get(level, 'ℹ️')
                self.log(f"  {icon} {title}")
            
            if total > 3:
                self.log(f"  ... 还有 {total - 3} 条通知")
        
        except Exception as e:
            self.log(f"❌ 获取失败: {e}")
        
        self.log("")
    
    def show_notification_center(self):
        """显示通知中心"""
        self.log("📢 打开通知中心...")
        
        if not self.notification_manager.notifications:
            self.log("⚠️  请先获取通知")
            self.log("")
            return
        
        try:
            dialog = NotificationDialog(self.notification_manager, self)
            dialog.exec_()
            self.log("✅ 通知中心已关闭")
        except Exception as e:
            self.log(f"❌ 打开失败: {e}")
        
        self.log("")
    
    def check_update(self):
        """检查更新"""
        self.log("🔄 正在检查更新...")
        
        try:
            verify = _resolve_verify(UPDATE_CONFIG.get("ssl_verify", True), UPDATE_CONFIG.get("ssl_ca_bundle", ""))
            urls = _normalize_urls(UPDATE_CONFIG['api_url'])
            response = None
            for url in urls:
                try:
                    response = requests.get(url, timeout=5, verify=verify)
                    response.raise_for_status()
                    break
                except Exception:
                    response = None
            if response is None:
                raise Exception("无法检查更新")
            update_info = response.json()
            
            latest_version = update_info.get('version', '')
            self.log(f"📦 当前版本: {APP_VERSION}")
            self.log(f"📦 最新版本: {latest_version}")
            
            # 比较版本
            if self.is_newer_version(latest_version, APP_VERSION):
                self.log("✨ 发现新版本！")
                
                # 显示更新对话框
                dialog = UpdateDialog(update_info, APP_VERSION, self)
                dialog.exec_()
                self.log("✅ 更新对话框已关闭")
            else:
                self.log("✅ 当前已是最新版本")
        
        except Exception as e:
            self.log(f"❌ 检查失败: {e}")
        
        self.log("")
    
    @staticmethod
    def is_newer_version(latest: str, current: str) -> bool:
        """比较版本号"""
        try:
            latest_parts = [int(x) for x in latest.split('.')]
            current_parts = [int(x) for x in current.split('.')]
            return latest_parts > current_parts
        except:
            return False


def main():
    """主函数"""
    print("=" * 60)
    print("🧪 消息推送和更新系统测试")
    print("=" * 60)
    print()
    print("请确保测试服务器正在运行：")
    print("  python test_server.py")
    print()
    print("=" * 60)
    print()
    
    app = QApplication(sys.argv)
    window = SimpleTestWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
