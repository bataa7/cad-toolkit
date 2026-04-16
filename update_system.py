"""
增量更新系统
支持差分更新，只下载变化的文件
"""
import os
import sys
import json
import hashlib
import requests
import tempfile
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QUrl
from PyQt5.QtWidgets import (QApplication, QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QProgressBar, QTextEdit, QMessageBox)
from PyQt5.QtGui import QFont, QDesktopServices
import logging

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


def _quote_command_arg(value: str) -> str:
    return '"' + str(value).replace('"', '""') + '"'

# 当前版本
CURRENT_VERSION = "1.0.0"


class UpdateChecker(QThread):
    """检查更新的线程"""
    update_available = pyqtSignal(dict)  # 有更新时发送版本信息
    no_update = pyqtSignal()  # 无更新
    error_occurred = pyqtSignal(str)  # 错误
    
    def __init__(self, api_url: str, current_version: str, timeout: int = 10, verify=None, ca_bundle=None):
        super().__init__()
        self.api_url = api_url
        self.current_version = current_version
        self.timeout = timeout
        self.verify = verify
        self.ca_bundle = ca_bundle
    
    def run(self):
        try:
            verify_value = self.verify
            ca_bundle = self.ca_bundle
            if verify_value is None:
                from system_config import UPDATE_CONFIG
                verify_value = UPDATE_CONFIG.get("ssl_verify", True)
                ca_bundle = UPDATE_CONFIG.get("ssl_ca_bundle", "")
            verify = _resolve_verify(verify_value, ca_bundle)
            urls = _normalize_urls(self.api_url)
            errors = []
            for url in urls:
                try:
                    response = requests.get(url, timeout=self.timeout, verify=verify)
                    response.raise_for_status()
                    data = response.json()
                    latest_version = data.get('version', '')
                    if self.is_newer_version(latest_version, self.current_version):
                        self.update_available.emit(data)
                    else:
                        self.no_update.emit()
                    return
                except Exception as e:
                    errors.append(str(e))
            if errors:
                raise Exception(" | ".join(errors))
            raise Exception("未提供有效的更新地址")
        except Exception as e:
            logger.error(f"检查更新失败: {e}")
            self.error_occurred.emit(str(e))
    
    @staticmethod
    def is_newer_version(latest: str, current: str) -> bool:
        """比较版本号"""
        try:
            latest_parts = [int(x) for x in latest.split('.')]
            current_parts = [int(x) for x in current.split('.')]
            max_len = max(len(latest_parts), len(current_parts))
            latest_parts.extend([0] * (max_len - len(latest_parts)))
            current_parts.extend([0] * (max_len - len(current_parts)))
            return latest_parts > current_parts
        except:
            return False


class UpdateDownloader(QThread):
    """下载更新的线程"""
    progress_updated = pyqtSignal(int, int, str)  # 当前进度, 总大小, 状态信息
    download_completed = pyqtSignal(str)  # 下载完成，返回文件路径
    error_occurred = pyqtSignal(str)
    
    def __init__(self, update_info: dict, download_dir: str, verify=None, ca_bundle=None):
        super().__init__()
        self.update_info = update_info
        self.download_dir = download_dir
        self.cancelled = False
        self.verify = verify
        self.ca_bundle = ca_bundle
    
    def cancel(self):
        """取消下载"""
        self.cancelled = True
    
    def run(self):
        try:
            os.makedirs(self.download_dir, exist_ok=True)
            
            # 获取差分包信息
            patch_files = self.update_info.get('patch_files', [])
            full_package = self.update_info.get('full_package', {})
            
            if patch_files:
                # 增量更新
                self.download_patches(patch_files)
            elif full_package:
                # 完整包更新
                self.download_full_package(full_package)
            else:
                self.error_occurred.emit("更新信息不完整")
        except Exception as e:
            logger.error(f"下载更新失败: {e}")
            self.error_occurred.emit(str(e))
    
    def download_patches(self, patch_files: List[Dict]):
        """下载差分文件"""
        total_files = len(patch_files)
        
        for idx, patch_info in enumerate(patch_files):
            if self.cancelled:
                return
            
            action = patch_info.get('action', 'replace')
            file_name = patch_info.get('name') or patch_info.get('source') or ''
            file_hash = patch_info.get('hash', '')

            if action == 'delete':
                self.progress_updated.emit(
                    idx + 1, total_files,
                    f"准备删除文件 {idx + 1}/{total_files}: {patch_info.get('target', file_name)}"
                )
                continue

            file_url = patch_info.get('url', '')
            if not file_url:
                raise ValueError(f"增量更新文件缺少下载地址: {file_name or patch_info.get('target', '')}")
            if not file_name:
                raise ValueError(f"增量更新文件缺少名称: {file_url}")

            self.progress_updated.emit(
                idx + 1, total_files,
                f"下载文件 {idx + 1}/{total_files}: {file_name}"
            )

            # 下载文件
            local_path = os.path.join(self.download_dir, file_name)
            self.download_file(file_url, local_path, file_hash)
        
        self.download_completed.emit(self.download_dir)
    
    def download_full_package(self, package_info: Dict):
        """下载完整安装包"""
        url = package_info['url']
        file_name = package_info['name']
        file_hash = package_info.get('hash', '')
        
        self.progress_updated.emit(0, 1, f"下载完整安装包: {file_name}")
        
        local_path = os.path.join(self.download_dir, file_name)
        self.download_file(url, local_path, file_hash)
        
        self.download_completed.emit(local_path)
    
    def download_file(self, url: str, local_path: str, expected_hash: str = ''):
        """下载单个文件"""
        verify_value = self.verify
        ca_bundle = self.ca_bundle
        if verify_value is None:
            from system_config import UPDATE_CONFIG
            verify_value = UPDATE_CONFIG.get("ssl_verify", True)
            ca_bundle = UPDATE_CONFIG.get("ssl_ca_bundle", "")
        verify = _resolve_verify(verify_value, ca_bundle)

        parent_dir = os.path.dirname(local_path)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)

        response = requests.get(url, stream=True, timeout=30, verify=verify)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(local_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if self.cancelled:
                    return
                
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
        
        # 验证文件哈希
        if expected_hash:
            actual_hash = self.calculate_file_hash(local_path)
            if actual_hash != expected_hash:
                raise ValueError(f"文件校验失败: {local_path}")
    
    @staticmethod
    def calculate_file_hash(file_path: str) -> str:
        """计算文件SHA256哈希"""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        return sha256.hexdigest()


class UpdateInstaller:
    """更新安装器"""
    
    def __init__(self, update_dir: str, app_dir: str):
        self.update_dir = update_dir
        self.app_dir = app_dir
    
    def install_patches(self, patch_files) -> bool:
        """安装差分更新"""
        try:
            if not patch_files:
                raise ValueError("未提供增量更新文件")

            if isinstance(patch_files[0], dict):
                script_path = self.create_patch_script(patch_files)
                if sys.platform == 'win32':
                    subprocess.Popen(
                        ['cmd', '/c', script_path],
                        creationflags=subprocess.CREATE_NEW_CONSOLE
                    )
                else:
                    subprocess.Popen(['sh', script_path])
                return True

            backup_dir = os.path.join(tempfile.gettempdir(), 'cad_toolkit_backup')
            os.makedirs(backup_dir, exist_ok=True)
            
            # 备份原文件
            for patch_file in patch_files:
                patch_path = os.path.join(self.update_dir, patch_file)
                if not os.path.exists(patch_path):
                    continue
                
                # 读取补丁信息
                with open(patch_path, 'r', encoding='utf-8') as f:
                    patch_info = json.load(f)
                
                target_file = patch_info['target']
                target_path = os.path.join(self.app_dir, target_file)
                
                # 备份
                if os.path.exists(target_path):
                    backup_path = os.path.join(backup_dir, target_file)
                    os.makedirs(os.path.dirname(backup_path), exist_ok=True)
                    shutil.copy2(target_path, backup_path)
                
                # 应用补丁
                self.apply_patch(patch_info, target_path)
            
            return True
        except Exception as e:
            logger.error(f"安装更新失败: {e}")
            # 恢复备份
            if 'backup_dir' in locals():
                self.restore_backup(backup_dir)
            return False
    
    def apply_patch(self, patch_info: Dict, target_path: str):
        """应用单个补丁"""
        action = patch_info.get('action', 'replace')
        
        if action == 'replace':
            # 替换文件
            source = patch_info['source']
            source_path = os.path.join(self.update_dir, source)
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            shutil.copy2(source_path, target_path)
        
        elif action == 'delete':
            # 删除文件
            if os.path.exists(target_path):
                os.remove(target_path)
        
        elif action == 'create':
            # 创建新文件
            source = patch_info['source']
            source_path = os.path.join(self.update_dir, source)
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            shutil.copy2(source_path, target_path)

    def create_patch_script(self, patch_files: List[Dict]) -> str:
        """创建增量更新脚本，确保主程序退出后再替换文件。"""
        if sys.platform == 'win32':
            script_path = os.path.join(tempfile.gettempdir(), 'apply_incremental_update.bat')
            lines = [
                "@echo off",
                "echo 正在应用增量更新...",
                "timeout /t 2 /nobreak > nul",
            ]

            if getattr(sys, 'frozen', False):
                exe_name = os.path.basename(sys.executable)
                lines.append(f'taskkill /f /im {_quote_command_arg(exe_name)} 2>nul')
                lines.append("timeout /t 1 /nobreak > nul")

            for patch_info in patch_files:
                action = patch_info.get('action', 'replace')
                target_rel = patch_info.get('target') or patch_info.get('name')
                if not target_rel:
                    raise ValueError(f"补丁缺少 target: {patch_info}")

                target_path = os.path.join(self.app_dir, target_rel)

                if action in ('replace', 'create'):
                    payload_name = patch_info.get('name') or patch_info.get('source')
                    if not payload_name:
                        raise ValueError(f"补丁缺少 name/source: {patch_info}")
                    payload_path = os.path.join(self.update_dir, payload_name)
                    if not os.path.exists(payload_path):
                        raise FileNotFoundError(f"补丁文件不存在: {payload_path}")

                    target_dir = os.path.dirname(target_path)
                    if target_dir:
                        lines.append(f'if not exist {_quote_command_arg(target_dir)} mkdir {_quote_command_arg(target_dir)}')
                    lines.append(f'copy /y {_quote_command_arg(payload_path)} {_quote_command_arg(target_path)} >nul')
                elif action == 'delete':
                    lines.append(f'if exist {_quote_command_arg(target_path)} del /f /q {_quote_command_arg(target_path)}')
                else:
                    raise ValueError(f"不支持的补丁动作: {action}")

            if getattr(sys, 'frozen', False):
                restart_cmd = f'start "" {_quote_command_arg(sys.executable)}'
            else:
                argv = [sys.executable] + sys.argv
                restart_cmd = 'start "" ' + ' '.join(_quote_command_arg(arg) for arg in argv)
            lines.append(restart_cmd)
            lines.append('del "%~f0"')

            with open(script_path, 'w', encoding='utf-8') as f:
                f.write("\n".join(lines) + "\n")
            return script_path

        script_path = os.path.join(tempfile.gettempdir(), 'apply_incremental_update.sh')
        lines = [
            "#!/bin/bash",
            'echo "正在应用增量更新..."',
            "sleep 2",
        ]

        for patch_info in patch_files:
            action = patch_info.get('action', 'replace')
            target_rel = patch_info.get('target') or patch_info.get('name')
            if not target_rel:
                raise ValueError(f"补丁缺少 target: {patch_info}")

            target_path = os.path.join(self.app_dir, target_rel)

            if action in ('replace', 'create'):
                payload_name = patch_info.get('name') or patch_info.get('source')
                if not payload_name:
                    raise ValueError(f"补丁缺少 name/source: {patch_info}")
                payload_path = os.path.join(self.update_dir, payload_name)
                if not os.path.exists(payload_path):
                    raise FileNotFoundError(f"补丁文件不存在: {payload_path}")

                target_dir = os.path.dirname(target_path)
                if target_dir:
                    lines.append(f'mkdir -p {_quote_command_arg(target_dir)}')
                lines.append(f'cp -f {_quote_command_arg(payload_path)} {_quote_command_arg(target_path)}')
            elif action == 'delete':
                lines.append(f'rm -f {_quote_command_arg(target_path)}')
            else:
                raise ValueError(f"不支持的补丁动作: {action}")

        restart_cmd = ' '.join(_quote_command_arg(arg) for arg in [sys.executable] + sys.argv) + " &"
        lines.append(restart_cmd)
        lines.append('rm "$0"')

        with open(script_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines) + "\n")
        os.chmod(script_path, 0o755)
        return script_path
    
    def restore_backup(self, backup_dir: str):
        """恢复备份"""
        try:
            if os.path.exists(backup_dir):
                for root, dirs, files in os.walk(backup_dir):
                    for file in files:
                        backup_path = os.path.join(root, file)
                        rel_path = os.path.relpath(backup_path, backup_dir)
                        target_path = os.path.join(self.app_dir, rel_path)
                        shutil.copy2(backup_path, target_path)
        except Exception as e:
            logger.error(f"恢复备份失败: {e}")
    
    def install_full_package(self, package_path: str) -> bool:
        """安装完整包"""
        try:
            # 创建更新脚本
            script_path = self.create_update_script(package_path)
            
            # 启动更新脚本并退出当前程序
            if sys.platform == 'win32':
                subprocess.Popen(['cmd', '/c', script_path], 
                               creationflags=subprocess.CREATE_NEW_CONSOLE)
            else:
                subprocess.Popen(['sh', script_path])
            
            return True
        except Exception as e:
            logger.error(f"安装完整包失败: {e}")
            return False
    
    def create_update_script(self, package_path: str) -> str:
        """Create an update script for a directory payload or installer package."""
        package_path = os.path.abspath(package_path)

        if sys.platform == 'win32':
            script_path = os.path.join(tempfile.gettempdir(), 'update.bat')
            lines = [
                "@echo off",
                "echo Preparing update...",
                "timeout /t 2 /nobreak > nul",
            ]

            if getattr(sys, 'frozen', False):
                exe_name = os.path.basename(sys.executable)
                lines.append(f'taskkill /f /im {_quote_command_arg(exe_name)} 2>nul')
                lines.append("timeout /t 1 /nobreak > nul")

            if os.path.isdir(package_path):
                source_glob = os.path.join(package_path, "*")
                lines.append(
                    f'xcopy /s /e /y {_quote_command_arg(source_glob)} '
                    f'{_quote_command_arg(self.app_dir + os.sep)} >nul'
                )
                if getattr(sys, 'frozen', False):
                    lines.append(f'start "" {_quote_command_arg(sys.executable)}')
            elif package_path.lower().endswith(('.exe', '.msi')):
                lines.append(f'start "" {_quote_command_arg(package_path)}')
            else:
                raise ValueError(f"Unsupported full package type: {package_path}")

            lines.append('del "%~f0"')
            script_content = "\n".join(lines) + "\n"
        else:
            script_path = os.path.join(tempfile.gettempdir(), 'update.sh')
            lines = [
                "#!/bin/bash",
                'echo "Preparing update..."',
                "sleep 2",
            ]

            if os.path.isdir(package_path):
                source_glob = os.path.join(package_path, "*")
                lines.append(f'cp -rf {_quote_command_arg(source_glob)} {_quote_command_arg(self.app_dir + os.sep)}')
                if getattr(sys, 'frozen', False):
                    lines.append(f'{_quote_command_arg(sys.executable)} &')
            elif os.path.isfile(package_path):
                lines.append(f'chmod +x {_quote_command_arg(package_path)} 2>/dev/null || true')
                lines.append(f'{_quote_command_arg(package_path)} &')
            else:
                raise ValueError(f"Unsupported update package: {package_path}")

            lines.append('rm "$0"')
            script_content = "\n".join(lines) + "\n"

        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)

        if sys.platform != 'win32':
            os.chmod(script_path, 0o755)

        return script_path


class UpdateDialog(QDialog):
    """更新对话框"""
    
    def __init__(self, update_info: dict, current_version: str, parent=None):
        super().__init__(parent)
        self.update_info = update_info
        self.current_version = current_version
        self.downloader = None
        
        self.setWindowTitle("软件更新")
        self.setMinimumSize(600, 400)
        self.setModal(True)
        
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # 标题
        title_label = QLabel("🎉 发现新版本！")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # 版本信息
        version_layout = QHBoxLayout()
        version_layout.addWidget(QLabel(f"当前版本: {self.current_version}"))
        version_layout.addWidget(QLabel("→"))
        new_version_label = QLabel(f"最新版本: {self.update_info.get('version', 'Unknown')}")
        new_version_label.setStyleSheet("color: green; font-weight: bold;")
        version_layout.addWidget(new_version_label)
        version_layout.addStretch()
        layout.addLayout(version_layout)
        
        # 更新说明
        layout.addWidget(QLabel("更新内容:"))
        self.changelog_text = QTextEdit()
        self.changelog_text.setReadOnly(True)
        self.changelog_text.setMaximumHeight(150)
        changelog = self.update_info.get('changelog') or self.update_info.get('description') or '暂无更新说明'
        self.changelog_text.setPlainText(changelog)
        layout.addWidget(self.changelog_text)
        
        # 更新大小
        update_size = self.update_info.get('size', 0)
        size_mb = update_size / (1024 * 1024)
        update_type = "增量更新" if self.update_info.get('patch_files') else "完整更新"
        size_label = QLabel(f"更新类型: {update_type} | 下载大小: {size_mb:.2f} MB")
        size_label.setStyleSheet("color: #666;")
        layout.addWidget(size_label)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # 状态标签
        self.status_label = QLabel("")
        self.status_label.setVisible(False)
        layout.addWidget(self.status_label)
        
        # 按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.update_btn = QPushButton("立即更新")
        self.update_btn.clicked.connect(self.start_update)
        button_layout.addWidget(self.update_btn)
        
        self.later_btn = QPushButton("稍后提醒")
        self.later_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.later_btn)
        
        self.skip_btn = QPushButton("跳过此版本")
        self.skip_btn.clicked.connect(self.skip_version)
        button_layout.addWidget(self.skip_btn)
        
        layout.addLayout(button_layout)
    
    def start_update(self):
        """开始更新"""
        patch_files = self.update_info.get('patch_files', [])
        full_package = self.update_info.get('full_package') or {}
        has_incremental = bool(patch_files)
        has_full_package = isinstance(full_package, dict) and bool(full_package.get('url'))
        manual_download_url = self.update_info.get('download_url', '')

        if not has_incremental and not has_full_package:
            if manual_download_url:
                opened = QDesktopServices.openUrl(QUrl(manual_download_url))
                if opened:
                    QMessageBox.information(
                        self,
                        "手动更新",
                        "当前版本使用手动更新模式，已为你打开下载页面，请下载并安装最新版本。"
                    )
                    self.accept()
                    return
            QMessageBox.critical(self, "更新失败", "更新信息不完整，缺少可下载的更新包信息。")
            self.reject()
            return

        self.update_btn.setEnabled(False)
        self.later_btn.setEnabled(False)
        self.skip_btn.setEnabled(False)
        
        self.progress_bar.setVisible(True)
        self.status_label.setVisible(True)
        self.status_label.setText("正在下载更新...")
        
        # 创建下载目录
        download_dir = tempfile.mkdtemp(prefix='cad_toolkit_update_')
        
        # 开始下载
        self.downloader = UpdateDownloader(self.update_info, download_dir)
        self.downloader.progress_updated.connect(self.on_progress_updated)
        self.downloader.download_completed.connect(self.on_download_completed)
        self.downloader.error_occurred.connect(self.on_error)
        self.downloader.start()
    
    def on_progress_updated(self, current: int, total: int, status: str):
        """更新进度"""
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        self.status_label.setText(status)
    
    def on_download_completed(self, download_path: str):
        """下载完成"""
        self.status_label.setText("下载完成，正在安装...")
        
        # 安装更新
        app_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        installer = UpdateInstaller(download_path, app_dir)
        has_incremental = bool(self.update_info.get('patch_files'))
        
        if has_incremental:
            # 增量更新
            success = installer.install_patches(self.update_info['patch_files'])
        else:
            # 完整包更新
            success = installer.install_full_package(download_path)
        
        if success:
            if has_incremental:
                QMessageBox.information(self, "更新成功", "更新已完成，程序将重新启动。")
                self.accept()
                QApplication.quit()
            else:
                QMessageBox.information(
                    self,
                    "已启动安装程序",
                    "新版安装包已经启动，请按安装向导完成升级。安装完成后会启动新版本。"
                )
                self.accept()
                QApplication.quit()
        else:
            QMessageBox.critical(self, "更新失败", 
                               "更新安装失败，请稍后重试。")
            self.reject()
    
    def on_error(self, error_msg: str):
        """错误处理"""
        QMessageBox.critical(self, "更新失败", f"更新过程中出现错误:\n{error_msg}")
        self.reject()
    
    def skip_version(self):
        """跳过此版本"""
        # 保存跳过的版本号
        from system_config import UPDATE_CONFIG

        config_file = UPDATE_CONFIG.get("config_file", "update_config.json")
        try:
            config = {}
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            
            config['skipped_version'] = self.update_info.get('version')
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
        
        self.reject()
    
    def restart_application(self):
        """重启应用程序"""
        try:
            if getattr(sys, 'frozen', False):
                # 打包后的exe
                subprocess.Popen([sys.executable])
            else:
                # 开发环境
                subprocess.Popen([sys.executable] + sys.argv)
            
            sys.exit(0)
        except Exception as e:
            logger.error(f"重启失败: {e}")


# 示例API响应格式
EXAMPLE_UPDATE_API_RESPONSE = {
    "version": "1.1.0",
    "changelog": "1. 新增消息推送功能\n2. 新增增量更新功能\n3. 修复若干bug",
    "size": 5242880,  # 字节
    "release_date": "2026-03-05",
    "patch_files": [  # 增量更新文件列表
        {
            "name": "patches/cad_toolkit_gui.py",
            "url": "https://example.com/updates/patches/cad_toolkit_gui.py",
            "hash": "abc123...",
            "target": "cad_toolkit_gui.py",
            "action": "replace"
        }
    ],
    "full_package": {  # 完整安装包（备用）
        "name": "CAD工具包_v1.1.0.zip",
        "url": "https://example.com/updates/full_package.zip",
        "hash": "def456..."
    }
}
