@echo off
chcp 65001 >nul
echo ====================================
echo CAD工具包 - 编译安装程序
echo ====================================
echo.

REM 检查Inno Setup是否安装
set "INNO_PATH=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"

if not exist "%INNO_PATH%" (
    echo [错误] 未找到 Inno Setup 编译器
    echo 请确保 Inno Setup 6 已安装在默认路径
    echo 下载地址: https://jrsoftware.org/isdl.php
    echo.
    pause
    exit /b 1
)

echo [信息] 找到 Inno Setup 编译器
echo [INFO] Sync CADToolkit package folder...
echo.

if not exist "..\dist\CADToolkit\CADToolkit.exe" (
    echo [错误] 未找到 ..\dist\CADToolkit\CADToolkit.exe
    echo 请先在项目根目录完成文件夹模式打包
    echo.
    pause
    exit /b 1
)

if exist "Files\CADToolkit" rmdir /s /q "Files\CADToolkit"
xcopy "..\dist\CADToolkit" "Files\CADToolkit\" /e /i /y >nul

if errorlevel 1 (
    echo [错误] 同步 CADToolkit 文件失败
    echo.
    pause
    exit /b 1
)

echo [信息] 开始编译安装程序...
echo.

"%INNO_PATH%" "Scripts\setup.iss"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ====================================
    echo [成功] 安装程序编译完成！
    echo ====================================
    echo 输出位置: Output\CADToolkit安装程序_v3.8.exe
    echo.
    start "" "Output"
) else (
    echo.
    echo [错误] 编译失败，错误代码: %ERRORLEVEL%
    echo.
)

pause
