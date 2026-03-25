"""
更新管理器模块
实现程序的自动更新检查和推送更新功能
"""
import os
import sys
import json
import requests
import hashlib
import tempfile
import shutil
from datetime import datetime
from typing import Optional, Dict, Tuple
from PyQt5.QtCore import QThread, pyqtSignal, QObject

try:
    import certifi
except Exception:
    certifi = None

# 当前版本号
CURRENT_VERSION = "3.8.2"

# GitHub配置
GITHUB_OWNER = "bataa7"  # 替换为你的GitHub用户名
GITHUB_REPO = "cad-toolkit"     # 替换为你的仓库名
GITHUB_API_BASE = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}"
GITHUB_RAW_BASE = f"https://raw.githubusercontent.com/{GITHUB_OWNER}/{GITHUB_REPO}/main"


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


class UpdateChecker(QThread):
    """更新检查线程"""
    update_available = pyqtSignal(dict)  # 有更新可用
    no_update = pyqtSignal()  # 无更新
    check_failed = pyqtSignal(str)  # 检查失败
    
    def __init__(self, current_version: str = CURRENT_VERSION):
        super().__init__()
        self.current_version = current_version
        self.timeout = 10  # 请求超时时间（秒）
    
    def run(self):
        """执行更新检查"""
        try:
            # 从GitHub获取最新版本信息
            version_info = self._fetch_version_info()
            
            if version_info:
                latest_version = version_info.get('version', '0.0.0')
                
                # 比较版本号
                if self._compare_versions(latest_version, self.current_version) > 0:
                    self.update_available.emit(version_info)
                else:
                    self.no_update.emit()
            else:
                self.check_failed.emit("无法获取版本信息")
                
        except Exception as e:
            self.check_failed.emit(f"检查更新失败: {str(e)}")
    
    def _fetch_version_info(self) -> Optional[Dict]:
        """从GitHub获取版本信息"""
        try:
            from system_config import UPDATE_CONFIG
            verify_value = UPDATE_CONFIG.get("ssl_verify", True)
            ca_bundle = UPDATE_CONFIG.get("ssl_ca_bundle", "")
            verify = _resolve_verify(verify_value, ca_bundle)

            # 尝试从GitHub Releases获取最新版本
            try:
                url = f"{GITHUB_API_BASE}/releases/latest"
                response = requests.get(url, timeout=self.timeout, verify=verify)
                
                if response.status_code == 200:
                    release_data = response.json()
                    return {
                        'version': release_data.get('tag_name', '').lstrip('v'),
                        'description': release_data.get('body', ''),
                        'download_url': release_data.get('html_url', ''),
                        'published_at': release_data.get('published_at', ''),
                        'assets': release_data.get('assets', [])
                    }
            except requests.RequestException:
                pass
            
            # 如果没有Releases，尝试从version.json获取
            urls = [
                f"{GITHUB_RAW_BASE}/version.json",
                f"https://cdn.jsdelivr.net/gh/{GITHUB_OWNER}/{GITHUB_REPO}@main/version.json",
            ]
            errors = []
            for url in _normalize_urls(urls):
                try:
                    response = requests.get(url, timeout=self.timeout, verify=verify)
                    if response.status_code == 200:
                        return response.json()
                except Exception as e:
                    errors.append(str(e))
            
            return None
            
        except requests.RequestException as e:
            print(f"获取版本信息失败: {e}")
            return None
    
    def _compare_versions(self, version1: str, version2: str) -> int:
        """
        比较两个版本号
        返回: 1 如果version1 > version2, -1 如果version1 < version2, 0 如果相等
        """
        try:
            v1_parts = [int(x) for x in version1.split('.')]
            v2_parts = [int(x) for x in version2.split('.')]
            
            # 补齐长度
            max_len = max(len(v1_parts), len(v2_parts))
            v1_parts.extend([0] * (max_len - len(v1_parts)))
            v2_parts.extend([0] * (max_len - len(v2_parts)))
            
            for v1, v2 in zip(v1_parts, v2_parts):
                if v1 > v2:
                    return 1
                elif v1 < v2:
                    return -1
            
            return 0
        except Exception:
            return 0


class UpdateDownloader(QThread):
    """更新下载线程"""
    progress = pyqtSignal(int)  # 下载进度 (0-100)
    download_complete = pyqtSignal(str)  # 下载完成，返回文件路径
    download_failed = pyqtSignal(str)  # 下载失败
    
    def __init__(self, download_url: str, file_name: str, verify=None, ca_bundle=None):
        super().__init__()
        self.download_url = download_url
        self.file_name = file_name
        self.save_path = None
        self.verify = verify
        self.ca_bundle = ca_bundle
    
    def run(self):
        """执行下载"""
        try:
            # 创建临时目录
            temp_dir = tempfile.mkdtemp(prefix='cad_toolkit_update_')
            self.save_path = os.path.join(temp_dir, self.file_name)
            parent_dir = os.path.dirname(self.save_path)
            if parent_dir:
                os.makedirs(parent_dir, exist_ok=True)
            
            # 下载文件
            verify_value = self.verify
            ca_bundle = self.ca_bundle
            if verify_value is None:
                from system_config import UPDATE_CONFIG
                verify_value = UPDATE_CONFIG.get("ssl_verify", True)
                ca_bundle = UPDATE_CONFIG.get("ssl_ca_bundle", "")
            verify = _resolve_verify(verify_value, ca_bundle)

            response = requests.get(self.download_url, stream=True, timeout=30, verify=verify)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0
            
            with open(self.save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)
                        
                        # 更新进度
                        if total_size > 0:
                            progress = int((downloaded_size / total_size) * 100)
                            self.progress.emit(progress)
            
            self.download_complete.emit(self.save_path)
            
        except Exception as e:
            self.download_failed.emit(f"下载失败: {str(e)}")


class NotificationFetcher(QThread):
    """消息通知获取线程"""
    notifications_received = pyqtSignal(list)  # 收到通知列表
    fetch_failed = pyqtSignal(str)  # 获取失败
    
    def __init__(self):
        super().__init__()
        self.timeout = 10
    
    def run(self):
        """获取通知"""
        try:
            notifications = self._fetch_notifications()
            if notifications is not None:
                self.notifications_received.emit(notifications)
            else:
                self.fetch_failed.emit("无法获取通知")
        except Exception as e:
            self.fetch_failed.emit(f"获取通知失败: {str(e)}")
    
    def _fetch_notifications(self) -> Optional[list]:
        """从GitHub或本地获取通知信息"""
        try:
            # 导入配置
            from system_config import DEV_MODE, NOTIFICATION_CONFIG
            
            # 如果启用了开发模式，使用本地数据
            if DEV_MODE.get('use_local_data', False):
                local_file = DEV_MODE.get('local_notifications', 'test_notifications.json')
                if os.path.exists(local_file):
                    with open(local_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        return data.get('notifications', [])
                else:
                    print(f"本地通知文件不存在: {local_file}")
                    return []
            
            verify_value = NOTIFICATION_CONFIG.get("ssl_verify", True)
            ca_bundle = NOTIFICATION_CONFIG.get("ssl_ca_bundle", "")
            verify = _resolve_verify(verify_value, ca_bundle)
            urls = [
                f"{GITHUB_RAW_BASE}/notifications.json",
                f"https://cdn.jsdelivr.net/gh/{GITHUB_OWNER}/{GITHUB_REPO}@main/notifications.json",
            ]
            errors = []
            for url in _normalize_urls(urls):
                try:
                    response = requests.get(url, timeout=self.timeout, verify=verify)
                    if response.status_code == 200:
                        data = response.json()
                        return data.get('notifications', [])
                except Exception as e:
                    errors.append(str(e))
            
            return []
            
        except requests.RequestException as e:
            print(f"获取通知失败: {e}")
            return None


class UpdateManager(QObject):
    """更新管理器主类"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_version = CURRENT_VERSION
        self.update_checker = None
        self.update_downloader = None
        self.notification_fetcher = None
    
    def check_for_updates(self, callback_available=None, callback_no_update=None, callback_failed=None):
        """
        检查更新
        
        Args:
            callback_available: 有更新时的回调函数
            callback_no_update: 无更新时的回调函数
            callback_failed: 检查失败时的回调函数
        """
        self.update_checker = UpdateChecker(self.current_version)
        
        if callback_available:
            self.update_checker.update_available.connect(callback_available)
        if callback_no_update:
            self.update_checker.no_update.connect(callback_no_update)
        if callback_failed:
            self.update_checker.check_failed.connect(callback_failed)
        
        self.update_checker.start()
    
    def download_update(self, download_url: str, file_name: str, 
                       callback_progress=None, callback_complete=None, callback_failed=None):
        """
        下载更新
        
        Args:
            download_url: 下载地址
            file_name: 文件名
            callback_progress: 进度回调函数
            callback_complete: 完成回调函数
            callback_failed: 失败回调函数
        """
        self.update_downloader = UpdateDownloader(download_url, file_name)
        
        if callback_progress:
            self.update_downloader.progress.connect(callback_progress)
        if callback_complete:
            self.update_downloader.download_complete.connect(callback_complete)
        if callback_failed:
            self.update_downloader.download_failed.connect(callback_failed)
        
        self.update_downloader.start()
    
    def fetch_notifications(self, callback_received=None, callback_failed=None):
        """
        获取通知
        
        Args:
            callback_received: 收到通知时的回调函数
            callback_failed: 获取失败时的回调函数
        """
        self.notification_fetcher = NotificationFetcher()
        
        if callback_received:
            self.notification_fetcher.notifications_received.connect(callback_received)
        if callback_failed:
            self.notification_fetcher.fetch_failed.connect(callback_failed)
        
        self.notification_fetcher.start()
    
    @staticmethod
    def get_current_version() -> str:
        """获取当前版本号"""
        return CURRENT_VERSION
    
    @staticmethod
    def save_last_check_time():
        """保存最后检查时间"""
        try:
            config_dir = os.path.join(os.path.expanduser('~'), '.cad_toolkit')
            os.makedirs(config_dir, exist_ok=True)
            
            config_file = os.path.join(config_dir, 'update_config.json')
            config = {}
            
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            
            config['last_check_time'] = datetime.now().isoformat()
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存检查时间失败: {e}")
    
    @staticmethod
    def get_last_check_time() -> Optional[datetime]:
        """获取最后检查时间"""
        try:
            config_dir = os.path.join(os.path.expanduser('~'), '.cad_toolkit')
            config_file = os.path.join(config_dir, 'update_config.json')
            
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    last_check = config.get('last_check_time')
                    if last_check:
                        return datetime.fromisoformat(last_check)
            
            return None
        except Exception as e:
            print(f"获取检查时间失败: {e}")
            return None


def integrate_update_manager(main_window):
    """
    将更新管理器集成到主窗口
    
    Args:
        main_window: 主窗口实例
    """
    # 创建更新管理器
    update_manager = UpdateManager(main_window)
    main_window.update_manager = update_manager
    
    # 添加菜单项
    if hasattr(main_window, 'menuBar'):
        help_menu = None
        for action in main_window.menuBar().actions():
            if action.text() == '帮助(&H)' or action.text() == '帮助':
                help_menu = action.menu()
                break
        
        if help_menu:
            # 添加检查更新菜单项
            check_update_action = help_menu.addAction('检查更新')
            check_update_action.triggered.connect(lambda: _check_for_updates(main_window))
            
            # 添加查看通知菜单项
            view_notifications_action = help_menu.addAction('查看通知')
            view_notifications_action.triggered.connect(lambda: _view_notifications(main_window))
    
    return update_manager


def _check_for_updates(main_window):
    """检查更新的内部函数"""
    from PyQt5.QtWidgets import QMessageBox, QProgressDialog
    
    # 显示检查中对话框
    progress = QProgressDialog("正在检查更新...", None, 0, 0, main_window)
    progress.setWindowTitle("检查更新")
    progress.setModal(True)
    progress.show()
    
    def on_update_available(version_info):
        progress.close()
        _show_update_dialog(main_window, version_info)
    
    def on_no_update():
        progress.close()
        QMessageBox.information(main_window, "检查更新", 
                               f"当前已是最新版本 v{CURRENT_VERSION}")
    
    def on_check_failed(error_msg):
        progress.close()
        QMessageBox.warning(main_window, "检查更新", 
                           f"检查更新失败:\n{error_msg}")
    
    main_window.update_manager.check_for_updates(
        callback_available=on_update_available,
        callback_no_update=on_no_update,
        callback_failed=on_check_failed
    )


def _show_update_dialog(main_window, version_info):
    """显示更新对话框"""
    from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QTextEdit, QHBoxLayout
    
    dialog = QDialog(main_window)
    dialog.setWindowTitle("发现新版本")
    dialog.setMinimumWidth(500)
    dialog.setMinimumHeight(300)
    
    layout = QVBoxLayout(dialog)
    
    # 版本信息
    version_label = QLabel(f"发现新版本: v{version_info.get('version', 'Unknown')}")
    version_label.setStyleSheet("font-size: 14px; font-weight: bold;")
    layout.addWidget(version_label)
    
    current_label = QLabel(f"当前版本: v{CURRENT_VERSION}")
    layout.addWidget(current_label)
    
    # 更新说明
    desc_label = QLabel("更新说明:")
    layout.addWidget(desc_label)
    
    desc_text = QTextEdit()
    desc_text.setReadOnly(True)
    desc_text.setPlainText(version_info.get('description', '暂无更新说明'))
    layout.addWidget(desc_text)
    
    # 按钮
    button_layout = QHBoxLayout()
    
    download_btn = QPushButton("前往下载")
    download_btn.clicked.connect(lambda: _open_download_page(version_info.get('download_url', '')))
    button_layout.addWidget(download_btn)
    
    later_btn = QPushButton("稍后提醒")
    later_btn.clicked.connect(dialog.accept)
    button_layout.addWidget(later_btn)
    
    layout.addLayout(button_layout)
    
    dialog.exec_()


def _open_download_page(url: str):
    """打开下载页面"""
    from PyQt5.QtGui import QDesktopServices
    from PyQt5.QtCore import QUrl
    
    if url:
        QDesktopServices.openUrl(QUrl(url))


def _view_notifications(main_window):
    """查看通知"""
    from PyQt5.QtWidgets import QDialog, QVBoxLayout, QListWidget, QPushButton, QProgressDialog
    
    # 显示加载中对话框
    progress = QProgressDialog("正在获取通知...", None, 0, 0, main_window)
    progress.setWindowTitle("获取通知")
    progress.setModal(True)
    progress.show()
    
    def on_notifications_received(notifications):
        progress.close()
        _show_notifications_dialog(main_window, notifications)
    
    def on_fetch_failed(error_msg):
        progress.close()
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.warning(main_window, "获取通知", 
                           f"获取通知失败:\n{error_msg}")
    
    main_window.update_manager.fetch_notifications(
        callback_received=on_notifications_received,
        callback_failed=on_fetch_failed
    )


def _show_notifications_dialog(main_window, notifications):
    """显示通知对话框"""
    from PyQt5.QtWidgets import QDialog, QVBoxLayout, QListWidget, QPushButton, QLabel, QTextEdit
    
    dialog = QDialog(main_window)
    dialog.setWindowTitle("系统通知")
    dialog.setMinimumWidth(600)
    dialog.setMinimumHeight(400)
    
    layout = QVBoxLayout(dialog)
    
    if not notifications:
        label = QLabel("暂无通知")
        label.setStyleSheet("padding: 20px; text-align: center;")
        layout.addWidget(label)
    else:
        # 通知列表
        for notification in notifications:
            notif_widget = QTextEdit()
            notif_widget.setReadOnly(True)
            notif_widget.setMaximumHeight(150)
            
            title = notification.get('title', '无标题')
            content = notification.get('content', '')
            date = notification.get('date', '')
            
            notif_text = f"【{title}】 {date}\n\n{content}"
            notif_widget.setPlainText(notif_text)
            layout.addWidget(notif_widget)
    
    # 关闭按钮
    close_btn = QPushButton("关闭")
    close_btn.clicked.connect(dialog.accept)
    layout.addWidget(close_btn)
    
    dialog.exec_()
