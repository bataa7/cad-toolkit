# Windows + .xls + Excel COM 专项验收前置条件

本文档用于补充 `.xls` 老格式 Excel 文件在 **Windows + Excel COM** 场景下的专项验收说明。该场景是项目真实交付中最容易踩坑的路径，因为它和普通 `.xlsx` 路径不同，额外依赖本机的 Excel 桌面环境与 COM 组件。

---

## 1. 适用场景

当满足以下任一条件时，建议阅读并执行本文档中的专项验收：

- 客户现场仍大量使用 `.xls` 文件
- 交付要求明确提出“必须支持 `.xls`”
- 现场机器不是开发机，需要重新确认 Excel COM 能否正常工作
- 虽然 `.xlsx` 路径已通过，但 `.xls` 文件在现场出现无法读取、被跳过或结果缺失的问题

> 如果项目只使用 `.xlsx/.xlsm/.xltx/.xltm`，则无需执行本专项验收，可直接按常规运行手册完成交付。

---

## 2. 与普通 `.xlsx` 路径的核心差异

普通 `.xlsx` 路径与 `.xls` 路径最大的差异在于：

- `.xlsx/.xlsm/.xltx/.xltm`：由 `openpyxl` 直接读取
- `.xls`：程序不会直接解析老格式，而是先尝试调用 **Windows 本机 Excel COM**，把 `.xls` 转换为临时 `.xlsx`，再继续处理

也就是说，`.xls` 路径比 `.xlsx` 多依赖以下能力：

1. 当前机器必须是 **Windows**
2. 当前机器通常需要安装 **桌面版 Microsoft Excel**
3. Python 侧需要可用的 **pywin32 / win32com.client**
4. Excel COM 必须能被正常创建与调用

因此，`.xlsx` 能正常运行，并不代表 `.xls` 一定能正常运行。

---

## 3. 所需本机环境

### 3.1 必须满足的环境

建议专项验收机器满足以下条件：

- 操作系统：Windows 10 / Windows 11
- Python：3.11 / 3.12 / 3.13
- 已安装项目依赖：`requirements.txt`
- Python 中可导入 `win32com.client`
- 本机可正常启动桌面版 Excel
- 当前账号具有启动本机 Office 应用的权限

### 3.2 强烈建议具备的环境

- 安装 **Microsoft Excel 桌面版**（Microsoft 365 / Office 2019 / Office 2021 等）
- 使用本地登录用户执行验收，而不是受限服务账号
- 机器允许首次启动 Excel 并完成初始化配置
- 机器不是纯服务器精简环境

### 3.3 不推荐直接作为专项验收机的环境

以下环境不建议用来认定 `.xls` 兼容已经通过：

- GitHub Actions 托管 `windows-latest`
- 未安装桌面 Excel 的 Windows 机器
- 仅有 WPS、但未验证 COM 兼容性的机器
- 远程受限账号 / 无桌面会话环境
- 刚安装 Office 但 Excel 从未成功手动打开过的机器

---

## 4. Excel / COM 依赖前提

### 4.1 Python 依赖前提

先执行：

```powershell
python -m pip install -r requirements.txt
python -c "import win32com.client; print('pywin32 ok')"
```

如果第二条命令失败，则说明 Python 无法使用 Excel COM，`.xls` 路径无法通过。

### 4.2 Excel 应用前提

请先手工确认：

1. 本机可以正常打开 Excel
2. 双击任意一个 `.xls` 文件，Excel 能正常打开
3. 第一次启动 Excel 时若有许可证、隐私、加载项、宏安全提示，需要先完成初始化
4. Excel 不应停在未关闭的报错弹窗、恢复窗口、首次引导页上

### 4.3 COM 调用前提

程序内部在读取 `.xls` 时，会尝试执行以下动作：

- 创建 Excel COM 实例（`DispatchEx("Excel.Application")`）
- 打开 `.xls`
- 另存为临时 `.xlsx`
- 关闭工作簿和 Excel 进程

若以上任一步失败，程序就无法读取 `.xls`。

---

## 5. 推荐的专项验收前置检查

在正式跑程序前，建议按顺序执行以下检查。

### 步骤 1：确认 Python 与依赖

```powershell
python --version
python -m pip install -r requirements.txt
python -c "import win32com.client; print('pywin32 ok')"
```

### 步骤 2：确认 Excel 本机可用

人工执行：

1. 手工打开 Excel
2. 新建并关闭一个空白工作簿
3. 手工打开一个真实 `.xls` 文件
4. 确认没有弹出阻塞式对话框（许可证、恢复、加载项报错、兼容性警告等）

### 步骤 3：确认 `.xlsx` 主路径本身已通过

先跑普通验证：

```powershell
verify_windows.bat
```

这样可以先排除 Python 主程序、测试数据、CLI 路径、编码设置等基础问题。

### 步骤 4：准备一份真实 `.xls` 样例

专项验收不要只依赖 `.xlsx` 示例文件，建议准备：

- 至少 1 份真实 `.xls` 待查或 BOM 文件
- 文件中包含业务上实际使用的表头与图号数据
- 文件路径不要过长、不要包含网络盘权限问题

### 步骤 5：执行 `.xls` 专项 CLI 验证

建议优先使用 CLI，而不是 GUI。示例：

```powershell
python bom_searcher.py --input "C:\验收样例\待查.xls" --bom-folder "C:\验收样例\BOM目录" --output "C:\验收样例\artifacts\xls_verify_output.xlsx"
```

### 步骤 6：检查结果与日志

重点检查：

- 是否成功生成输出文件
- 输出文件是否包含 `搜索结果 / 汇总BOM / 搜索明细 / 未找到`
- 日志中是否出现“跳过文件”或“缺少 Excel COM 支持”等提示
- 若 BOM 文件夹中有多个 `.xls` 文件，是否只有部分失败

---

## 6. 推荐验证步骤（最小可执行版）

建议按以下顺序执行，以减少排错成本。

### 方案 A：最小专项验收流程

1. 安装依赖：
   ```powershell
   python -m pip install -r requirements.txt
   ```
2. 检查 pywin32：
   ```powershell
   python -c "import win32com.client; print('pywin32 ok')"
   ```
3. 手工打开一次 Excel 和一份 `.xls`
4. 执行 `.xls` CLI 命令
5. 检查输出文件和日志

### 方案 B：推荐正式交付流程

1. 先执行普通验证：
   ```powershell
   verify_windows.bat
   ```
2. 再执行 `.xls` 专项 CLI 验证
3. 如客户实际使用 GUI，再补做一次 GUI 人工操作演示
4. 如客户现场有多种 `.xls` 模板，至少抽样验证 2~3 份

---

## 7. 常见失败模式

以下是 `.xls + Excel COM` 场景的高频失败模式。

### 7.1 缺少 pywin32

现象：

- `python -c "import win32com.client"` 失败
- 或程序日志显示缺少 Excel COM 支持

原因：

- 未安装 `pywin32`
- 当前 Python 环境与安装依赖的环境不是同一个

建议处理：

```powershell
python -m pip install -r requirements.txt
python -c "import win32com.client; print('pywin32 ok')"
```

### 7.2 没有安装桌面版 Excel

现象：

- `.xlsx` 正常，`.xls` 不正常
- Excel COM 创建失败
- 程序跳过 `.xls`

原因：

- 本机没有 Microsoft Excel 桌面版
- 只安装了部分 Office 组件，未安装 Excel

建议处理：

- 安装桌面版 Excel
- 安装后手工打开一次 Excel 完成初始化

### 7.3 Excel 已安装，但首次启动未初始化完成

现象：

- 手工打开 Excel 时弹出许可、隐私、加载项、恢复等窗口
- 程序调用 COM 时卡住、报错或直接失败

原因：

- Excel 首次启动向导/弹窗阻塞了自动化调用

建议处理：

1. 手工启动 Excel
2. 处理所有首次弹窗
3. 打开并关闭一次空白工作簿
4. 再重新执行 `.xls` 验证

### 7.4 使用了受限账号或无桌面会话环境

现象：

- 本机有 Excel，但脚本调用失败
- 远程会话、计划任务或服务账号下异常

原因：

- Excel COM 更适合在有桌面会话、可交互的本地用户环境下工作

建议处理：

- 使用本地登录用户验收
- 避免把 `.xls` 专项验收完全交给后台服务账号

### 7.5 `.xls` 文件本身损坏或需要人工确认

现象：

- 手工打开 `.xls` 时 Excel 先弹出修复或兼容提示
- 程序路径中该文件失败，但其他 `.xls` 正常

原因：

- 文件本身损坏
- 文件需要人工确认才能打开

建议处理：

- 先手工打开并确认该文件可正常读取
- 如 Excel 提示修复，建议修复后另存为 `.xlsx` 再交由程序处理

### 7.6 文件路径/权限问题

现象：

- 某些 `.xls` 文件无法读取
- 网络盘、只读目录、权限不足目录更容易失败

建议处理：

- 优先把验收样例复制到本地磁盘短路径目录
- 避免使用过深目录、特殊权限目录、网络共享路径作为第一轮验收路径

### 7.7 程序本身没问题，但结果被“回扫污染”

现象：

- 第一次跑正常，第二次跑结果异常增多

原因：

- 输出文件又被放回了待扫描 BOM 目录

建议处理：

- 输出写到独立 `artifacts` 目录
- 或使用包含 `搜索结果` / `_` / `result` / `output` 的文件名

---

## 8. 用户排查建议

当用户反馈“.xls 不行，但 .xlsx 可以”时，建议按下面顺序排查：

1. **先确认操作系统**：是否真的是 Windows
2. **确认 Python 依赖**：
   ```powershell
   python -c "import win32com.client; print('pywin32 ok')"
   ```
3. **确认 Excel 本体**：能否手工打开 Excel 和该 `.xls`
4. **确认首次弹窗**：Excel 有没有未处理的许可证/恢复/隐私弹窗
5. **确认运行账号**：是不是本地登录用户，而不是受限账号
6. **确认文件本身**：该 `.xls` 是否损坏、是否需要修复
7. **确认路径权限**：是否放在网络盘、只读目录、路径过长目录
8. **确认输出路径**：是否把输出结果写回待扫描目录，导致误判为读取异常

如果仍无法解决，建议采用以下临时绕行方案：

- 先让用户手工把 `.xls` 转为 `.xlsx`
- 再用普通 `.xlsx` 路径执行程序

这通常是现场最稳妥、成本最低的兜底方案。

---

## 9. 推荐交付口径

对业务方或验收方建议统一说明：

1. 项目对 `.xlsx` 路径支持较稳定，可通过 CI 和一键验证覆盖
2. `.xls` 属于增强兼容路径，依赖 Windows 本机 Excel COM 环境
3. `.xls` 的验收结论必须以 **真实 Windows + Excel 机器实测结果** 为准
4. GitHub 托管 CI 通过，不代表 `.xls` COM 场景必然通过
5. 若现场环境复杂，建议优先将 `.xls` 统一转换为 `.xlsx`

---

## 10. 最小专项验收清单

建议验收人逐项勾选：

- [ ] 当前机器为 Windows
- [ ] 已执行 `python -m pip install -r requirements.txt`
- [ ] `python -c "import win32com.client; print('pywin32 ok')"` 通过
- [ ] 本机已安装桌面版 Excel
- [ ] 已手工打开过 Excel，并完成首次初始化
- [ ] 已手工打开过至少 1 个真实 `.xls` 文件
- [ ] 已执行 `.xls` 专项 CLI 验证
- [ ] 已检查输出文件生成成功
- [ ] 已检查输出文件包含预期工作表
- [ ] 若现场仍不稳定，已验证手工转 `.xlsx` 兜底方案可用

---

## 11. 与主运行手册的关系

建议搭配以下文档一起使用：

- `docs/交付验收与运行手册.md`

使用建议：

- 一般交付：先看主运行手册
- 涉及 `.xls`：再补看本文档
- 现场排障：优先按“用户排查建议”执行

---

**结论**：`.xls` 支持不是单纯的“代码能力”问题，而是“代码 + Windows + Excel + COM + 本机环境”共同决定的交付场景。只有在真实 Windows + 桌面 Excel 环境中完成专项验收，才能对 `.xls` 支持给出可靠结论。
