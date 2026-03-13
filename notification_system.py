"""Notification system for the CAD toolkit."""

import json
import logging
from typing import Dict, List, Optional

import requests
from PyQt5.QtCore import Qt, QThread, QTimer, pyqtSignal
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

try:
    import certifi
except Exception:
    certifi = None

logger = logging.getLogger(__name__)


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


class NotificationFetcher(QThread):
    """Background fetcher for notification data."""

    notifications_received = pyqtSignal(list)
    error_occurred = pyqtSignal(str)

    def __init__(self, api_url: str, timeout: int = 10, verify=None, ca_bundle=None):
        super().__init__()
        self.api_url = api_url
        self.timeout = timeout
        self.verify = verify
        self.ca_bundle = ca_bundle

    def run(self):
        try:
            verify_value = self.verify
            ca_bundle = self.ca_bundle
            if verify_value is None:
                from system_config import NOTIFICATION_CONFIG

                verify_value = NOTIFICATION_CONFIG.get("ssl_verify", True)
                ca_bundle = NOTIFICATION_CONFIG.get("ssl_ca_bundle", "")
            verify = _resolve_verify(verify_value, ca_bundle)

            errors = []
            for url in _normalize_urls(self.api_url):
                try:
                    response = requests.get(url, timeout=self.timeout, verify=verify)
                    response.raise_for_status()
                    data = response.json()
                    if isinstance(data, dict) and "notifications" in data:
                        notifications = data["notifications"]
                    elif isinstance(data, list):
                        notifications = data
                    else:
                        notifications = []
                    self.notifications_received.emit(notifications)
                    return
                except Exception as e:
                    errors.append(str(e))

            if errors:
                raise requests.RequestException(" | ".join(errors))
            raise requests.RequestException("未提供有效的通知地址")
        except requests.RequestException as e:
            logger.error(f"获取通知失败: {e}")
            self.error_occurred.emit(str(e))
        except json.JSONDecodeError as e:
            logger.error(f"解析通知数据失败: {e}")
            self.error_occurred.emit("数据格式错误")
        except Exception as e:
            logger.error(f"未知错误: {e}")
            self.error_occurred.emit(str(e))


class NotificationManager:
    """Tracks notification list and unread state."""

    def __init__(self, api_url: str, cache_file: str = "notifications_cache.json"):
        self.api_url = api_url
        self.cache_file = cache_file
        self.notifications: List[Dict] = []
        self.read_notifications = set()
        self.load_cache()

    def load_cache(self):
        try:
            with open(self.cache_file, "r", encoding="utf-8") as f:
                cache = json.load(f)
                self.read_notifications = set(cache.get("read", []))
        except FileNotFoundError:
            pass
        except Exception as e:
            logger.error(f"加载缓存失败: {e}")

    def save_cache(self):
        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump({"read": list(self.read_notifications)}, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存缓存失败: {e}")

    def mark_as_read(self, notification_id: str):
        self.read_notifications.add(notification_id)
        self.save_cache()

    def mark_all_as_read(self):
        for notif in self.notifications:
            if "id" in notif:
                self.read_notifications.add(notif["id"])
        self.save_cache()

    def get_unread_count(self) -> int:
        return sum(1 for n in self.notifications if n.get("id") not in self.read_notifications)

    def is_read(self, notification_id: str) -> bool:
        return notification_id in self.read_notifications


class NotificationDialog(QDialog):
    """Notification center dialog."""

    def __init__(self, manager: NotificationManager, parent=None):
        super().__init__(parent)
        self.manager = manager
        self.refresh_fetcher: Optional[NotificationFetcher] = None
        self.setWindowTitle("通知中心")
        self.setMinimumSize(800, 600)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        title_layout = QHBoxLayout()
        title_label = QLabel("通知中心")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_layout.addWidget(title_label)
        title_layout.addStretch()

        mark_all_btn = QPushButton("全部标记为已读")
        mark_all_btn.clicked.connect(self.mark_all_read)
        title_layout.addWidget(mark_all_btn)
        layout.addLayout(title_layout)

        splitter = QSplitter(Qt.Horizontal)
        self.notification_list = QListWidget()
        self.notification_list.currentItemChanged.connect(self.on_notification_selected)
        splitter.addWidget(self.notification_list)

        self.detail_browser = QTextBrowser()
        self.detail_browser.setOpenExternalLinks(True)
        splitter.addWidget(self.detail_browser)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        layout.addWidget(splitter)

        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.refresh_btn = QPushButton("刷新")
        self.refresh_btn.clicked.connect(self.refresh_notifications)
        button_layout.addWidget(self.refresh_btn)

        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        layout.addLayout(button_layout)

        self.load_notifications()

    def load_notifications(self):
        self.notification_list.clear()

        for notif in self.manager.notifications:
            notif_id = notif.get("id", "")
            title = notif.get("title", "无标题")
            level = notif.get("level", "info")
            date = notif.get("date", "")
            is_read = self.manager.is_read(notif_id)

            icon_map = {
                "critical": "[严重]",
                "warning": "[警告]",
                "info": "[通知]",
                "success": "[完成]",
            }
            display_text = f"{icon_map.get(level, '[通知]')} {title}"
            if not is_read:
                display_text = f"* {display_text}"
            if date:
                display_text += f" ({date})"

            item = QListWidgetItem(display_text)
            item.setData(Qt.UserRole, notif)
            font = item.font()
            if not is_read:
                font.setBold(True)
            item.setFont(font)
            self.notification_list.addItem(item)

        if self.notification_list.count() > 0:
            self.notification_list.setCurrentRow(0)

    def on_notification_selected(self, current, previous):
        if not current:
            return

        notif = current.data(Qt.UserRole)
        notif_id = notif.get("id", "")
        title = notif.get("title", "无标题")
        content = notif.get("content", "无内容")
        date = notif.get("date", "")
        level = notif.get("level", "info")

        level_colors = {
            "critical": "#d32f2f",
            "warning": "#f57c00",
            "info": "#1976d2",
            "success": "#388e3c",
        }
        color = level_colors.get(level, "#1976d2")

        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: 'Microsoft YaHei', Arial, sans-serif; padding: 20px; }}
                .header {{ border-left: 4px solid {color}; padding-left: 15px; margin-bottom: 20px; }}
                .title {{ font-size: 18px; font-weight: bold; color: {color}; margin-bottom: 5px; }}
                .date {{ color: #666; font-size: 12px; }}
                .content {{ line-height: 1.6; color: #333; }}
                a {{ color: {color}; }}
            </style>
        </head>
        <body>
            <div class="header">
                <div class="title">{title}</div>
                <div class="date">{date}</div>
            </div>
            <div class="content">{content}</div>
        </body>
        </html>
        """
        self.detail_browser.setHtml(html)

        if notif_id and not self.manager.is_read(notif_id):
            self.manager.mark_as_read(notif_id)
            font = current.font()
            font.setBold(False)
            current.setFont(font)
            if current.text().startswith("* "):
                current.setText(current.text()[2:])

    def mark_all_read(self):
        self.manager.mark_all_as_read()
        self.load_notifications()

    def refresh_notifications(self):
        if self.refresh_fetcher and self.refresh_fetcher.isRunning():
            return

        self.refresh_btn.setEnabled(False)
        self.refresh_btn.setText("刷新中...")
        self.refresh_fetcher = NotificationFetcher(self.manager.api_url)
        self.refresh_fetcher.notifications_received.connect(self.on_notifications_refreshed)
        self.refresh_fetcher.error_occurred.connect(self.on_refresh_error)
        self.refresh_fetcher.finished.connect(self._finish_refresh)
        self.refresh_fetcher.start()

    def on_notifications_refreshed(self, notifications):
        self.manager.notifications = notifications
        self.load_notifications()

    def on_refresh_error(self, error_msg):
        QMessageBox.warning(self, "刷新失败", f"获取通知失败：\n{error_msg}")

    def _finish_refresh(self):
        self.refresh_btn.setEnabled(True)
        self.refresh_btn.setText("刷新")
        if self.refresh_fetcher:
            self.refresh_fetcher.deleteLater()
            self.refresh_fetcher = None


class NotificationWidget(QWidget):
    """Status-bar notification entry."""

    def __init__(self, manager: NotificationManager, parent=None):
        super().__init__(parent)
        self.manager = manager
        self.fetcher: Optional[NotificationFetcher] = None
        self._has_polled_once = False
        self.init_ui()

        self.check_timer = QTimer(self)
        self.check_timer.timeout.connect(self.check_notifications)
        self.check_timer.start(300000)

    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.notification_btn = QPushButton("通知")
        self.notification_btn.clicked.connect(self.show_notifications)
        layout.addWidget(self.notification_btn)
        self.update_badge()

    def update_badge(self):
        unread_count = self.manager.get_unread_count()
        if unread_count > 0:
            self.notification_btn.setText(f"通知 ({unread_count})")
            self.notification_btn.setStyleSheet("QPushButton { color: red; font-weight: bold; }")
        else:
            self.notification_btn.setText("通知")
            self.notification_btn.setStyleSheet("")

    def check_notifications(self):
        if self.fetcher and self.fetcher.isRunning():
            return

        self.fetcher = NotificationFetcher(self.manager.api_url)
        self.fetcher.notifications_received.connect(self.on_notifications_received)
        self.fetcher.error_occurred.connect(self.on_notification_error)
        self.fetcher.finished.connect(self._finish_fetch)
        self.fetcher.start()

    @staticmethod
    def _collect_notification_ids(notifications):
        return {
            str(notif.get("id"))
            for notif in notifications
            if isinstance(notif, dict) and notif.get("id") is not None
        }

    @classmethod
    def _find_new_unread_notifications(cls, previous_notifications, notifications, read_ids=None):
        previous_ids = cls._collect_notification_ids(previous_notifications)
        current_ids = cls._collect_notification_ids(notifications)
        read_ids = {str(notif_id) for notif_id in (read_ids or ())}
        return [
            notif for notif in notifications
            if isinstance(notif, dict)
            and notif.get("id") is not None
            and str(notif.get("id")) in (current_ids - previous_ids)
            and str(notif.get("id")) not in read_ids
        ]

    def on_notifications_received(self, notifications):
        previous_notifications = list(self.manager.notifications)
        self.manager.notifications = notifications
        new_unread = self._find_new_unread_notifications(
            previous_notifications,
            notifications,
            self.manager.read_notifications,
        )

        if self._has_polled_once and new_unread:
            QMessageBox.information(self, "新通知", f"您有 {len(new_unread)} 条新通知")

        self.update_badge()
        self._has_polled_once = True

    def on_notification_error(self, error_msg):
        logger.warning(f"Notification polling failed: {error_msg}")

    def _finish_fetch(self):
        if self.fetcher:
            self.fetcher.deleteLater()
            self.fetcher = None

    def show_notifications(self):
        dialog = NotificationDialog(self.manager, self)
        dialog.exec_()
        self.update_badge()


EXAMPLE_API_RESPONSE = {
    "notifications": [
        {
            "id": "notif_001",
            "title": "系统维护通知",
            "content": "系统将于今晚 22:00-23:00 进行维护，期间部分功能可能不可用。",
            "level": "warning",
            "date": "2026-03-05",
        },
        {
            "id": "notif_002",
            "title": "新功能上线",
            "content": "我们上线了增量更新功能，现在更新更快更省流量。<br><a href='#'>查看详情</a>",
            "level": "info",
            "date": "2026-03-04",
        },
    ]
}
