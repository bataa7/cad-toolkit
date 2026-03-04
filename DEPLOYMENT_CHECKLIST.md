# 部署检查清单

使用此清单确保正确部署CAD工具包到GitHub。

## 部署前检查

### 环境准备
- [ ] Python 3.8+ 已安装
- [ ] Git 已安装并配置
- [ ] GitHub账号已创建
- [ ] 网络连接正常

### 依赖安装
- [ ] 运行 `pip install -r requirements.txt`
- [ ] 确认所有依赖安装成功
- [ ] 测试导入关键模块（PyQt5, requests, ezdxf）

### 配置检查
- [ ] 运行 `python setup_github.py` 配置GitHub信息
- [ ] 确认 `update_manager.py` 中的 GITHUB_OWNER 已更新
- [ ] 确认 `update_manager.py` 中的 GITHUB_REPO 已更新
- [ ] 检查 `version.json` 格式正确
- [ ] 检查 `notifications.json` 格式正确

### 文件检查
- [ ] 所有新增文件已创建
- [ ] `.gitignore` 文件存在
- [ ] `LICENSE` 文件存在
- [ ] `README.md` 内容完整

## GitHub仓库创建

### 创建仓库
- [ ] 访问 https://github.com/new
- [ ] 填写仓库名称（与配置一致）
- [ ] 选择 Public（或Private，需配置访问令牌）
- [ ] 不要初始化README、.gitignore或License（本地已有）
- [ ] 点击 "Create repository"
- [ ] 复制仓库URL

### 仓库设置（可选）
- [ ] 添加仓库描述
- [ ] 添加主题标签
- [ ] 设置仓库主页
- [ ] 配置GitHub Pages（如需要）

## 代码推送

### Git初始化
- [ ] 运行 `git init`
- [ ] 运行 `git add .`
- [ ] 运行 `git commit -m "Initial commit: CAD工具包 v1.0.0"`
- [ ] 检查提交内容是否正确

### 添加远程仓库
- [ ] 运行 `git remote add origin <仓库URL>`
- [ ] 运行 `git remote -v` 确认远程仓库配置

### 推送代码
- [ ] 运行 `git branch -M main`
- [ ] 运行 `git push -u origin main`
- [ ] 确认推送成功
- [ ] 在GitHub上查看文件是否正确上传

### 创建版本标签
- [ ] 运行 `git tag v1.0.0`
- [ ] 运行 `git push origin v1.0.0`
- [ ] 在GitHub上查看Tags页面

## 功能测试

### 本地测试
- [ ] 运行 `python test_update_system.py`
- [ ] 确认所有测试通过
- [ ] 运行 `python integrate_update_example.py`
- [ ] 测试更新检查功能
- [ ] 测试通知获取功能

### GitHub集成测试
- [ ] 访问 `https://raw.githubusercontent.com/<用户名>/<仓库名>/main/version.json`
- [ ] 确认可以访问version.json
- [ ] 访问 `https://raw.githubusercontent.com/<用户名>/<仓库名>/main/notifications.json`
- [ ] 确认可以访问notifications.json
- [ ] 在程序中手动检查更新
- [ ] 确认能正确获取版本信息

### Release创建（可选）
- [ ] 在GitHub上创建第一个Release
- [ ] 标签选择 v1.0.0
- [ ] 填写Release标题和说明
- [ ] 上传可执行文件（如果已构建）
- [ ] 发布Release

## 主程序集成

### 代码集成
- [ ] 在 `cad_toolkit_gui.py` 中导入更新管理器
- [ ] 在 MainWindow.__init__ 中调用 integrate_update_manager
- [ ] 添加 check_updates_on_startup 方法
- [ ] 测试启动时自动检查功能

### UI测试
- [ ] 启动主程序
- [ ] 检查"帮助"菜单是否有"检查更新"选项
- [ ] 检查"帮助"菜单是否有"查看通知"选项
- [ ] 点击"检查更新"测试功能
- [ ] 点击"查看通知"测试功能

### 用户体验测试
- [ ] 测试启动延迟（3秒后检查）
- [ ] 测试24小时检查间隔
- [ ] 测试网络错误处理
- [ ] 测试更新提示对话框
- [ ] 测试通知显示对话框

## 文档完善

### 文档检查
- [ ] README.md 中的链接已更新
- [ ] DEPLOYMENT.md 中的示例已更新
- [ ] 所有文档中的用户名/仓库名已替换
- [ ] 文档格式正确，无错别字

### 截图和示例
- [ ] 添加程序截图到README（可选）
- [ ] 添加更新对话框截图（可选）
- [ ] 录制演示视频（可选）

## GitHub Actions（可选）

### 工作流配置
- [ ] 检查 `.github/workflows/release.yml` 文件
- [ ] 确认构建命令正确
- [ ] 确认Python版本配置
- [ ] 测试工作流（推送标签触发）

### 构建测试
- [ ] 推送新标签触发构建
- [ ] 查看Actions运行日志
- [ ] 确认构建成功
- [ ] 检查Release是否自动创建
- [ ] 下载并测试构建的可执行文件

## 发布后检查

### 功能验证
- [ ] 从GitHub下载最新版本
- [ ] 安装并运行程序
- [ ] 测试所有核心功能
- [ ] 测试更新检查功能
- [ ] 测试通知功能

### 用户反馈
- [ ] 邀请测试用户试用
- [ ] 收集反馈意见
- [ ] 记录发现的问题
- [ ] 规划改进计划

### 监控和维护
- [ ] 监控GitHub Issues
- [ ] 检查更新检查日志
- [ ] 统计下载次数
- [ ] 定期更新通知

## 版本更新流程

### 准备新版本
- [ ] 更新 `update_manager.py` 中的 CURRENT_VERSION
- [ ] 更新 `version.json` 中的版本信息
- [ ] 更新 `CHANGELOG.md` 记录变更
- [ ] 添加新通知到 `notifications.json`（可选）

### 发布新版本
- [ ] 提交所有更改
- [ ] 创建新的版本标签
- [ ] 推送到GitHub
- [ ] 创建Release（手动或自动）
- [ ] 通知用户更新

### 发布后验证
- [ ] 旧版本用户能收到更新提示
- [ ] 新版本信息显示正确
- [ ] 下载链接有效
- [ ] 更新说明清晰

## 常见问题处理

### 推送失败
- [ ] 检查网络连接
- [ ] 检查GitHub认证
- [ ] 检查远程仓库URL
- [ ] 尝试使用HTTPS或SSH

### 更新检查失败
- [ ] 检查GitHub配置
- [ ] 检查文件路径
- [ ] 检查JSON格式
- [ ] 检查网络连接

### 构建失败
- [ ] 检查依赖列表
- [ ] 检查PyInstaller配置
- [ ] 查看构建日志
- [ ] 本地测试构建

## 安全检查

### 代码安全
- [ ] 不包含敏感信息（密码、令牌）
- [ ] 不包含个人数据
- [ ] 依赖库无已知漏洞
- [ ] 代码经过审查

### 数据安全
- [ ] 不收集用户隐私数据
- [ ] 使用HTTPS传输
- [ ] 验证下载文件完整性
- [ ] 遵循数据保护法规

## 最终确认

### 部署完成
- [ ] 所有检查项已完成
- [ ] 功能测试通过
- [ ] 文档完整准确
- [ ] 用户可以正常使用

### 后续计划
- [ ] 制定维护计划
- [ ] 规划下一版本功能
- [ ] 建立用户支持渠道
- [ ] 持续改进和优化

---

## 快速检查命令

```bash
# 测试更新系统
python test_update_system.py

# 运行演示程序
python integrate_update_example.py

# 检查Git状态
git status

# 查看远程仓库
git remote -v

# 查看标签
git tag

# 测试网络连接
curl https://api.github.com

# 验证JSON格式
python -m json.tool version.json
python -m json.tool notifications.json
```

## 获取帮助

遇到问题？
1. 查看 DEPLOYMENT.md 详细说明
2. 运行 test_update_system.py 诊断问题
3. 查看 UPDATE_SYSTEM_GUIDE.md 了解原理
4. 在GitHub提交Issue寻求帮助

---

**检查清单版本:** 1.0.0  
**最后更新:** 2026-03-04
