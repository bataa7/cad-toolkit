# CAD工具包网站

这是CAD工具包的官方下载和介绍网站。

## 文件结构

```
website/
├── index.html                      # 主页面
├── style.css                       # 样式文件
├── CAD工具包.exe                   # 程序安装包
├── CAD工具包使用说明.pdf           # 使用说明文档
├── CAD工具包功能模块说明.pdf       # 功能模块文档
├── 启动网站.bat                    # 本地服务器启动脚本
├── 直接打开网站.bat                # 直接在浏览器打开
└── README.md                       # 说明文档
```

## 快速开始（本地部署）

### 方法1：直接打开（推荐）

双击 `直接打开网站.bat` 文件，网站将在默认浏览器中打开。

注意：此方式下载功能可能受浏览器安全限制。

### 方法2：使用本地服务器（推荐用于测试下载）

1. 确保已安装Python 3
2. 双击 `启动网站.bat` 文件
3. 在浏览器访问 `http://localhost:8000`
4. 按 Ctrl+C 停止服务器

此方式可以正常测试下载功能。

## 在线部署方法

### 部署到GitHub Pages

1. 在GitHub创建新仓库
2. 将website文件夹内容推送到仓库
3. 在仓库设置中启用GitHub Pages
4. 选择主分支作为源
5. 网站将自动发布

### 部署到Netlify

1. 在GitHub创建新仓库
2. 点击"New site from Git"或直接拖拽website文件夹
3. 网站将自动部署并获得免费域名

### 部署到Vercel

1. 注册Netlify账号
2. 导入GitHub仓库或直接上传文件夹
3. 自动部署完成

## 需要修改的内容

在正式部署前，请修改以下内容：

1. **下载链接**：将 `index.html` 中的下载链接改为实际的程序下载地址
   ```html
   <a href="你的下载链接" class="btn btn-download" download>下载 CAD工具包</a>
   ```

2. **文档链接**：如果要提供在线文档，修改文档下载链接
   ```html
   <a href="你的文档链接" class="doc-link">下载使用说明</a>
   ```

3. **联系方式**：在footer或about部分添加联系方式（可选）

## 自定义

### 修改颜色主题

在 `style.css` 中修改以下变量：

- 主色调：`#667eea` 和 `#764ba2`（渐变色）
- 强调色：`#2563eb`（按钮和链接）
- 成功色：`#10b981`（勾选标记）

### 添加更多内容

可以在 `index.html` 中添加：
- 用户评价/案例
- 视频教程
- 常见问题FAQ
- 更新日志
- 联系表单

## 优化建议

1. **添加图标**：在 `<head>` 中添加favicon
   ```html
   <link rel="icon" href="favicon.ico" type="image/x-icon">
   ```

2. **添加截图**：在功能介绍部分添加软件截图

3. **SEO优化**：添加meta标签
   ```html
   <meta name="description" content="CAD工具包 - 专业的DXF文件批量处理工具">
   <meta name="keywords" content="CAD,DXF,批量处理,块管理,自动排版">
   ```

4. **添加统计**：集成Google Analytics或其他统计工具

5. **添加社交分享**：添加分享到社交媒体的按钮

## 技术栈

- HTML5
- CSS3
- 响应式设计（支持移动端）
- 无需JavaScript（纯静态页面）

## 浏览器兼容性

支持所有现代浏览器：
- Chrome/Edge (最新版)
- Firefox (最新版)
- Safari (最新版)
- 移动端浏览器

## 许可

根据项目需要添加相应的许可证信息。
