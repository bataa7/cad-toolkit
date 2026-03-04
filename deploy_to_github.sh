#!/bin/bash

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
git remote add origin https://github.com/bataa7/cad-toolkit.git || {
    echo "远程仓库可能已存在，尝试更新..."
    git remote set-url origin https://github.com/bataa7/cad-toolkit.git
}

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
echo "请访问: https://github.com/bataa7/cad-toolkit"
echo
