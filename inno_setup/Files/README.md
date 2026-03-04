# CAD工具包

一个功能强大的CAD文件处理工具，提供块导出、文件读取、块创建等功能。

## 功能特性

- **块批量导出**: 将DXF文件中的块导出为单独的文件
- **CAD文件读取**: 读取和分析CAD文件内容
- **CAD块创建**: 批量创建CAD块
- **Excel数据处理**: 处理和验证Excel数据
- **自动更新检查**: 自动检查并提示新版本
- **消息通知系统**: 接收重要通知和更新信息

## 安装

### 从源码运行

1. 克隆仓库:
```bash
git clone https://github.com/bataa7/cad-toolkit.git
cd cad-toolkit
```

2. 创建虚拟环境（推荐）:
```bash
python -m venv .venv
.venv\Scripts\activate  # Windows
```

3. 安装依赖:
```bash
pip install -r requirements.txt
```

4. 运行程序:
```bash
python cad_toolkit_gui.py
```

### 从GitHub下载可执行文件

访问 [Releases](https://github.com/bataa7/cad-toolkit/releases) 页面下载最新的可执行文件。

## 依赖项

- Python 3.8+
- PyQt5 >= 5.15.0
- ezdxf >= 1.1.0
- pandas >= 1.0.0
- requests >= 2.25.0

完整依赖列表请查看 `requirements.txt`

## 更新系统

程序内置自动更新检查功能:

1. 启动时自动检查更新（可在设置中关闭）
2. 手动检查: 菜单栏 -> 帮助 -> 检查更新
3. 查看通知: 菜单栏 -> 帮助 -> 查看通知

## 开发

### 构建可执行文件

```bash
pyinstaller --name="CAD工具包" --windowed --onefile cad_toolkit_gui.py
```

### 发布新版本

1. 更新 `update_manager.py` 中的 `CURRENT_VERSION`
2. 更新 `version.json` 中的版本信息
3. 提交更改并创建标签:
```bash
git add .
git commit -m "Release v1.0.1"
git tag v1.0.1
git push origin main --tags
```

4. GitHub Actions 会自动构建并创建 Release

## 配置

### GitHub配置

编辑 `update_manager.py` 中的配置:

```python
GITHUB_OWNER = "your-username"  # 你的GitHub用户名
GITHUB_REPO = "cad-toolkit"     # 仓库名
```

### 通知配置

编辑 `notifications.json` 添加新通知:

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

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！

## 联系方式

如有问题，请在 GitHub 上提交 Issue。
