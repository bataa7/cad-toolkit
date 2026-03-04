# CAD工具包 - Inno Setup 安装程序

## 文件夹结构

```
inno_setup/
├── Scripts/          # 安装脚本
│   └── setup.iss    # Inno Setup 配置文件
├── Files/           # 需要打包的文件
│   ├── CAD工具包.exe
│   ├── 启动主程序.bat
│   ├── README.md
│   └── CAD工具包使用说明.md
├── Output/          # 生成的安装程序输出目录
└── 编译安装程序.bat  # 一键编译脚本
```

## 使用步骤

### 1. 安装 Inno Setup

下载并安装 Inno Setup 6：
- 官方网站: https://jrsoftware.org/isdl.php
- 选择 "Inno Setup 6.x.x" 版本
- 使用默认安装路径

### 2. 准备文件

确保以下文件已复制到 `Files/` 目录：
- ✓ CAD工具包.exe
- ✓ 启动主程序.bat
- ✓ README.md
- ✓ CAD工具包使用说明.md

### 3. 编译安装程序

方法一：使用批处理脚本（推荐）
```bash
双击运行: 编译安装程序.bat
```

方法二：手动编译
1. 打开 Inno Setup Compiler
2. 打开文件: `Scripts/setup.iss`
3. 点击菜单: Build > Compile
4. 等待编译完成

### 4. 获取安装程序

编译成功后，在 `Output/` 目录下会生成：
```
CAD工具包安装程序_v3.0.exe
```

## 安装程序特性

- 支持中文界面
- 自动创建开始菜单项
- 可选创建桌面快捷方式
- 包含卸载程序
- 需要管理员权限
- 使用 LZMA 压缩算法

## 自定义配置

编辑 `Scripts/setup.iss` 文件可以修改：
- 应用程序名称和版本
- 默认安装路径
- 快捷方式设置
- 添加更多文件
- 修改安装界面

## 常见问题

Q: 编译失败怎么办？
A: 检查 Inno Setup 是否正确安装，路径是否为默认路径

Q: 如何添加更多文件？
A: 将文件复制到 Files/ 目录，然后在 setup.iss 的 [Files] 部分添加对应条目

Q: 如何修改版本号？
A: 编辑 setup.iss 文件中的 `#define MyAppVersion` 行

## 技术支持

如有问题，请查看：
- Inno Setup 官方文档: https://jrsoftware.org/ishelp/
- CAD工具包使用说明.md
