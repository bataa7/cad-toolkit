#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CAD工具包 - 版本检查模块
可以集成到主程序中，用于检查更新
"""

import json
import urllib.request
import urllib.error
from packaging import version as pkg_version

class VersionChecker:
    """版本检查器"""
    
    def __init__(self, current_version, update_url="http://localhost:8000/version.json"):
        """
        初始化版本检查器
        
        Args:
            current_version: 当前程序版本
            update_url: 版本信息URL
        """
        self.current_version = current_version
        self.update_url = update_url
        self.latest_info = None
    
    def check_for_updates(self):
        """
        检查是否有新版本
        
        Returns:
            dict: 更新信息，如果有更新返回详细信息，否则返回None
        """
        try:
            # 获取最新版本信息
            with urllib.request.urlopen(self.update_url, timeout=5) as response:
                data = json.loads(response.read().decode('utf-8'))
                self.latest_info = data
                
                latest_version = data['latest_version']
                
                # 比较版本
                if self._compare_versions(latest_version, self.current_version) > 0:
                    # 获取最新版本的更新日志
                    changelog = data['changelog'][0] if data['changelog'] else {}
                    
                    return {
                        'has_update': True,
                        'latest_version': latest_version,
                        'current_version': self.current_version,
                        'release_date': data['release_date'],
                        'download_url': data['download_url'],
                        'file_size': data['file_size'],
                        'changes': changelog.get('changes', []),
                        'update_notes': data.get('update_notes', '')
                    }
                else:
                    return {
                        'has_update': False,
                        'latest_version': latest_version,
                        'current_version': self.current_version
                    }
                    
        except urllib.error.URLError as e:
            print(f"检查更新失败: 无法连接到服务器 ({e})")
            return None
        except Exception as e:
            print(f"检查更新失败: {e}")
            return None
    
    def _compare_versions(self, v1, v2):
        """
        比较两个版本号
        
        Args:
            v1: 版本1
            v2: 版本2
            
        Returns:
            int: 1表示v1>v2, 0表示相等, -1表示v1<v2
        """
        try:
            ver1 = pkg_version.parse(v1)
            ver2 = pkg_version.parse(v2)
            
            if ver1 > ver2:
                return 1
            elif ver1 < ver2:
                return -1
            else:
                return 0
        except:
            # 简单的字符串比较
            parts1 = [int(x) for x in v1.split('.')]
            parts2 = [int(x) for x in v2.split('.')]
            
            for i in range(max(len(parts1), len(parts2))):
                p1 = parts1[i] if i < len(parts1) else 0
                p2 = parts2[i] if i < len(parts2) else 0
                
                if p1 > p2:
                    return 1
                elif p1 < p2:
                    return -1
            
            return 0
    
    def get_changelog(self, version=None):
        """
        获取指定版本的更新日志
        
        Args:
            version: 版本号，None表示最新版本
            
        Returns:
            dict: 更新日志信息
        """
        if not self.latest_info:
            self.check_for_updates()
        
        if not self.latest_info:
            return None
        
        if version is None:
            return self.latest_info['changelog'][0] if self.latest_info['changelog'] else None
        
        for log in self.latest_info['changelog']:
            if log['version'] == version:
                return log
        
        return None


def show_update_dialog(update_info):
    """
    显示更新对话框（使用PyQt5）
    
    Args:
        update_info: 更新信息字典
    """
    try:
        from PyQt5.QtWidgets import QMessageBox, QApplication
        import sys
        
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        msg = QMessageBox()
        msg.setWindowTitle("发现新版本")
        msg.setIcon(QMessageBox.Information)
        
        text = f"""
发现新版本 v{update_info['latest_version']}！

当前版本: v{update_info['current_version']}
最新版本: v{update_info['latest_version']}
发布日期: {update_info['release_date']}

更新内容:
"""
        for change in update_info['changes'][:5]:  # 只显示前5条
            text += f"\n• {change}"
        
        if len(update_info['changes']) > 5:
            text += f"\n... 还有 {len(update_info['changes']) - 5} 条更新"
        
        msg.setText(text)
        msg.setInformativeText("\n是否立即前往下载？")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setDefaultButton(QMessageBox.Yes)
        
        result = msg.exec_()
        
        if result == QMessageBox.Yes:
            import webbrowser
            webbrowser.open("http://localhost:8000/#download")
        
    except ImportError:
        # 如果没有PyQt5，使用控制台输出
        print("\n" + "=" * 50)
        print("发现新版本！")
        print("=" * 50)
        print(f"当前版本: v{update_info['current_version']}")
        print(f"最新版本: v{update_info['latest_version']}")
        print(f"发布日期: {update_info['release_date']}")
        print("\n更新内容:")
        for change in update_info['changes']:
            print(f"  • {change}")
        print("\n请访问 http://localhost:8000 下载最新版本")
        print("=" * 50)


# 示例用法
if __name__ == '__main__':
    # 当前程序版本
    CURRENT_VERSION = "3.0.0"
    
    # 创建版本检查器
    checker = VersionChecker(CURRENT_VERSION)
    
    print("正在检查更新...")
    update_info = checker.check_for_updates()
    
    if update_info is None:
        print("检查更新失败，请检查网络连接")
    elif update_info['has_update']:
        print(f"\n发现新版本: v{update_info['latest_version']}")
        show_update_dialog(update_info)
    else:
        print(f"\n当前已是最新版本: v{update_info['current_version']}")
