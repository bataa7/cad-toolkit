@echo off
chcp 65001 >nul
echo ========================================
echo CAD工具包 - Netlify部署助手
echo ========================================
echo.

REM 检查是否安装了Netlify CLI
where netlify >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ 未检测到Netlify CLI
    echo.
    echo 请先安装Netlify CLI:
    echo   npm install -g netlify-cli
    echo.
    echo 或者使用GitHub自动部署（推荐）
    echo 查看 NETLIFY_DEPLOYMENT.md 获取详细说明
    echo.
    pause
    exit /b 1
)

echo ✅ Netlify CLI已安装
echo.

REM 检查是否已登录
netlify status >nul 2>nul
if %errorlevel% neq 0 (
    echo 📝 需要登录Netlify...
    echo.
    netlify login
    if %errorlevel% neq 0 (
        echo ❌ 登录失败
        pause
        exit /b 1
    )
)

echo ✅ 已登录Netlify
echo.

REM 检查是否已初始化
if not exist ".netlify" (
    echo 🔧 初始化Netlify站点...
    echo.
    netlify init
    if %errorlevel% neq 0 (
        echo ❌ 初始化失败
        pause
        exit /b 1
    )
)

echo.
echo ========================================
echo 开始部署到Netlify
echo ========================================
echo.

REM 部署到生产环境
netlify deploy --prod

if %errorlevel% neq 0 (
    echo.
    echo ========================================
    echo ❌ 部署失败
    echo ========================================
    echo.
    echo 请检查:
    echo 1. 网络连接是否正常
    echo 2. docs目录是否存在
    echo 3. netlify.toml配置是否正确
    echo.
    echo 查看 NETLIFY_DEPLOYMENT.md 获取帮助
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo ✅ 部署成功!
echo ========================================
echo.
echo 你的网站已成功部署到Netlify
echo.
echo 下一步:
echo 1. 访问你的网站查看效果
echo 2. 配置自定义域名（可选）
echo 3. 启用HTTPS（自动）
echo.
echo 查看部署详情:
netlify open
echo.
pause
