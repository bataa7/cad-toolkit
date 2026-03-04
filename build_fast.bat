@echo off
chcp 65001 >nul
echo ========================================
echo CAD工具包 快速打包脚本
echo ========================================
echo.
echo 请选择打包模式：
echo 1. 文件夹模式（启动最快，推荐日常使用）
echo 2. 单文件模式（便于分发给客户）
echo 3. 清理构建文件
echo 4. 退出
echo.
set /p choice=请输入选项 (1/2/3/4): 

if "%choice%"=="1" goto folder_mode
if "%choice%"=="2" goto single_mode
if "%choice%"=="3" goto clean
if "%choice%"=="4" exit /b
echo 无效选项
pause
exit /b

:folder_mode
echo.
echo ========================================
echo 文件夹模式打包
echo ========================================
echo 优点：启动速度最快（1-2秒）
echo 缺点：生成多个文件
echo 位置：dist\CAD工具包\ 文件夹
echo ========================================
echo.
echo 正在打包，请稍候...
pyinstaller --clean --noconfirm CAD工具包_文件夹模式.spec
if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo 打包成功！
    echo ========================================
    echo 程序位于: dist\CAD工具包\CAD工具包.exe
    echo.
    echo 提示：可以将整个 dist\CAD工具包 文件夹复制到其他位置使用
    echo ========================================
) else (
    echo.
    echo ========================================
    echo 打包失败！请检查错误信息
    echo ========================================
)
pause
exit /b

:single_mode
echo.
echo ========================================
echo 单文件模式打包
echo ========================================
echo 优点：只有一个exe文件，便于分发
echo 缺点：启动稍慢（3-5秒）
echo 位置：dist\CAD工具包.exe
echo ========================================
echo.
echo 正在打包，请稍候...
pyinstaller --clean --noconfirm CAD工具包_优化.spec
if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo 打包成功！
    echo ========================================
    echo 程序位于: dist\CAD工具包.exe
    echo.
    echo 提示：可以直接将 CAD工具包.exe 发送给客户
    echo ========================================
) else (
    echo.
    echo ========================================
    echo 打包失败！请检查错误信息
    echo ========================================
)
pause
exit /b

:clean
echo.
echo ========================================
echo 清理构建文件
echo ========================================
if exist build (
    rmdir /s /q build
    echo 已删除 build 文件夹
)
if exist dist (
    rmdir /s /q dist
    echo 已删除 dist 文件夹
)
del /q *.spec~ 2>nul
echo.
echo 清理完成！
echo ========================================
pause
exit /b
