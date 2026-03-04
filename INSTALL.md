# CAD工具包 - 安装指南

## 从GitHub安装

### 方法一：下载可执行文件（推荐给普通用户）

1. 访问项目的GitHub Releases页面：
   ```
   https://github.com/bataa7/cad-toolkit/releases
   ```

2. 下载最新版本的 `CAD工具包.exe` 文件

3. 双击运行即可使用，无需安装Python环境

### 方法二：从源码安装（推荐给开发者）

#### 前置要求

- Python 3.8 或更高版本
- Git

#### 安装步骤

1. **克隆仓库**

   打开命令行（CMD或PowerShell），执行：
   ```bash
   git clone https://github.com/bataa7/cad-toolkit.git
   cd cad-toolkit
   ```

2. **创建虚拟环境（推荐）**

   ```bash
   python -m venv .venv
   ```

3. **激活虚拟环境**

   Windows CMD:
   ```bash
   .venv\Scripts\activate.bat
   ```

   Windows PowerShell:
   ```bash
   .venv\Scripts\Activate.ps1
   ```

   Git Bash:
   ```bash
   source .venv/Scripts/activate
   ```

4. **安装依赖**

   ```bash
   pip install -r requirements.txt
   ```

5. **运行程序**

   ```bash
   python cad_toolkit_gui.py
   ```

### 方法三：直接下载ZIP包

1. 访问项目主页：
   ```
   https://github.com/bataa7/cad-toolkit
   ```

2. 点击绿色的 "Code" 按钮，选择 "Download ZIP"

3. 解压下载的ZIP文件

4. 按照"方法二"的步骤2-5继续操作

## 依赖项说明

程序需要以下Python库：

- **ezdxf** (>=1.1.0) - DXF文件处理
- **PyQt5** (>=5.15.0) - 图形界面
- **pandas** (>=1.0.0) - 数据处理
- **requests** (>=2.25.0) - 网络请求
- **pyautocad** (>=0.2.0) - AutoCAD自动化
- **comtypes** (>=1.1.14) - COM组件支持
- **pypinyin** (>=0.40.0) - 拼音处理
- **flask** (>=3.0.0) - Web服务

## 常见问题

### Q: 提示"找不到Python"

A: 请先安装Python 3.8或更高版本，下载地址：https://www.python.org/downloads/

### Q: pip install失败

A: 尝试使用国内镜像源：
```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### Q: PyQt5安装失败

A: 在Windows上，可能需要安装Visual C++运行库。下载地址：
https://aka.ms/vs/17/release/vc_redist.x64.exe

### Q: 程序无法启动

A: 确保：
1. Python版本正确（3.8+）
2. 所有依赖已正确安装
3. 虚拟环境已激活（如果使用）

### Q: 如何更新到最新版本

**使用可执行文件：**
- 程序会自动检查更新并提示下载

**使用源码：**
```bash
cd cad-toolkit
git pull origin main
pip install -r requirements.txt --upgrade
```

## 验证安装

安装完成后，可以运行以下命令验证：

```bash
python -c "import ezdxf, PyQt5, pandas; print('所有依赖安装成功！')"
```

如果没有报错，说明安装成功。

## 获取帮助

- 查看使用说明：[CAD工具包使用说明.md](CAD工具包使用说明.md)
- 提交问题：https://github.com/bataa7/cad-toolkit/issues
- 查看更新日志：[CHANGELOG.md](CHANGELOG.md)

## 卸载

### 卸载可执行文件版本

直接删除 `CAD工具包.exe` 文件即可

### 卸载源码版本

1. 删除项目文件夹
2. 如果使用了虚拟环境，虚拟环境也会一并删除
