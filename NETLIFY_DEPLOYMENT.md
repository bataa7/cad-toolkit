# Netlify部署指南

将CAD工具包文档网站部署到Netlify的完整指南。

## 📋 概述

本指南将帮助你将CAD工具包的文档网站部署到Netlify。网站包含：
- 项目介绍和功能展示
- 下载链接和安装说明
- 文档中心和使用指南
- 自动更新的版本信息

## 🎯 部署目标

- **主网站**: 展示项目信息和文档
- **快捷链接**: 提供便捷的下载和文档访问
- **API端点**: 为更新系统提供版本信息

## 📁 文件结构

```
cad-toolkit/
├── docs/
│   ├── index.html          # 主页
│   ├── 404.html            # 404页面
│   └── _redirects          # 重定向规则
├── netlify.toml            # Netlify配置
└── NETLIFY_DEPLOYMENT.md   # 本文件
```

## 🚀 部署步骤

### 方法1: 通过GitHub自动部署（推荐）

#### 步骤1: 推送代码到GitHub

确保你的代码已经推送到GitHub:

```bash
git add .
git commit -m "Add Netlify deployment files"
git push origin main
```

#### 步骤2: 连接Netlify

1. 访问 [Netlify](https://www.netlify.com/)
2. 点击 "Sign up" 或 "Log in"
3. 选择 "GitHub" 登录（推荐）

#### 步骤3: 创建新站点

1. 点击 "Add new site" -> "Import an existing project"
2. 选择 "GitHub"
3. 授权Netlify访问你的GitHub账户
4. 选择 `bataa7/cad-toolkit` 仓库

#### 步骤4: 配置构建设置

Netlify会自动检测 `netlify.toml` 配置文件，你只需确认：

- **Branch to deploy**: `main`
- **Build command**: `echo 'Static site - no build needed'`
- **Publish directory**: `docs`

点击 "Deploy site"

#### 步骤5: 等待部署完成

- 部署通常需要1-2分钟
- 完成后会显示一个临时域名，如: `random-name-123456.netlify.app`

#### 步骤6: 自定义域名（可选）

1. 在站点设置中点击 "Domain settings"
2. 点击 "Add custom domain"
3. 输入你的域名（如: `cad-toolkit.yourdomain.com`）
4. 按照提示配置DNS记录

### 方法2: 通过Netlify CLI部署

#### 步骤1: 安装Netlify CLI

```bash
npm install -g netlify-cli
```

#### 步骤2: 登录Netlify

```bash
netlify login
```

#### 步骤3: 初始化站点

```bash
netlify init
```

按照提示选择：
- Create & configure a new site
- 选择团队
- 输入站点名称（可选）

#### 步骤4: 部署

```bash
netlify deploy --prod
```

### 方法3: 手动拖放部署

1. 访问 [Netlify Drop](https://app.netlify.com/drop)
2. 将 `docs` 文件夹拖放到页面上
3. 等待上传和部署完成

## ⚙️ 配置说明

### netlify.toml

主要配置项：

```toml
[build]
  publish = "docs"              # 发布目录
  command = "echo 'No build'"   # 构建命令

[[redirects]]
  from = "/download"
  to = "https://github.com/bataa7/cad-toolkit/releases/latest"
  status = 302
```

### 重定向规则

在 `docs/_redirects` 文件中定义：

```
/download    https://github.com/bataa7/cad-toolkit/releases/latest    302
/github      https://github.com/bataa7/cad-toolkit                     302
```

使用方式：
- `https://your-site.netlify.app/download` → 跳转到最新版本下载
- `https://your-site.netlify.app/github` → 跳转到GitHub仓库

## 🔧 高级配置

### 自定义域名

1. 在Netlify控制面板中添加自定义域名
2. 配置DNS记录：
   ```
   Type: CNAME
   Name: cad-toolkit (或 @)
   Value: your-site.netlify.app
   ```
3. 等待DNS传播（可能需要几小时）

### HTTPS配置

Netlify自动提供免费的Let's Encrypt SSL证书：
- 自动续期
- 强制HTTPS重定向
- HTTP/2支持

### 环境变量

在Netlify控制面板中设置：
1. Site settings -> Environment variables
2. 添加变量（如果需要）

### 构建钩子

设置自动部署触发器：
1. Site settings -> Build & deploy -> Build hooks
2. 创建新的构建钩子
3. 使用webhook URL触发部署

## 📊 部署后验证

### 检查清单

- [ ] 网站可以正常访问
- [ ] 所有链接正常工作
- [ ] 下载链接指向正确的GitHub Release
- [ ] 404页面正常显示
- [ ] 重定向规则生效
- [ ] HTTPS证书已配置
- [ ] 移动端显示正常

### 测试链接

访问以下URL测试功能：

```
https://your-site.netlify.app/              # 主页
https://your-site.netlify.app/download      # 下载重定向
https://your-site.netlify.app/github        # GitHub重定向
https://your-site.netlify.app/docs          # 文档重定向
https://your-site.netlify.app/nonexistent   # 404页面
```

## 🔄 更新网站

### 自动更新

推送到GitHub后自动部署：

```bash
git add .
git commit -m "Update website"
git push origin main
```

Netlify会自动检测更改并重新部署。

### 手动触发部署

在Netlify控制面板中：
1. Deploys -> Trigger deploy
2. 选择 "Deploy site"

### 回滚部署

如果新版本有问题：
1. Deploys -> 选择之前的部署
2. 点击 "Publish deploy"

## 🎨 自定义网站

### 修改样式

编辑 `docs/index.html` 中的 `<style>` 部分：

```css
/* 修改主题色 */
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);

/* 修改字体 */
font-family: 'Your Font', sans-serif;
```

### 添加新页面

1. 在 `docs/` 目录创建新的HTML文件
2. 更新 `index.html` 中的链接
3. 推送到GitHub

### 添加分析

在 `index.html` 的 `</body>` 前添加：

```html
<!-- Google Analytics -->
<script async src="https://www.googletagmanager.com/gtag/js?id=GA_MEASUREMENT_ID"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'GA_MEASUREMENT_ID');
</script>
```

## 🔍 监控和分析

### Netlify Analytics

启用Netlify Analytics（付费功能）：
1. Site settings -> Analytics
2. Enable analytics
3. 查看访问统计、页面浏览量等

### 免费替代方案

- **Google Analytics**: 详细的访问分析
- **Plausible**: 隐私友好的分析工具
- **Umami**: 开源自托管分析

## 🐛 故障排除

### 问题1: 部署失败

**症状**: 构建过程中出错

**解决方法**:
1. 检查 `netlify.toml` 配置
2. 确认 `docs` 目录存在
3. 查看部署日志获取详细错误

### 问题2: 404错误

**症状**: 访问页面显示404

**解决方法**:
1. 检查文件路径是否正确
2. 确认 `_redirects` 文件配置
3. 清除浏览器缓存

### 问题3: 重定向不工作

**症状**: 快捷链接无法跳转

**解决方法**:
1. 检查 `_redirects` 文件格式
2. 确认 `netlify.toml` 中的重定向规则
3. 等待几分钟让配置生效

### 问题4: HTTPS证书问题

**症状**: 浏览器显示不安全

**解决方法**:
1. 在Netlify控制面板中强制HTTPS
2. 等待证书自动配置（可能需要几分钟）
3. 清除浏览器缓存

## 📈 性能优化

### 启用缓存

在 `netlify.toml` 中配置：

```toml
[[headers]]
  for = "/*.html"
  [headers.values]
    Cache-Control = "public, max-age=3600"
```

### 压缩资源

Netlify自动启用：
- Gzip压缩
- Brotli压缩
- 资源优化

### CDN加速

Netlify自动使用全球CDN：
- 自动分发到全球节点
- 智能路由
- 边缘缓存

## 🔐 安全配置

### 安全头部

在 `netlify.toml` 中已配置：

```toml
[[headers]]
  for = "/*"
  [headers.values]
    X-Frame-Options = "DENY"
    X-XSS-Protection = "1; mode=block"
    X-Content-Type-Options = "nosniff"
```

### 访问控制

设置密码保护（可选）：
1. Site settings -> Access control
2. Enable password protection
3. 设置密码

## 💰 费用说明

### 免费套餐包含

- ✅ 100GB带宽/月
- ✅ 300分钟构建时间/月
- ✅ 自动HTTPS
- ✅ 持续部署
- ✅ 表单处理（100次/月）
- ✅ 无限站点

### 付费功能

- Netlify Analytics: $9/月
- 更多带宽: 按需付费
- 团队协作: $19/月起

对于文档网站，免费套餐完全够用！

## 📞 获取帮助

### 官方资源

- [Netlify文档](https://docs.netlify.com/)
- [Netlify社区](https://answers.netlify.com/)
- [Netlify状态](https://www.netlifystatus.com/)

### 项目资源

- [GitHub Issues](https://github.com/bataa7/cad-toolkit/issues)
- [项目文档](https://github.com/bataa7/cad-toolkit/blob/main/README.md)

## ✅ 部署检查清单

部署前确认：

- [ ] 代码已推送到GitHub
- [ ] `docs/index.html` 文件存在
- [ ] `netlify.toml` 配置正确
- [ ] GitHub链接已更新为正确的仓库地址
- [ ] 所有文档链接有效

部署后验证：

- [ ] 网站可以访问
- [ ] 下载链接正常
- [ ] 重定向工作正常
- [ ] 移动端显示正常
- [ ] HTTPS已启用
- [ ] 404页面正常

## 🎉 完成

恭喜！你的CAD工具包文档网站已成功部署到Netlify！

**下一步:**
1. 分享你的网站链接
2. 在README.md中添加网站徽章
3. 定期更新内容
4. 监控访问统计

---

**部署示例URL**: `https://cad-toolkit.netlify.app`  
**GitHub仓库**: `https://github.com/bataa7/cad-toolkit`  
**最后更新**: 2026-03-04
