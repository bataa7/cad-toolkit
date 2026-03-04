# 更新系统使用指南

## 概述

CAD工具包内置了自动更新检查和消息通知系统，采用"客户端请求 + 云端响应"的模式，通过GitHub实现版本管理和消息推送。

## 系统架构

```
客户端程序 (CAD工具包)
    ↓ HTTP请求
GitHub仓库
    ├── version.json (版本信息)
    ├── notifications.json (通知消息)
    └── Releases (发布文件)
    ↓ HTTP响应
客户端程序接收并处理
```

## 核心组件

### 1. UpdateManager (更新管理器)

主要功能:
- 检查更新
- 下载更新
- 获取通知
- 管理配置

### 2. UpdateChecker (更新检查线程)

- 从GitHub获取最新版本信息
- 比较版本号
- 触发更新提示

### 3. NotificationFetcher (通知获取线程)

- 从GitHub获取通知列表
- 解析通知内容
- 显示通知消息

## 工作流程

### 启动时自动检查

```
程序启动
    ↓
延迟3秒
    ↓
检查上次检查时间
    ↓
距离上次检查 < 24小时? → 跳过检查
    ↓ 否
连接GitHub API
    ↓
获取version.json
    ↓
比较版本号
    ↓
有新版本? → 显示更新提示
    ↓ 否
静默完成
```

### 手动检查更新

```
用户点击"检查更新"
    ↓
显示"正在检查..."对话框
    ↓
连接GitHub API
    ↓
获取version.json
    ↓
比较版本号
    ↓
有新版本? → 显示更新详情对话框
    ↓ 否
显示"已是最新版本"
```

### 查看通知

```
用户点击"查看通知"
    ↓
显示"正在获取..."对话框
    ↓
连接GitHub API
    ↓
获取notifications.json
    ↓
解析通知列表
    ↓
显示通知对话框
```

## 配置文件

### version.json

存储在GitHub仓库根目录，包含版本信息:

```json
{
  "version": "1.0.0",
  "description": "更新说明...",
  "release_date": "2026-03-04",
  "download_url": "https://github.com/user/repo/releases/latest",
  "min_version": "1.0.0"
}
```

字段说明:
- `version`: 最新版本号
- `description`: 更新说明（支持Markdown）
- `release_date`: 发布日期
- `download_url`: 下载地址
- `min_version`: 最低兼容版本

### notifications.json

存储在GitHub仓库根目录，包含通知列表:

```json
{
  "notifications": [
    {
      "id": "1",
      "title": "通知标题",
      "content": "通知内容",
      "date": "2026-03-04",
      "type": "info",
      "priority": "normal"
    }
  ]
}
```

字段说明:
- `id`: 通知唯一标识
- `title`: 通知标题
- `content`: 通知内容
- `date`: 发布日期
- `type`: 类型 (info/warning/update/error)
- `priority`: 优先级 (low/normal/high)

## API端点

### 获取版本信息

**方法1: GitHub Releases API**
```
GET https://api.github.com/repos/{owner}/{repo}/releases/latest
```

返回最新Release信息，包括版本号、说明、下载链接等。

**方法2: 直接获取version.json**
```
GET https://raw.githubusercontent.com/{owner}/{repo}/main/version.json
```

返回version.json文件内容。

### 获取通知

```
GET https://raw.githubusercontent.com/{owner}/{repo}/main/notifications.json
```

返回notifications.json文件内容。

## 集成到现有程序

### 步骤1: 导入模块

```python
from update_manager import integrate_update_manager, CURRENT_VERSION
from PyQt5.QtCore import QTimer
```

### 步骤2: 在主窗口初始化时集成

```python
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # ... 现有代码 ...
        
        # 集成更新管理器
        integrate_update_manager(self)
        
        # 启动时自动检查更新
        QTimer.singleShot(3000, self.check_updates_on_startup)
```

### 步骤3: 实现自动检查方法

```python
def check_updates_on_startup(self):
    """启动时检查更新"""
    from update_manager import UpdateManager
    from datetime import datetime, timedelta
    from PyQt5.QtWidgets import QMessageBox
    
    # 检查上次检查时间
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

## 发布新版本流程

### 1. 更新版本号

编辑 `update_manager.py`:
```python
CURRENT_VERSION = "1.0.1"  # 更新版本号
```

### 2. 更新版本信息

编辑 `version.json`:
```json
{
  "version": "1.0.1",
  "description": "v1.0.1 更新内容:\n- 修复XXX问题\n- 新增XXX功能",
  "release_date": "2026-03-05"
}
```

### 3. 添加通知（可选）

编辑 `notifications.json`:
```json
{
  "notifications": [
    {
      "id": "3",
      "title": "v1.0.1 发布",
      "content": "新版本已发布，包含重要更新...",
      "date": "2026-03-05",
      "type": "update",
      "priority": "high"
    }
  ]
}
```

### 4. 提交并推送

```bash
git add .
git commit -m "Release v1.0.1"
git push origin main
```

### 5. 创建Release

```bash
git tag v1.0.1
git push origin v1.0.1
```

或在GitHub网页上创建Release。

## 用户体验

### 首次启动

1. 程序启动
2. 延迟3秒后开始检查更新
3. 如果有新版本，弹出提示框
4. 用户可选择查看详情或稍后提醒

### 日常使用

1. 每24小时自动检查一次
2. 用户可随时手动检查
3. 通知会在查看时实时获取

### 更新流程

1. 发现新版本
2. 查看更新说明
3. 点击"前往下载"
4. 浏览器打开GitHub Release页面
5. 下载新版本
6. 手动安装

## 安全性

### 数据传输

- 使用HTTPS加密传输
- 不传输用户隐私数据
- 仅读取公开的GitHub仓库信息

### 版本验证

- 比较版本号确保更新方向正确
- 支持最低版本检查
- 防止降级安装

### 错误处理

- 网络错误静默失败
- 不影响程序正常使用
- 记录错误日志便于调试

## 性能优化

### 异步检查

- 使用QThread避免阻塞UI
- 超时设置防止长时间等待
- 进度提示改善用户体验

### 缓存策略

- 记录上次检查时间
- 24小时内不重复检查
- 减少不必要的网络请求

### 资源占用

- 延迟启动避免影响程序启动速度
- 按需加载减少内存占用
- 请求超时控制避免资源浪费

## 故障排除

### 检查更新失败

可能原因:
1. 网络连接问题
2. GitHub服务不可用
3. 配置错误

解决方法:
1. 检查网络连接
2. 稍后重试
3. 查看错误日志

### 无法获取通知

可能原因:
1. notifications.json文件不存在
2. JSON格式错误
3. 网络问题

解决方法:
1. 确认文件已推送到GitHub
2. 验证JSON格式
3. 检查网络连接

### 版本号比较错误

可能原因:
1. 版本号格式不规范
2. version.json格式错误

解决方法:
1. 使用标准版本号格式 (x.y.z)
2. 验证JSON格式

## 最佳实践

### 版本号规范

使用语义化版本号:
- 主版本号.次版本号.修订号
- 例如: 1.0.0, 1.2.3, 2.0.0

### 更新说明

- 清晰描述更新内容
- 使用列表格式
- 突出重要变更

### 通知管理

- 及时清理过期通知
- 重要通知设置高优先级
- 内容简洁明了

### 发布频率

- 重大更新: 新主版本
- 功能更新: 新次版本
- 问题修复: 新修订号
- 建议每1-2周发布一次更新

## 扩展功能

### 自动下载

可以扩展UpdateDownloader实现自动下载:

```python
def download_and_install(self, version_info):
    """下载并安装更新"""
    download_url = version_info.get('download_url')
    self.update_manager.download_update(
        download_url,
        'CAD工具包.exe',
        callback_complete=self.on_download_complete
    )
```

### 增量更新

实现差异更新减少下载大小:

```python
def check_incremental_update(self):
    """检查增量更新"""
    # 获取当前版本和目标版本的差异
    # 仅下载变更的文件
    pass
```

### 更新统计

收集更新统计信息:

```python
def report_update_stats(self):
    """上报更新统计"""
    # 匿名统计更新成功率
    # 帮助改进更新体验
    pass
```

## 总结

更新系统采用简单可靠的"客户端请求 + 云端响应"模式，通过GitHub实现:

- ✓ 零服务器成本
- ✓ 高可用性
- ✓ 易于维护
- ✓ 安全可靠
- ✓ 用户体验好

适合中小型桌面应用的更新需求。
