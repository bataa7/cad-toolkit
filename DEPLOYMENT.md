# CAD工具包 - GitHub部署指南

本指南将帮助你将CAD工具包部署到GitHub，并启用自动更新和消息通知功能。

## 前置准备

1. GitHub账号
2. Git已安装
3. Python 3.8+ 已安装

## 步骤1: 创建GitHub仓库

1. 登录GitHub
2. 点击右上角的 "+" -> "New repository"
3. 填写仓库信息:
   - Repository name: `cad-toolkit` (或你喜欢的名字)
   - Description: CAD文件处理工具
   - Public/Private: 根据需要选择
4. 点击 "Create repository"

## 步骤2: 配置更新管理器

编辑 `update_manager.py` 文件，修改以下配置:

```python
# GitHub配置
GITHUB_OWNER = "your-username"  # 替换为你的GitHub用户名
GITHUB_REPO = "cad-toolkit"     # 替换为你的仓库名
```

例如，如果你的GitHub用户名是 `zhangsan`，仓库名是 `cad-toolkit`:

```python
GITHUB_OWNER = "zhangsan"
GITHUB_REPO = "cad-toolkit"
```

## 步骤3: 初始化Git仓库并推送

在项目根目录打开终端，执行以下命令:

```bash
# 初始化Git仓库
git init

# 添加所有文件
git add .

# 提交
git commit -m "Initial commit: CAD工具包 v1.0.0"

# 添加远程仓库（替换为你的仓库地址）
git remote add origin https://github.com/your-username/cad-toolkit.git

# 推送到GitHub
git branch -M main
git push -u origin main
```

## 步骤4: 配置GitHub Actions（可选）

如果你想启用自动构建和发布功能:

1. 确保 `.github/workflows/release.yml` 文件已存在
2. 该工作流会在你推送标签时自动触发
3. 它会自动构建可执行文件并创建Release

注意: 自动构建需要在Windows环境下运行，GitHub Actions的Windows runner可能需要额外配置。

## 步骤5: 发布第一个版本

### 方法1: 使用GitHub Releases（推荐）

1. 在GitHub仓库页面，点击 "Releases"
2. 点击 "Create a new release"
3. 填写信息:
   - Tag version: `v1.0.0`
   - Release title: `v1.0.0 - 初始版本`
   - Description: 复制 `version.json` 中的描述
4. 上传构建好的可执行文件（如果有）
5. 点击 "Publish release"

### 方法2: 使用Git标签触发自动构建

```bash
# 创建标签
git tag v1.0.0

# 推送标签
git push origin v1.0.0
```

GitHub Actions会自动构建并创建Release。

## 步骤6: 测试更新功能

1. 运行程序
2. 点击菜单栏 -> 帮助 -> 检查更新
3. 如果配置正确，程序会连接到GitHub检查更新

## 步骤7: 发布新版本

当你需要发布新版本时:

1. 修改代码
2. 更新 `update_manager.py` 中的 `CURRENT_VERSION`:
   ```python
   CURRENT_VERSION = "1.0.1"
   ```

3. 更新 `version.json`:
   ```json
   {
     "version": "1.0.1",
     "description": "v1.0.1 更新内容...",
     "release_date": "2026-03-05"
   }
   ```

4. 提交并推送:
   ```bash
   git add .
   git commit -m "Release v1.0.1"
   git push origin main
   ```

5. 创建新的Release或标签:
   ```bash
   git tag v1.0.1
   git push origin v1.0.1
   ```

## 步骤8: 管理通知

编辑 `notifications.json` 来添加或修改通知:

```json
{
  "notifications": [
    {
      "id": "3",
      "title": "新功能发布",
      "content": "v1.0.1 新增了XXX功能...",
      "date": "2026-03-05",
      "type": "update",
      "priority": "high"
    }
  ]
}
```

提交并推送更改:

```bash
git add notifications.json
git commit -m "Update notifications"
git push origin main
```

用户下次启动程序时会自动获取新通知。

## 集成到现有GUI

在 `cad_toolkit_gui.py` 的 `MainWindow` 类中添加:

```python
from update_manager import integrate_update_manager, CURRENT_VERSION
from PyQt5.QtCore import QTimer

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # ... 现有初始化代码 ...
        
        # 集成更新管理器
        integrate_update_manager(self)
        
        # 启动时自动检查更新（延迟3秒）
        QTimer.singleShot(3000, self.check_updates_on_startup)
    
    def check_updates_on_startup(self):
        """启动时检查更新"""
        from update_manager import UpdateManager
        from datetime import datetime, timedelta
        from PyQt5.QtWidgets import QMessageBox
        
        # 检查上次检查时间，避免频繁检查
        last_check = UpdateManager.get_last_check_time()
        if last_check:
            if datetime.now() - last_check < timedelta(hours=24):
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
        
        def on_check_failed(error_msg):
            print(f'检查更新失败: {error_msg}')
        
        self.update_manager.check_for_updates(
            callback_available=on_update_available,
            callback_failed=on_check_failed
        )
```

## 测试演示程序

运行演示程序来测试更新功能:

```bash
python integrate_update_example.py
```

## 故障排除

### 问题1: 检查更新失败

- 检查网络连接
- 确认GitHub仓库是公开的（或配置了访问令牌）
- 检查 `update_manager.py` 中的配置是否正确

### 问题2: 无法获取通知

- 确认 `notifications.json` 文件已推送到GitHub
- 检查文件路径和JSON格式是否正确

### 问题3: GitHub Actions构建失败

- 检查 `.github/workflows/release.yml` 配置
- 确认所有依赖都在 `requirements.txt` 中
- 查看GitHub Actions日志获取详细错误信息

## 高级配置

### 使用私有仓库

如果使用私有仓库，需要配置GitHub Personal Access Token:

1. 在GitHub生成Personal Access Token
2. 在 `update_manager.py` 中添加认证:

```python
def _fetch_version_info(self) -> Optional[Dict]:
    headers = {
        'Authorization': 'token YOUR_GITHUB_TOKEN'
    }
    response = requests.get(url, headers=headers, timeout=self.timeout)
    # ...
```

### 自定义更新服务器

如果不想使用GitHub，可以修改 `update_manager.py` 中的URL配置，指向你自己的服务器。

## 安全建议

1. 不要在代码中硬编码敏感信息（如访问令牌）
2. 使用HTTPS确保通信安全
3. 验证下载文件的完整性（可添加SHA256校验）
4. 定期更新依赖库以修复安全漏洞

## 许可证

确保在仓库中包含适当的许可证文件（如MIT License）。

## 支持

如有问题，请在GitHub仓库中提交Issue。
