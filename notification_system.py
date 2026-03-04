"""
消息推送系统
支持从服务器获取公告、通知等信息
"""
import json
import requests
from datetime import datetime
from typing import List, Dict, Optional
from PyQt5.QtCore import QThread, pyqtSignal, QTimer
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTextBrowser, 
                             QPushButton, QLabel, QListWidget, QListWidgetItem,
                             QSplitter, QWidget, QMessageBox)
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import Qt
import logging

logger = logging.getLogger(__name__)


class NotificationFetcher(QThread):
    """后台获取通知的线程"""
    notifications_received = pyqtSignal(list)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, api_url: str, timeout: int = 10):
        super().__init__()
        self.api_url = api_url
        self.timeout = timeout
    
    def run(self):
        try:
            response = requests.get(self.api_url, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            
            if isinstance(data, dict) and 'notifications' in data:
                notifications = data['notifications']
            elif isinstance(data, list):
                notifications = data
            else:
                notifications = []
            
            self.notifications_received.emit(notifications)
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
    """通知管理器"""
    
    def __init__(self, api_url: str, cache_file: str = "notifications_cache.json"):
        self.api_url = api_url
        self.cache_file = cache_file
        self.notifications = []
        self.read_notifications = set()
        self.load_cache()
    
    def load_cache(self):
        """从缓存加载已读通知"""
        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                cache = json.load(f)
                self.read_notifications = set(cache.get('read', []))
        except FileNotFoundError:
            pass
        except Exception as e:
            logger.error(f"加载缓存失败: {e}")
    
    def save_cache(self):
        """保存已读通知到缓存"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump({'read': list(self.read_notifications)}, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存缓存失败: {e}")
    
    def mark_as_read(self, notification_id: str):
        """标记通知为已读"""
        self.read_notifications.add(notification_id)
        self.save_cache()
    
    def mark_all_as_read(self):
        """标记所有通知为已读"""
        for notif in self.notifications:
            if 'id' in notif:
                self.read_notifications.add(notif['id'])
        self.save_cache()
    
    def get_unread_count(self) -> int:
        """获取未读通知数量"""
        return sum(1 for n in self.notifications if n.get('id') not in self.read_notifications)
    
    def is_read(self, notification_id: str) -> bool:
        """检查通知是否已读"""
        return notification_id in self.read_notifications


class NotificationDialog(QDialog):
    """通知中心对话框"""
    
    def __init__(self, manager: NotificationManager, parent=None):
        super().__init__(parent)
        self.manager = manager
        self.setWindowTitle("通知中心")
        self.setMinimumSize(800, 600)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # 标题栏
        title_layout = QHBoxLayout()
        title_label = QLabel("📢 通知中心")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        # 标记全部已读按钮
        mark_all_btn = QPushButton("全部标记为已读")
        mark_all_btn.clicked.connect(self.mark_all_read)
        title_layout.addWidget(mark_all_btn)
        
        layout.addLayout(title_layout)
        
        # 分割器
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧：通知列表
        self.notification_list = QListWidget()
        self.notification_list.currentItemChanged.connect(self.on_notification_selected)
        splitter.addWidget(self.notification_list)
        
        # 右侧：通知详情
        self.detail_browser = QTextBrowser()
        self.detail_browser.setOpenExternalLinks(True)
        splitter.addWidget(self.detail_browser)
        
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        layout.addWidget(splitter)
        
        # 底部按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        refresh_btn = QPushButton("刷新")
        refresh_btn.clicked.connect(self.refresh_notifications)
        button_layout.addWidget(refresh_btn)
        
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
        # 加载通知
        self.load_notifications()
    
    def load_notifications(self):
        """加载通知列表"""
        self.notification_list.clear()
        
        for notif in self.manager.notifications:
            notif_id = notif.get('id', '')
            title = notif.get('title', '无标题')
            level = notif.get('level', 'info')
            date = notif.get('date', '')
            is_read = self.manager.is_read(notif_id)
            
            # 图标
            icon_map = {
                'critical': '🔴',
                'warning': '⚠️',
                'info': 'ℹ️',
                'success': '✅'
            }
            icon = icon_map.get(level, 'ℹ️')
            
            # 显示文本
            display_text = f"{icon} {title}"
            if not is_read:
                display_text = f"● {display_text}"  # 未读标记
            if date:
                display_text += f" ({date})"
            
            item = QListWidgetItem(display_text)
            item.setData(Qt.UserRole, notif)
            
            # 设置字体
            font = item.font()
            if not is_read:
                font.setBold(True)
            item.setFont(font)
            
            self.notification_list.addItem(item)
        
        # 选中第一项
        if self.notification_list.count() > 0:
            self.notification_list.setCurrentRow(0)
    
    def on_notification_selected(self, current, previous):
        """通知被选中时"""
        if not current:
            return
        
        notif = current.data(Qt.UserRole)
        notif_id = notif.get('id', '')
        title = notif.get('title', '无标题')
        content = notif.get('content', '无内容')
        date = notif.get('date', '')
        level = notif.get('level', 'info')
        
        # 构建HTML内容
        level_colors = {
            'critical': '#d32f2f',
            'warning': '#f57c00',
            'info': '#1976d2',
            'success': '#388e3c'
        }
        color = level_colors.get(level, '#1976d2')
        
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: "Microsoft YaHei", Arial, sans-serif; padding: 20px; }}
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
            <div class="content">
                {content}
            </div>
        </body>
        </html>
        """
        
        self.detail_browser.setHtml(html)
        
        # 标记为已读
        if notif_id and not self.manager.is_read(notif_id):
            self.manager.mark_as_read(notif_id)
            # 更新列表项显示
            font = current.font()
            font.setBold(False)
            current.setFont(font)
            text = current.text()
            if text.startswith('● '):
                current.setText(text[2:])
    
    def mark_all_read(self):
        """标记全部为已读"""
        self.manager.mark_all_as_read()
        self.load_notifications()
    
    def refresh_notifications(self):
        """刷新通知"""
        self.load_notifications()


class NotificationWidget(QWidget):
    """通知小部件（可嵌入主窗口）"""
    
    def __init__(self, manager: NotificationManager, parent=None):
        super().__init__(parent)
        self.manager = manager
        self.init_ui()
        
        # 定时检查更新
        self.check_timer = QTimer(self)
        self.check_timer.timeout.connect(self.check_notifications)
        self.check_timer.start(300000)  # 每5分钟检查一次
    
    def init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.notification_btn = QPushButton("🔔 通知")
        self.notification_btn.clicked.connect(self.show_notifications)
        layout.addWidget(self.notification_btn)
        
        self.update_badge()
    
    def update_badge(self):
        """更新未读数量徽章"""
        unread_count = self.manager.get_unread_count()
        if unread_count > 0:
            self.notification_btn.setText(f"🔔 通知 ({unread_count})")
            self.notification_btn.setStyleSheet("QPushButton { color: red; font-weight: bold; }")
        else:
            self.notification_btn.setText("🔔 通知")
            self.notification_btn.setStyleSheet("")
    
    def check_notifications(self):
        """检查新通知"""
        fetcher = NotificationFetcher(self.manager.api_url)
        fetcher.notifications_received.connect(self.on_notifications_received)
        fetcher.start()
    
    def on_notifications_received(self, notifications):
        """收到通知时"""
        old_count = len(self.manager.notifications)
        self.manager.notifications = notifications
        new_count = len(notifications)
        
        # 如果有新通知，显示提示
        if new_count > old_count:
            unread = self.manager.get_unread_count()
            if unread > 0:
                QMessageBox.information(self, "新通知", f"您有 {unread} 条新通知！")
        
        self.update_badge()
    
    def show_notifications(self):
        """显示通知中心"""
        dialog = NotificationDialog(self.manager, self)
        dialog.exec_()
        self.update_badge()


# 示例API响应格式
EXAMPLE_API_RESPONSE = {
    "notifications": [
        {
            "id": "notif_001",
            "title": "系统维护通知",
            "content": "系统将于今晚22:00-23:00进行维护，期间可能无法使用部分功能。",
            "level": "warning",
            "date": "2026-03-05"
        },
        {
            "id": "notif_002",
            "title": "新功能上线",
            "content": "我们上线了增量更新功能，现在更新更快更省流量！<br><a href='#'>查看详情</a>",
            "level": "info",
            "date": "2026-03-04"
        }
    ]
}
