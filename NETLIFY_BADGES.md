# Netlify徽章和链接

部署成功后，可以在README.md中添加以下徽章和链接。

## 📛 徽章代码

### Netlify状态徽章

```markdown
[![Netlify Status](https://api.netlify.com/api/v1/badges/YOUR-SITE-ID/deploy-status)](https://app.netlify.com/sites/YOUR-SITE-NAME/deploys)
```

**获取方式:**
1. 访问Netlify控制面板
2. 进入你的站点设置
3. 在 "Site information" 中找到 "Status badge"
4. 复制Markdown代码

### 网站链接徽章

```markdown
[![Website](https://img.shields.io/website?url=https%3A%2F%2Fyour-site.netlify.app)](https://your-site.netlify.app)
```

### 版本徽章

```markdown
[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/bataa7/cad-toolkit/releases)
```

### 许可证徽章

```markdown
[![License](https://img.shields.io/badge/license-MIT-green.svg)](https://github.com/bataa7/cad-toolkit/blob/main/LICENSE)
```

## 📝 更新README.md

在README.md顶部添加：

```markdown
# CAD工具包

[![Netlify Status](https://api.netlify.com/api/v1/badges/YOUR-SITE-ID/deploy-status)](https://app.netlify.com/sites/YOUR-SITE-NAME/deploys)
[![Website](https://img.shields.io/website?url=https%3A%2F%2Fyour-site.netlify.app)](https://your-site.netlify.app)
[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/bataa7/cad-toolkit/releases)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

> 功能强大的CAD文件处理工具

🌐 **官方网站**: [https://your-site.netlify.app](https://your-site.netlify.app)

## 快速链接

- 📥 [下载最新版本](https://your-site.netlify.app/download)
- 📖 [在线文档](https://your-site.netlify.app)
- 🐛 [问题反馈](https://github.com/bataa7/cad-toolkit/issues)
- 💬 [讨论区](https://github.com/bataa7/cad-toolkit/discussions)
```

## 🔗 快捷链接

部署后，你可以使用以下短链接：

| 短链接 | 目标 | 用途 |
|--------|------|------|
| `your-site.netlify.app/download` | GitHub Releases | 下载最新版本 |
| `your-site.netlify.app/github` | GitHub仓库 | 访问源码 |
| `your-site.netlify.app/docs` | README.md | 查看文档 |
| `your-site.netlify.app/issues` | GitHub Issues | 提交问题 |
| `your-site.netlify.app/quickstart` | QUICKSTART.md | 快速开始 |

## 📊 分析代码

### Google Analytics

在 `docs/index.html` 的 `</head>` 前添加：

```html
<!-- Google Analytics -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-XXXXXXXXXX');
</script>
```

### Plausible Analytics

```html
<script defer data-domain="your-site.netlify.app" src="https://plausible.io/js/script.js"></script>
```

## 🎨 自定义域名配置

### 添加自定义域名

1. 在Netlify控制面板中:
   - Site settings → Domain management
   - Add custom domain

2. 配置DNS记录:

**使用CNAME（推荐）:**
```
Type: CNAME
Name: cad-toolkit (或你想要的子域名)
Value: your-site.netlify.app
```

**使用A记录（根域名）:**
```
Type: A
Name: @
Value: 75.2.60.5
```

### 更新README中的链接

域名配置后，更新所有链接：

```markdown
🌐 **官方网站**: [https://cad-toolkit.yourdomain.com](https://cad-toolkit.yourdomain.com)
```

## 📱 社交媒体卡片

### Open Graph标签

在 `docs/index.html` 的 `<head>` 中添加：

```html
<!-- Open Graph / Facebook -->
<meta property="og:type" content="website">
<meta property="og:url" content="https://your-site.netlify.app/">
<meta property="og:title" content="CAD工具包 - 专业的CAD文件处理工具">
<meta property="og:description" content="功能强大的CAD文件处理工具，支持块导出、文件读取、自动更新">
<meta property="og:image" content="https://your-site.netlify.app/preview.png">

<!-- Twitter -->
<meta property="twitter:card" content="summary_large_image">
<meta property="twitter:url" content="https://your-site.netlify.app/">
<meta property="twitter:title" content="CAD工具包 - 专业的CAD文件处理工具">
<meta property="twitter:description" content="功能强大的CAD文件处理工具，支持块导出、文件读取、自动更新">
<meta property="twitter:image" content="https://your-site.netlify.app/preview.png">
```

## 🖼️ 预览图片

创建一个预览图片 `docs/preview.png` (1200x630px)，用于社交媒体分享。

## 📈 SEO优化

### 添加sitemap.xml

在 `docs/sitemap.xml`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://your-site.netlify.app/</loc>
    <lastmod>2026-03-04</lastmod>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
  </url>
</urlset>
```

### 添加robots.txt

在 `docs/robots.txt`:

```
User-agent: *
Allow: /

Sitemap: https://your-site.netlify.app/sitemap.xml
```

## 🔔 部署通知

### Slack通知

1. 在Netlify控制面板:
   - Site settings → Build & deploy → Deploy notifications
   - Add notification → Slack

2. 配置Slack webhook URL

### Email通知

在同一位置配置Email通知，接收部署状态更新。

## 📊 示例README

完整的README.md示例：

```markdown
# CAD工具包

[![Netlify Status](https://api.netlify.com/api/v1/badges/YOUR-SITE-ID/deploy-status)](https://app.netlify.com/sites/YOUR-SITE-NAME/deploys)
[![Website](https://img.shields.io/website?url=https%3A%2F%2Fyour-site.netlify.app)](https://your-site.netlify.app)
[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/bataa7/cad-toolkit/releases)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![GitHub stars](https://img.shields.io/github/stars/bataa7/cad-toolkit?style=social)](https://github.com/bataa7/cad-toolkit/stargazers)

> 功能强大的CAD文件处理工具

🌐 **官方网站**: [https://your-site.netlify.app](https://your-site.netlify.app)

## ✨ 特性

- 📦 块批量导出
- 📖 CAD文件读取
- 🔨 CAD块创建
- 📊 Excel数据处理
- 🔄 自动更新检查
- 📢 消息通知系统

## 🚀 快速开始

### 下载安装

访问 [官方网站](https://your-site.netlify.app) 或直接 [下载最新版本](https://your-site.netlify.app/download)

### 从源码运行

\`\`\`bash
git clone https://github.com/bataa7/cad-toolkit.git
cd cad-toolkit
pip install -r requirements.txt
python cad_toolkit_gui.py
\`\`\`

## 📚 文档

- [快速开始](https://your-site.netlify.app/quickstart)
- [使用手册](https://your-site.netlify.app/docs)
- [部署指南](https://your-site.netlify.app/deployment)
- [更新日志](https://your-site.netlify.app/changelog)

## 🤝 贡献

欢迎贡献！请查看 [贡献指南](CONTRIBUTING.md)

## 📄 许可证

[MIT License](LICENSE)

## 🔗 链接

- 🌐 [官方网站](https://your-site.netlify.app)
- 📥 [下载](https://your-site.netlify.app/download)
- 📖 [文档](https://your-site.netlify.app/docs)
- 🐛 [问题反馈](https://github.com/bataa7/cad-toolkit/issues)
- 💬 [讨论区](https://github.com/bataa7/cad-toolkit/discussions)

---

使用 ❤️ 和 Python 构建 | [bataa7](https://github.com/bataa7)
```

## 🎉 完成

部署成功后，记得：

1. ✅ 更新README.md添加徽章
2. ✅ 配置自定义域名（可选）
3. ✅ 添加社交媒体标签
4. ✅ 设置分析工具
5. ✅ 配置部署通知

---

**参考文档**: NETLIFY_DEPLOYMENT.md  
**最后更新**: 2026-03-04
