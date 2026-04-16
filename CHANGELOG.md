# 更新日志

所有重要的项目变更都会记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [未发布]

### 计划中
- 自动下载和安装更新
- 增量更新支持
- 多语言界面
- 离线模式

## [3.8.3] - 2026-04-16

### 新增
- 集成独立 `BOM` 工具到主程序，新增“BOM搜索汇总”页面
- 新增 v3.8.3 版本公告，提示 BOM 功能接入与升级方式

### 改进
- 在线更新元数据补充完整安装包信息，旧版本程序可在软件内检查更新后启动新版安装包升级
- 安装包输出名统一为 `CADToolkit_Setup_v3.8.3.exe`，便于程序内更新与 GitHub 直链分发

### 验证
- 通过 `python -m unittest discover -s tests -v` 验证 BOM 搜索逻辑
- 通过 `pytest test_incremental_update_flow.py` 验证增量更新与完整安装包升级脚本

## [3.8.1] - 2026-03-07

### 修复
- 🐛 修复块筛寻与合并页的布局重复挂载问题，消除 `QLayout::addChildLayout` 警告
- 🐛 修复更新检查在 GitHub Releases 请求失败时未回退的问题，确保继续尝试 version.json

### 安全
- 🔒 通知与更新请求默认启用 SSL 证书校验，降低中间人风险

### 验证
- ✅ 通过 `python -m unittest discover -p "test_*.py"` 回归测试
- ✅ 通过 `python test_update_system.py` 更新链路测试
- ✅ 通过 `python diagnose.py` 主程序诊断

## [1.0.0] - 2026-03-04

### 新增
- ✨ 自动更新检查系统
  - 启动时自动检查更新
  - 手动检查更新功能
  - 版本比较算法
  - 更新提示对话框
  
- 📢 消息通知系统
  - 实时获取通知
  - 多种通知类型支持
  - 优先级管理
  - 通知历史查看

- 🔄 GitHub集成
  - 基于GitHub的版本管理
  - 使用GitHub Releases发布
  - 通过GitHub API获取更新信息
  - 零服务器成本

- 📝 完整文档
  - README.md - 项目说明
  - QUICKSTART.md - 快速开始指南
  - DEPLOYMENT.md - 详细部署指南
  - UPDATE_SYSTEM_GUIDE.md - 更新系统使用指南
  - IMPLEMENTATION_SUMMARY.md - 实现总结
  - PROJECT_STRUCTURE.md - 项目结构说明

- 🛠️ 工具脚本
  - setup_github.py - GitHub配置助手
  - test_update_system.py - 测试脚本
  - integrate_update_example.py - 集成示例
  - 自动生成部署脚本

- ⚙️ GitHub Actions
  - 自动构建工作流
  - 自动创建Release
  - 自动上传构建产物

### 改进
- 📦 更新依赖列表，添加 requests>=2.25.0
- 🔒 添加 .gitignore 文件
- 📄 添加 MIT License

### 技术细节
- 使用 PyQt5 QThread 实现异步更新检查
- 采用"客户端请求 + 云端响应"架构
- 支持版本号语义化比较
- 24小时检查间隔，避免频繁请求
- 10秒请求超时，优化用户体验

## [0.9.0] - 之前版本

### 功能
- CAD块批量导出
- CAD文件读取和分析
- CAD块创建
- Excel数据处理
- 自动排版功能

---

## 版本说明

### 版本号格式
- 主版本号.次版本号.修订号 (例如: 1.0.0)

### 版本类型
- **主版本号**: 不兼容的API修改
- **次版本号**: 向下兼容的功能性新增
- **修订号**: 向下兼容的问题修正

### 标签说明
- ✨ 新功能
- 🐛 问题修复
- 📝 文档更新
- 🔄 重构
- ⚡ 性能优化
- 🔒 安全修复
- 📦 依赖更新
- 🛠️ 工具改进
- ⚙️ 配置变更
- 📢 通知/公告

## 如何贡献

发现问题或有改进建议？
1. 在GitHub上提交Issue
2. Fork仓库并创建Pull Request
3. 参与讨论和代码审查

## 支持

- GitHub Issues: https://github.com/your-username/cad-toolkit/issues
- 文档: 查看项目根目录的各个.md文件
