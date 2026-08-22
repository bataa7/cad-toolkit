# -*- mode: python ; coding: utf-8 -*-
"""
CAD工具包 —— 文件夹模式（onedir）打包配置
入口：cad_toolkit_gui.py
输出：dist/CAD工具包/CAD工具包.exe

依据《快速打包指南.txt》的"文件夹模式"：
  - onedir（启动最快，1-2 秒）
  - 仅打包 GUI 实际运行时所需的本地模块与数据文件
  - 排除大量测试/调试脚本，避免体积膨胀
"""

import os

block_cipher = None

# 运行时随 exe 分发的数据文件：(源路径, 目标目录)
datas = [
    # 消息推送 / 更新系统读取的配置缓存（缺失时 GUI 仍可降级运行，但带上更稳）
    ('notifications.json', '.'),
    ('notifications_cache.json', '.'),
    ('version.json', '.'),
    # 界面样式资源（checkbox 图标等，ui_styles.resource_path 引用）
    ('resources', 'resources'),
]

# GUI 运行时通过 import 或 try/except 加载的本地模块
# （PyInstaller 静态分析能抓到大部分，这里显式列出保证不漏）
hiddenimports = [
    'BOM', 'BOM.bom_searcher',
    'notification_system', 'update_system', 'update_manager',
    'system_config', 'ui_styles',
    'dxf_dwg_converter', 'block_finder', 'block_creator',
    'export_blocks', 'cad_merge', 'auto_nesting', 'text_processor',
    'excel', 'excel_reader', 'cad_reader', 'analyze_dxf',
    'version_checker',
    # 第三方库的常见子模块（pandas/ezdxf/openpyxl 的部分子模块易被遗漏）
    'pandas', 'openpyxl', 'ezdxf', 'comtypes', 'comtypes.client', 'comtypes.gen',
    'pypinyin', 'pypinyin.style', 'requests', 'flask',
]

# 排除与 GUI 无关的大型库，减小体积
excludes = [
    'matplotlib', 'scipy', 'numpy.distutils', 'numpy.testing',
    'numpy.f2py', 'pytest', 'IPython', 'notebook', 'jupyter',
    'tkinter', 'pydoc',
    # 注意：不可排除 unittest —— ezdxf → pyparsing.testing 导入时需要它
    # 本仓库的调试/测试脚本不打包
    'test_block_filter', 'test_block_finder', 'test_block_finder_consistency',
    'test_block_finder_unicode', 'test_block_creator_cleanup', 'test_dxf_text',
    'test_excel_stats', 'test_import', 'test_incremental_update_flow', 'test_integration',
    'test_notification_widget', 'test_server', 'test_solid_edge_nesting_worker',
    'test_todo_server', 'test_unicode_decoding', 'test_unicode_fix',
    'test_unicode_handling', 'test_update_download_ssl', 'test_update_system',
    'simple_test', 'debug_block_search', 'debug_excel_extraction', 'debug_material_ids',
    'debug_specific_ids', 'debug_text_encoding', 'debug_unicode_decoding',
    'demo_update_system', 'diagnose', 'diagnose_refs', 'setup_github',
    'check_excel_rows', 'clean_broken_refs', 'clear_update_settings',
    'find_duplicate_files', 'find_duplicates', 'generate_block_report',
    'normalize_blocks', 'normalize_blocks_v2', 'read_excel', 'repair_refs',
    'build_incremental_update', 'integrate_update', 'integrate_update_example',
    'integration_example', 'installer_config',
]

a = Analysis(
    ['cad_toolkit_gui.py'],
    pathex=[os.path.abspath(os.path.dirname(SPEC))],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# 文件夹模式（onedir=True）
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='CAD工具包',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,           # 文件夹模式无需 UPX，启动更快
    console=False,        # 不显示控制台窗口（windowed 子系统）；如需查看启动日志改 True
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    a.zipfiles,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='CAD工具包',
)
