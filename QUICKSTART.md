# 快速开始指南

5分钟快速部署CAD工具包到GitHub并启用自动更新功能。

## 前置条件

- ✓ Python 3.8+
- ✓ Git已安装
- ✓ GitHub账号

## 步骤1: 安装依赖 (1分钟)

```bash
pip install -r requirements.txt
```

## 步骤2: 配置GitHub (1分钟)

运行配置助手:

```bash
python setup_github.py
```

按提示输入:
- GitHub用户名
- 仓库名称 (默认: cad-toolkit)

## 步骤3: 创建GitHub仓库 (1分钟)

1. 访问 https://github.com/new
2. 仓库名称填写: `cad-toolkit` (或你在步骤2中设置的名称)
3. 选择 Public
4. 点击 "Create repository"

## 步骤4: 推送代码 (1分钟)

### 方法A: 使用自动生成的脚本

Windows:
```bash
deploy_to_github.bat
```

Linux/Mac:
```bash
bash deploy_to_github.sh
```

### 方法B: 手动执行

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/你的用户名/cad-toolkit.git
git push -u origin main
git tag v1.0.0
git push origin v1.0.0
```

## 步骤5: 测试功能 (1分钟)

运行测试脚本:

```bash
python test_update_system.py
```

运行演示程序:

```bash
python integrate_update_example.py
```

## 完成！

现在你的CAD工具包已经:
- ✓ 部署到GitHub
- ✓ 启用自动更新检查
- ✓ 启用消息通知系统

## 下一步

### 集成到主程序

在 `cad_toolkit_gui.py` 中添加以下代码:

```python
# 在文件顶部导入
from update_manager import integrate_update_manager
from PyQt5.QtCore import QTimer

# 在MainWindow.__init__方法中添加
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # ... 现有代码 ...
        
        # 集成更新管理器
        integrate_update_manager(self)
        
        # 启动时自动检查更新
        QTimer.singleShot(3000, self.check_updates_on_startup)
    
    def check_updates_on_startup(self):
        """启动时检查更新"""
        from update_manager import UpdateManager
        from datetime import datetime, timedelta
        from PyQt5.QtWidgets import QMessageBox
        
        # 检查上次检查时间
        last_check = UpdateManager.get_last_check_time()
        if last_check and datetime.now() - last_check < timedelta(hours=24):
            return
        
        def on_update_available(version_info):
            reply = QMessageBox.question(
                self, '发现新版本',
                f'发现新版本 v{version_info.get("version")}\n\n是否查看详情？',
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                from update_manager import _show_update_dialog
                _show_update_dialog(self, version_info)
            UpdateManager.save_last_check_time()
        
        self.update_manager.check_for_updates(
            callback_available=on_update_available,
            callback_failed=lambda e: print(f'检查更新失败: {e}')
        )
```

### 发布新版本

1. 修改 `update_manager.py` 中的版本号:
   ```python
   CURRENT_VERSION = "1.0.1"
   ```

2. 更新 `version.json`:
   ```json
   {
     "version": "1.0.1",
     "description": "更新内容..."
   }
   ```

3. 提交并推送:
   ```bash
   git add .
   git commit -m "Release v1.0.1"
   git push origin main
   git tag v1.0.1
   git push origin v1.0.1
   ```

## 常见问题

### Q: 检查更新失败？
A: 检查网络连接和GitHub配置是否正确。

### Q: 如何修改检查频率？
A: 在 `check_updates_on_startup` 方法中修改 `timedelta(hours=24)` 的值。

### Q: 如何添加新通知？
A: 编辑 `notifications.json` 文件，添加新的通知对象。

## 获取帮助

- 详细文档: `DEPLOYMENT.md`
- 系统指南: `UPDATE_SYSTEM_GUIDE.md`
- 实现总结: `IMPLEMENTATION_SUMMARY.md`

## 支持

遇到问题？在GitHub仓库提交Issue。
