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
echo [信息] 开始编译安装程序...
echo.

"%INNO_PATH%" "Scripts\setup.iss"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ====================================
    echo [成功] 安装程序编译完成！
    echo ====================================
    echo 输出位置: Output\CAD工具包安装程序_v3.0.exe
    echo.
    start "" "Output"
) else (
    echo.
    echo [错误] 编译失败，错误代码: %ERRORLEVEL%
    echo.
)

pause
