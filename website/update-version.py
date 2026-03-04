#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
版本更新管理工具
用于更新version.json文件，发布新版本
"""

import json
import os
from datetime import datetime

def load_version_data():
    """加载版本数据"""
    with open('version.json', 'r', encoding='utf-8') as f:
        return json.load(f)

def save_version_data(data):
    """保存版本数据"""
    with open('version.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def add_new_version():
    """添加新版本"""
    data = load_version_data()
    
    print("=" * 50)
    print("CAD工具包 - 版本发布工具")
    print("=" * 50)
    print()
    
    # 输入新版本信息
    print(f"当前最新版本: {data['latest_version']}")
    new_version = input("请输入新版本号 (例如: 3.1.0): ").strip()
    
    if not new_version:
        print("版本号不能为空！")
        return
    
    # 版本类型
    print("\n版本类型:")
    print("1. major - 重大更新")
    print("2. minor - 功能更新")
    print("3. patch - 修复更新")
    version_type_choice = input("请选择版本类型 (1/2/3): ").strip()
    
    version_type_map = {
        '1': 'major',
        '2': 'minor',
        '3': 'patch'
    }
    version_type = version_type_map.get(version_type_choice, 'minor')
    
    # 更新内容
    print("\n请输入更新内容 (每行一条，输入空行结束):")
    changes = []
    while True:
        change = input("- ").strip()
        if not change:
            break
        changes.append(change)
    
    if not changes:
        print("至少需要一条更新内容！")
        return
    
    # 文件大小
    exe_path = 'CAD工具包.exe'
    if os.path.exists(exe_path):
        file_size = os.path.getsize(exe_path)
    else:
        file_size_mb = input(f"\n未找到{exe_path}，请手动输入文件大小(MB): ").strip()
        try:
            file_size = int(float(file_size_mb) * 1024 * 1024)
        except:
            file_size = data['file_size']
    
    # 创建新版本记录
    new_version_record = {
        "version": new_version,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "type": version_type,
        "changes": changes,
        "download_count": 0
    }
    
    # 更新数据
    data['latest_version'] = new_version
    data['release_date'] = new_version_record['date']
    data['file_size'] = str(file_size)
    
    # 将新版本插入到changelog开头
    data['changelog'].insert(0, new_version_record)
    
    # 保存
    save_version_data(data)
    
    print("\n" + "=" * 50)
    print("✓ 版本发布成功！")
    print("=" * 50)
    print(f"版本号: {new_version}")
    print(f"发布日期: {new_version_record['date']}")
    print(f"版本类型: {version_type}")
    print(f"更新内容: {len(changes)} 条")
    print(f"文件大小: {file_size / 1024 / 1024:.1f} MB")
    print()
    print("请将更新后的version.json文件部署到服务器")

def update_download_count():
    """更新下载次数"""
    data = load_version_data()
    
    print("=" * 50)
    print("更新下载次数")
    print("=" * 50)
    print()
    
    for i, version in enumerate(data['changelog']):
        print(f"{i+1}. v{version['version']} - 当前下载: {version['download_count']}")
    
    choice = input("\n请选择要更新的版本 (输入序号): ").strip()
    
    try:
        index = int(choice) - 1
        if 0 <= index < len(data['changelog']):
            new_count = input(f"请输入新的下载次数 (当前: {data['changelog'][index]['download_count']}): ").strip()
            data['changelog'][index]['download_count'] = int(new_count)
            save_version_data(data)
            print("\n✓ 更新成功！")
        else:
            print("无效的选择！")
    except:
        print("输入错误！")

def view_versions():
    """查看所有版本"""
    data = load_version_data()
    
    print("=" * 50)
    print("版本历史")
    print("=" * 50)
    print()
    print(f"最新版本: {data['latest_version']}")
    print(f"发布日期: {data['release_date']}")
    print()
    
    for version in data['changelog']:
        print(f"\nv{version['version']} ({version['date']}) - {version['type']}")
        print(f"下载次数: {version['download_count']}")
        print("更新内容:")
        for change in version['changes']:
            print(f"  - {change}")

def main():
    """主函数"""
    while True:
        print("\n" + "=" * 50)
        print("CAD工具包 - 版本管理工具")
        print("=" * 50)
        print("1. 发布新版本")
        print("2. 更新下载次数")
        print("3. 查看版本历史")
        print("4. 退出")
        print()
        
        choice = input("请选择操作 (1-4): ").strip()
        
        if choice == '1':
            add_new_version()
        elif choice == '2':
            update_download_count()
        elif choice == '3':
            view_versions()
        elif choice == '4':
            print("\n再见！")
            break
        else:
            print("\n无效的选择，请重试")

if __name__ == '__main__':
    main()
