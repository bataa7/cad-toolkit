# 项目结构说明

## 目录结构

```
cad-toolkit/
├── .github/
│   └── workflows/
│       └── release.yml          # GitHub Actions自动构建配置
├── cad/                         # CAD文件目录
├── cad_backup/                  # CAD备份目录
├── build/                       # 构建输出目录
├── .venv/                       # Python虚拟环境
│
├── 核心模块
├── update_manager.py            # ⭐ 更新管理器（新增）
├── cad_toolkit_gui.py           # 主GUI程序
├── cad_toolkit.py               # CAD工具包核心
├── cad_reader.py                # CAD文件读取器
├── block_creator.py             # 块创建器
├── block_finder.py              # 块查找器
├── cad_merge.py                 # CAD合并工具
├── auto_nesting.py              # 自动排版
├── analyze_dxf.py               # DXF分析工具
│
├── 配置文件
├── version.json                 # ⭐ 版本信息（新增）
├── notifications.json           # ⭐ 通知配置（新增）
├── requirements.txt             # Python依赖
├── .gitignore                   # ⭐ Git忽略规则（新增）
│
├── 文档
├── README.md                    # ⭐ 项目说明（新增）
├── QUICKSTART.md                # ⭐ 快速开始（新增）
├── DEPLOYMENT.md                # ⭐ 部署指南（新增）
├── UPDATE_SYSTEM_GUIDE.md       # ⭐ 更新系统指南（新增）
├── IMPLEMENTATION_SUMMARY.md    # ⭐ 实现总结（新增）
├── PROJECT_STRUCTURE.md         # ⭐ 本文件（新增）
├── CAD工具包使用说明.md         # 原有使用说明
├── CAD工具包功能模块说明.md      # 原有功能说明
├── BLOCK_STANDARDS.md           # 块标准说明
│
├── 工具脚本
├── integrate_update_example.py  # ⭐ 集成示例（新增）
├── setup_github.py              # ⭐ GitHub配置助手（新增）
├── test_update_system.py        # ⭐ 测试脚本（新增）
├── deploy_to_github.bat         # ⭐ Windows部署脚本（自动生成）
├── deploy_to_github.sh          # ⭐ Linux/Mac部署脚本（自动生成）
├── excel.py                     # Excel处理工具
├── check_excel_rows.py          # Excel行检查
├── debug_block_search.py        # 块搜索调试
├── debug_excel_extraction.py    # Excel提取调试
├── clean_broken_refs.py         # 清理损坏引用
├── clear_update_settings.py     # 清理更新设置
│
└── 其他文件
    ├── block_resource_list.csv  # 块资源列表
    ├── cad_block_creator.log    # 日志文件
    └── *.spec                   # PyInstaller配置文件
```

## 新增文件说明

### 核心模块

#### update_manager.py
更新管理器主模块，包含:
- `UpdateManager`: 更新管理器主类
- `UpdateChecker`: 更新检查线程
- `UpdateDownloader`: 更新下载线程
- `NotificationFetcher`: 通知获取线程
- `integrate_update_manager()`: 集成函数

**关键功能:**
- 自动检查更新
- 版本比较
- 下载管理
- 通知获取

### 配置文件

#### version.json
版本信息配置文件，存储在GitHub仓库中。

**字段说明:**
```json
{
  "version": "1.0.0",           // 版本号
  "description": "更新说明",     // 更新内容描述
  "release_date": "2026-03-04", // 发布日期
  "download_url": "下载地址",    // 下载链接
  "min_version": "1.0.0"        // 最低兼容版本
}
```

#### notifications.json
通知配置文件，存储在GitHub仓库中。

**字段说明:**
```json
{
  "notifications": [
    {
      "id": "1",                    // 通知ID
      "title": "通知标题",           // 标题
      "content": "通知内容",         // 内容
      "date": "2026-03-04",         // 日期
      "type": "info",               // 类型
      "priority": "normal"          // 优先级
    }
  ]
}
```

**通知类型:**
- `info`: 一般信息
- `warning`: 警告
- `update`: 更新通知
- `error`: 错误提示

**优先级:**
- `low`: 低优先级
- `normal`: 普通
- `high`: 高优先级

#### .gitignore
Git忽略规则，排除不需要提交的文件:
- Python缓存文件
- 虚拟环境
- 构建输出
- 临时文件
- 日志文件
- 用户配置

### 文档

#### README.md
项目主文档，包含:
- 项目介绍
- 功能特性
- 安装说明
- 使用指南
- 更新系统说明

#### QUICKSTART.md
快速开始指南，5分钟快速部署:
1. 安装依赖
2. 配置GitHub
3. 创建仓库
4. 推送代码
5. 测试功能

#### DEPLOYMENT.md
详细部署指南，包含:
- 完整部署步骤
- 配置说明
- 发布流程
- 故障排除
- 高级配置

#### UPDATE_SYSTEM_GUIDE.md
更新系统使用指南，包含:
- 系统架构
- 工作流程
- API说明
- 集成方法
- 最佳实践

#### IMPLEMENTATION_SUMMARY.md
实现总结文档，包含:
- 项目概述
- 已创建文件列表
- 核心功能说明
- 技术架构
- 快速开始

#### PROJECT_STRUCTURE.md
本文件，项目结构说明。

### 工具脚本

#### integrate_update_example.py
集成示例和演示程序:
- 集成步骤说明
- 示例代码
- 演示窗口
- 功能测试

**运行方式:**
```bash
python integrate_update_example.py
```

#### setup_github.py
GitHub配置助手:
- 交互式配置
- 自动更新配置文件
- 生成部署脚本
- 检查Git状态

**运行方式:**
```bash
python setup_github.py
```

#### test_update_system.py
更新系统测试脚本:
- 版本比较测试
- 配置检查
- 文件格式验证
- 网络连接测试
- 实际功能测试

**运行方式:**
```bash
python test_update_system.py
```

#### deploy_to_github.bat / deploy_to_github.sh
自动部署脚本（由setup_github.py生成）:
- 初始化Git仓库
- 添加远程仓库
- 提交并推送代码
- 创建版本标签

**运行方式:**
```bash
# Windows
deploy_to_github.bat

# Linux/Mac
bash deploy_to_github.sh
```

### GitHub配置

#### .github/workflows/release.yml
GitHub Actions工作流配置:
- 自动构建可执行文件
- 创建Release
- 上传构建产物

**触发条件:**
推送版本标签时自动触发，例如:
```bash
git tag v1.0.0
git push origin v1.0.0
```

## 文件依赖关系

```
cad_toolkit_gui.py (主程序)
    ↓ 导入
update_manager.py (更新管理器)
    ↓ 请求
GitHub仓库
    ├── version.json
    └── notifications.json
```

## 数据流

### 更新检查流程

```
用户启动程序
    ↓
MainWindow.__init__()
    ↓
integrate_update_manager()
    ↓
QTimer.singleShot(3000, check_updates_on_startup)
    ↓
UpdateChecker.run()
    ↓
HTTP GET version.json
    ↓
比较版本号
    ↓
显示更新提示（如有新版本）
```

### 通知获取流程

```
用户点击"查看通知"
    ↓
NotificationFetcher.run()
    ↓
HTTP GET notifications.json
    ↓
解析通知列表
    ↓
显示通知对话框
```

## 配置存储

### 用户配置目录

```
~/.cad_toolkit/
└── update_config.json    # 更新配置
    ├── last_check_time   # 上次检查时间
    └── ...               # 其他配置
```

## 构建输出

### PyInstaller构建

```
build/                    # 构建临时文件
dist/                     # 最终可执行文件
    └── CAD工具包.exe
```

## 版本控制

### Git分支策略

- `main`: 主分支，稳定版本
- `develop`: 开发分支（可选）
- `feature/*`: 功能分支（可选）

### 版本标签

- `v1.0.0`: 主版本
- `v1.0.1`: 修订版本
- `v1.1.0`: 次版本

## 开发工作流

### 日常开发

1. 修改代码
2. 本地测试
3. 提交到Git
4. 推送到GitHub

### 发布新版本

1. 更新版本号
2. 更新version.json
3. 更新notifications.json（可选）
4. 提交并推送
5. 创建版本标签
6. GitHub Actions自动构建

## 文件大小参考

- `update_manager.py`: ~15KB
- `version.json`: ~1KB
- `notifications.json`: ~2KB
- `README.md`: ~5KB
- `DEPLOYMENT.md`: ~10KB
- `UPDATE_SYSTEM_GUIDE.md`: ~15KB

## 许可证

所有新增文件遵循项目许可证（MIT License）。

## 维护建议

### 定期维护

- 每周检查GitHub Issues
- 每月更新依赖库
- 每季度审查文档

### 版本发布

- 重大更新: 每3-6个月
- 功能更新: 每1-2个月
- 问题修复: 按需发布

### 文档更新

- 新功能发布时更新文档
- 用户反馈后改进说明
- 定期检查文档准确性

## 相关资源

- GitHub仓库: https://github.com/your-username/cad-toolkit
- 问题追踪: https://github.com/your-username/cad-toolkit/issues
- 发布页面: https://github.com/your-username/cad-toolkit/releases

## 贡献指南

欢迎贡献代码和文档！请参考:
1. Fork仓库
2. 创建功能分支
3. 提交Pull Request
4. 等待审核

---

**最后更新:** 2026-03-04
**文档版本:** 1.0.0
