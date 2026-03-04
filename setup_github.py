"""
GitHub部署配置助手
帮助快速配置GitHub仓库信息
"""
import os
import json
import re


def setup_github_config():
    """配置GitHub仓库信息"""
    print("=" * 60)
    print("CAD工具包 - GitHub配置助手")
    print("=" * 60)
    print()
    
    # 获取用户输入
    print("请输入你的GitHub信息:")
    github_username = input("GitHub用户名: ").strip()
    github_repo = input("仓库名称 (默认: cad-toolkit): ").strip() or "cad-toolkit"
    
    if not github_username:
        print("错误: GitHub用户名不能为空")
        return False
    
    print()
    print(f"配置信息:")
    print(f"  GitHub用户名: {github_username}")
    print(f"  仓库名称: {github_repo}")
    print()
    
    confirm = input("确认配置? (y/n): ").strip().lower()
    if confirm != 'y':
        print("已取消配置")
        return False
    
    # 更新 update_manager.py
    print("\n正在更新 update_manager.py...")
    try:
        update_manager_path = 'update_manager.py'
        if not os.path.exists(update_manager_path):
            print(f"错误: 找不到文件 {update_manager_path}")
            return False
        
        with open(update_manager_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 替换GitHub配置
        content = re.sub(
            r'GITHUB_OWNER = "[^"]*"',
            f'GITHUB_OWNER = "{github_username}"',
            content
        )
        content = re.sub(
            r'GITHUB_REPO = "[^"]*"',
            f'GITHUB_REPO = "{github_repo}"',
            content
        )
        
        with open(update_manager_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✓ update_manager.py 已更新")
    except Exception as e:
        print(f"✗ 更新 update_manager.py 失败: {e}")
        return False
    
    # 更新 version.json
    print("正在更新 version.json...")
    try:
        version_path = 'version.json'
        if os.path.exists(version_path):
            with open(version_path, 'r', encoding='utf-8') as f:
                version_data = json.load(f)
            
            version_data['download_url'] = f"https://github.com/{github_username}/{github_repo}/releases/latest"
            
            with open(version_path, 'w', encoding='utf-8') as f:
                json.dump(version_data, f, ensure_ascii=False, indent=2)
            
            print("✓ version.json 已更新")
        else:
            print("⚠ version.json 不存在，跳过")
    except Exception as e:
        print(f"✗ 更新 version.json 失败: {e}")
    
    # 更新 README.md
    print("正在更新 README.md...")
    try:
        readme_path = 'README.md'
        if os.path.exists(readme_path):
            with open(readme_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 替换GitHub链接
            content = re.sub(
                r'https://github\.com/[^/]+/[^/\)]+',
                f'https://github.com/{github_username}/{github_repo}',
                content
            )
            
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print("✓ README.md 已更新")
        else:
            print("⚠ README.md 不存在，跳过")
    except Exception as e:
        print(f"✗ 更新 README.md 失败: {e}")
    
    print()
    print("=" * 60)
    print("配置完成!")
    print("=" * 60)
    print()
    print("下一步:")
    print("1. 在GitHub上创建仓库: https://github.com/new")
    print(f"   仓库名称: {github_repo}")
    print()
    print("2. 初始化Git并推送代码:")
    print("   git init")
    print("   git add .")
    print('   git commit -m "Initial commit"')
    print(f"   git remote add origin https://github.com/{github_username}/{github_repo}.git")
    print("   git branch -M main")
    print("   git push -u origin main")
    print()
    print("3. 创建第一个Release:")
    print("   git tag v1.0.0")
    print("   git push origin v1.0.0")
    print()
    print("详细说明请查看 DEPLOYMENT.md")
    print()
    
    return True


def check_git_status():
    """检查Git状态"""
    print("\n检查Git状态...")
    
    if not os.path.exists('.git'):
        print("⚠ Git仓库未初始化")
        print("  运行: git init")
        return False
    
    print("✓ Git仓库已初始化")
    
    # 检查是否有远程仓库
    try:
        import subprocess
        result = subprocess.run(
            ['git', 'remote', '-v'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0 and result.stdout.strip():
            print("✓ 已配置远程仓库:")
            for line in result.stdout.strip().split('\n'):
                print(f"  {line}")
        else:
            print("⚠ 未配置远程仓库")
            print("  运行: git remote add origin <仓库URL>")
    except Exception as e:
        print(f"⚠ 无法检查远程仓库: {e}")
    
    return True


def create_git_commands_file():
    """创建Git命令脚本"""
    print("\n是否生成Git命令脚本? (y/n): ", end='')
    if input().strip().lower() != 'y':
        return
    
    # 读取配置
    try:
        with open('update_manager.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        owner_match = re.search(r'GITHUB_OWNER = "([^"]*)"', content)
        repo_match = re.search(r'GITHUB_REPO = "([^"]*)"', content)
        
        if owner_match and repo_match:
            github_username = owner_match.group(1)
            github_repo = repo_match.group(1)
            
            # 生成Windows批处理脚本
            bat_content = f"""@echo off
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
git remote add origin https://github.com/{github_username}/{github_repo}.git
if errorlevel 1 (
    echo 远程仓库可能已存在，尝试更新...
    git remote set-url origin https://github.com/{github_username}/{github_repo}.git
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
echo 请访问: https://github.com/{github_username}/{github_repo}
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
"""
            
            with open('deploy_to_github.bat', 'w', encoding='utf-8') as f:
                f.write(bat_content)
            
            print("✓ 已生成 deploy_to_github.bat")
            print("  双击运行该脚本即可自动部署到GitHub")
            
            # 生成Linux/Mac脚本
            sh_content = f"""#!/bin/bash

echo "========================================"
echo "CAD工具包 - Git部署脚本"
echo "========================================"
echo

echo "步骤1: 初始化Git仓库"
git init || exit 1

echo
echo "步骤2: 添加所有文件"
git add . || exit 1

echo
echo "步骤3: 提交"
git commit -m "Initial commit: CAD工具包 v1.0.0" || exit 1

echo
echo "步骤4: 添加远程仓库"
git remote add origin https://github.com/{github_username}/{github_repo}.git || {{
    echo "远程仓库可能已存在，尝试更新..."
    git remote set-url origin https://github.com/{github_username}/{github_repo}.git
}}

echo
echo "步骤5: 推送到GitHub"
git branch -M main
git push -u origin main || exit 1

echo
echo "步骤6: 创建并推送标签"
git tag v1.0.0
git push origin v1.0.0 || exit 1

echo
echo "========================================"
echo "部署完成!"
echo "========================================"
echo
echo "请访问: https://github.com/{github_username}/{github_repo}"
echo
"""
            
            with open('deploy_to_github.sh', 'w', encoding='utf-8', newline='\n') as f:
                f.write(sh_content)
            
            # 设置执行权限（仅在Unix系统上）
            try:
                os.chmod('deploy_to_github.sh', 0o755)
            except:
                pass
            
            print("✓ 已生成 deploy_to_github.sh")
            print("  运行: bash deploy_to_github.sh")
            
    except Exception as e:
        print(f"✗ 生成脚本失败: {e}")


if __name__ == '__main__':
    try:
        # 配置GitHub信息
        if setup_github_config():
            # 检查Git状态
            check_git_status()
            
            # 生成部署脚本
            create_git_commands_file()
        
    except KeyboardInterrupt:
        print("\n\n已取消配置")
    except Exception as e:
        print(f"\n错误: {e}")
