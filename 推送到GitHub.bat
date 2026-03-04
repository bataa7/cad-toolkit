@echo off
chcp 65001 >nul
echo ========================================
echo CAD工具包 - 推送到GitHub
echo ========================================
echo.
echo 请确保你已经在GitHub上创建了仓库:
echo https://github.com/bataa7/cad-toolkit
echo.
echo 按任意键开始推送...
pause >nul
echo.
echo 正在推送到GitHub...
git push -u origin main
echo.
if errorlevel 1 (
    echo ========================================
    echo 推送失败!
    echo ========================================
    echo.
    echo 可能的原因:
    echo 1. 仓库还没有在GitHub上创建
    echo 2. 需要认证（用户名和Personal Access Token）
    echo 3. 网络连接问题
    echo.
    echo 请查看 "GitHub上传步骤.md" 获取详细说明
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo 推送成功!
echo ========================================
echo.
echo 现在创建版本标签...
git tag v1.0.0
git push origin v1.0.0
echo.
if errorlevel 1 (
    echo 标签推送失败，但代码已成功上传
) else (
    echo 标签推送成功!
)
echo.
echo ========================================
echo 完成!
echo ========================================
echo.
echo 访问你的仓库: https://github.com/bataa7/cad-toolkit
echo.
echo 下一步:
echo 1. 在GitHub上创建Release
echo 2. 运行测试: python test_update_system.py
echo 3. 集成到主程序
echo.
pause
