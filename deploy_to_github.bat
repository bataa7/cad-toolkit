@echo off
echo ========================================
echo CAD工具包 - Git部署脚本
echo ========================================
echo.

echo 步骤1: 初始化Git仓库
git init
if errorlevel 1 goto error

echo.
echo 步骤2: 添加所有文件
git add .
if errorlevel 1 goto error

echo.
echo 步骤3: 提交
git commit -m "Initial commit: CAD工具包 v1.0.0"
if errorlevel 1 goto error

echo.
echo 步骤4: 添加远程仓库
git remote add origin https://github.com/bataa7/cad-toolkit.git
if errorlevel 1 (
    echo 远程仓库可能已存在，尝试更新...
    git remote set-url origin https://github.com/bataa7/cad-toolkit.git
)

echo.
echo 步骤5: 推送到GitHub
git branch -M main
git push -u origin main
if errorlevel 1 goto error

echo.
echo 步骤6: 创建并推送标签
git tag v1.0.0
git push origin v1.0.0
if errorlevel 1 goto error

echo.
echo ========================================
echo 部署完成!
echo ========================================
echo.
echo 请访问: https://github.com/bataa7/cad-toolkit
echo.
pause
exit /b 0

:error
echo.
echo ========================================
echo 部署失败!
echo ========================================
echo.
pause
exit /b 1
