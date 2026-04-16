# Tkinter 界面实施清单与字段映射

## 1. 文档目标

本文面向 `bom_searcher.py` 的后续开发实现，基于当前 Tkinter 桌面 GUI 现状、`docs/新BOM汇总业务规则梳理.md` 与 `docs/BOM汇总技术方案.md`，整理出一份可直接落地的界面实施清单。

目标是让开发者能够据此完成：
1. `BOMSearcherApp` 的界面重构；
2. “搜索模式 / 新BOM汇总模式”的 Tkinter 交互实现；
3. 输入字段映射、结果预览、导出参数、错误提示的落地；
4. 界面字段与“旧BOM搜刮并汇总成新BOM”业务字段之间的映射。

---

## 2. 当前代码基线

当前 GUI 主要集中在：
- `bom_searcher.py:754-926`：`BOMSearcherApp`
- `bom_searcher.py:702-751`：`run_search()`
- `bom_searcher.py:551-699`：结果写出逻辑
- `bom_searcher.py:291-318`：任务单查询项收集 `collect_queries()`
- `bom_searcher.py:224-244`：表头识别 `detect_header()`

当前界面仅有：
- 待查 Excel 路径
- BOM 文件夹路径
- 输出结果路径
- 开始搜索
- 清空日志
- 文本日志框
- 成功/失败弹窗

这只能支撑“按图号搜索”，不能支撑“按任务单生成新BOM”的输入映射、结果预览、汇总选项和异常管理。

---

## 3. 建议改造范围（bom_searcher.py）

建议优先仍在 `bom_searcher.py` 内完成第一阶段 UI 增强，后续再拆模块。

### 3.1 需要重点改造的方法

#### 现有方法
- `BOMSearcherApp.__init__()`
- `BOMSearcherApp._build_ui()`
- `BOMSearcherApp._path_row()`
- `BOMSearcherApp.start_search()`
- `BOMSearcherApp._search_worker()`
- `BOMSearcherApp._on_search_success()`
- `BOMSearcherApp._on_search_failed()`

#### 建议新增方法
- `_init_state_vars()`
- `_build_mode_panel()`
- `_build_input_panel()`
- `_build_mapping_panel()`
- `_build_option_panel()`
- `_build_action_bar()`
- `_build_result_notebook()`
- `_build_status_panel()`
- `_toggle_mode_fields()`
- `_detect_task_columns()`
- `_load_task_sheets()`
- `_preview_task_items()`
- `_validate_before_run()`
- `_collect_ui_options()`
- `_start_summary()`
- `_summary_worker()`
- `_populate_summary_result()`
- `_populate_detail_result()`
- `_populate_not_found_result()`
- `_populate_exception_result()`
- `_set_running_state()`
- `_show_validation_errors()`
- `_append_error_record()`

### 3.2 布局建议

建议把窗口从当前的简单纵向表单升级为：

1. 顶部：标题 + 运行模式区
2. 左侧：输入区 + 字段映射区 + 汇总/导出选项区
3. 右侧：预览区 + 结果页签区
4. 底部：状态栏 + 日志/错误摘要

### 3.3 窗口建议
- 标题：`BOM 搜索与汇总工具`
- 默认尺寸：`1280x820`
- 最小尺寸：`1100x720`
- 采用：`ttk.PanedWindow + ttk.LabelFrame + ttk.Notebook + ttk.Treeview`

---

## 4. 建议新增/调整的界面区块

## 4.1 运行模式区

### 目的
区分当前是：
- 仅搜索并导出明细；
- 按任务单汇总生成新BOM。

### 建议控件
- `self.run_mode_var = tk.StringVar(value="summary")`
- `self.run_mode_combo = ttk.Combobox(..., values=["search", "summary"], state="readonly")`
- 可展示中文：
  - `search` -> `搜索模式`
  - `summary` -> `新BOM汇总模式`

### 交互
- 切换到 `search`：隐藏“字段映射”“汇总选项”“汇总BOM页签”
- 切换到 `summary`：显示所有高级区块

---

## 4.2 输入区

### 目的
配置任务单来源、BOM 库来源、输出位置。

### 建议子区块
1. 任务单文件
2. 任务单工作表
3. BOM 文件夹
4. 输出结果文件
5. 任务单预览按钮

### 建议控件
- `task_file_var`
- `task_sheet_var`
- `bom_folder_var`
- `output_file_var`
- `task_sheet_combo`
- `preview_task_button`
- `detect_mapping_button`

---

## 4.3 字段映射区

### 目的
把任务单中的列映射到业务字段，而不是完全依赖自动识别。

### 需要映射的任务单字段
- 任务单号（可选）
- 输入序号
- 图号（必填）
- 名称（建议）
- 数量（汇总模式必填）
- 备注（可选）

### 建议控件
每个字段一行：`Label + Combobox + 状态提示 Label`

---

## 4.4 汇总/匹配选项区

### 目的
让“新BOM汇总”的关键业务规则可视化、可配置。

### 建议选项
1. 匹配模式
   - `全部保留并汇总`
   - `仅取优先级最高来源`
2. 汇总主键
   - `物料ID优先`
   - `图号优先`
3. 是否保留父项行
4. 是否保留说明行到明细
5. 是否生成异常报告
6. 是否导出后自动打开文件

---

## 4.5 结果预览区

### 目的
让用户在 GUI 中直接看到结果，而不是只看日志和 Excel 文件。

### 建议采用 `ttk.Notebook`
页签建议：
1. `任务单预览`
2. `汇总BOM`
3. `展开明细`
4. `未找到`
5. `异常报告`
6. `运行日志`

---

## 4.6 状态区

### 目的
反馈执行进度、当前状态、错误数量、输出文件路径。

### 建议控件
- `status_var`
- `progress_var`
- `summary_hint_var`
- `progress_bar`

---

## 5. 控件清单：变量 / 用途 / 校验 / 文案

下表为建议直接在 `BOMSearcherApp` 中新增的状态变量与控件。

| 区块 | 控件属性名 | 变量名 | 类型 | 默认值 | 用途 | 校验规则 | 失败提示文案 |
|---|---|---|---|---|---|---|---|
| 模式区 | `run_mode_combo` | `run_mode_var` | `StringVar` | `summary` | 切换搜索/汇总模式 | 必须为 `search` 或 `summary` | `运行模式无效，请重新选择。` |
| 输入区 | `task_file_entry` | `task_file_var` | `StringVar` | 空 | 任务单 Excel 路径 | 必填；文件必须存在；扩展名必须为受支持 Excel | `请选择任务单 Excel 文件。` |
| 输入区 | `task_sheet_combo` | `task_sheet_var` | `StringVar` | 空 | 指定任务单工作表 | 若任务单有多个工作表，至少选 1 个 | `请选择要处理的任务单工作表。` |
| 输入区 | `bom_folder_entry` | `bom_folder_var` | `StringVar` | 空 | 旧 BOM 目录 | 必填；目录必须存在 | `请选择 BOM 文件夹。` |
| 输入区 | `output_file_entry` | `output_file_var` | `StringVar` | 自动带 `_汇总BOM.xlsx` | 输出结果文件 | 必填；后缀必须为 `.xlsx` | `请选择结果输出路径。` |
| 字段映射区 | `task_no_combo` | `task_no_col_var` | `StringVar` | 空 | 映射任务单号列 | 可空 | 无 |
| 字段映射区 | `sequence_combo` | `sequence_col_var` | `StringVar` | 自动识别 | 映射输入序号列 | 可空但建议存在 | `未指定任务单序号列，将无法生成来源任务序号集合。` |
| 字段映射区 | `drawing_combo` | `drawing_col_var` | `StringVar` | 自动识别 | 映射图号列 | 必填 | `任务单中未识别到“图号”列，请手动指定。` |
| 字段映射区 | `name_combo` | `name_col_var` | `StringVar` | 自动识别 | 映射名称列 | 建议有 | `未指定名称列，匹配歧义时无法辅助判断。` |
| 字段映射区 | `quantity_combo` | `quantity_col_var` | `StringVar` | 自动识别 | 映射数量列 | `summary` 模式必填 | `汇总模式必须指定“数量”列。` |
| 字段映射区 | `remark_combo` | `remark_col_var` | `StringVar` | 空 | 映射备注列 | 可空 | 无 |
| 选项区 | `match_mode_combo` | `match_mode_var` | `StringVar` | `merge_all` | 多来源匹配策略 | 必须为 `merge_all` / `strict_best` | `匹配模式无效。` |
| 选项区 | `dedup_key_combo` | `dedup_key_var` | `StringVar` | `material_id_first` | 汇总主键策略 | 必须为预设值 | `汇总主键策略无效。` |
| 选项区 | `include_parent_check` | `include_parent_var` | `BooleanVar` | `False` | 汇总BOM是否保留父项总成行 | 无 | 无 |
| 选项区 | `include_note_check` | `include_note_var` | `BooleanVar` | `True` | 展开明细是否保留说明行 | 无 | 无 |
| 选项区 | `generate_exception_check` | `generate_exception_var` | `BooleanVar` | `True` | 是否生成异常报告页签/工作表 | 无 | 无 |
| 选项区 | `open_after_export_check` | `open_after_export_var` | `BooleanVar` | `False` | 导出后是否自动打开结果文件 | 无 | 无 |
| 选项区 | `export_summary_check` | `export_summary_var` | `BooleanVar` | `True` | 是否导出汇总BOM | 至少选 1 个导出对象 | `请至少选择一个导出内容。` |
| 选项区 | `export_detail_check` | `export_detail_var` | `BooleanVar` | `True` | 是否导出展开明细 | 至少选 1 个导出对象 | 同上 |
| 选项区 | `export_not_found_check` | `export_not_found_var` | `BooleanVar` | `True` | 是否导出未找到 | 至少选 1 个导出对象 | 同上 |
| 选项区 | `export_exception_check` | `export_exception_var` | `BooleanVar` | `True` | 是否导出异常报告 | 至少选 1 个导出对象 | 同上 |
| 状态区 | `status_label` | `status_var` | `StringVar` | `待执行` | 当前状态提示 | 无 | 无 |
| 状态区 | `summary_hint_label` | `summary_hint_var` | `StringVar` | 空 | 展示命中/未找到/异常摘要 | 无 | 无 |

---

## 6. 推荐控件布局与命名

## 6.1 左侧面板

### A. `输入设置` (`ttk.LabelFrame`)
- `task_file_entry`
- `task_file_button`
- `task_sheet_combo`
- `bom_folder_entry`
- `bom_folder_button`
- `output_file_entry`
- `output_file_button`

### B. `字段映射` (`ttk.LabelFrame`)
- `detect_mapping_button`
- `task_no_combo`
- `sequence_combo`
- `drawing_combo`
- `name_combo`
- `quantity_combo`
- `remark_combo`

### C. `汇总规则` (`ttk.LabelFrame`)
- `match_mode_combo`
- `dedup_key_combo`
- `include_parent_check`
- `include_note_check`
- `generate_exception_check`

### D. `导出设置` (`ttk.LabelFrame`)
- `export_summary_check`
- `export_detail_check`
- `export_not_found_check`
- `export_exception_check`
- `open_after_export_check`

### E. `操作区` (`ttk.Frame`)
- `preview_task_button`
- `validate_button`
- `run_button`
- `clear_result_button`

## 6.2 右侧面板（Notebook）

### 页签 1：`任务单预览`
Treeview：`task_preview_tree`

建议列：
- 输入工作表
- 输入行号
- 任务单号
- 输入序号
- 输入图号
- 输入名称
- 输入数量
- 输入备注
- 识别状态

### 页签 2：`汇总BOM`
Treeview：`summary_tree`

建议列：
- 序号
- 物料ID
- 图号
- 名称
- 厚度
- 材质
- 汇总总数量
- 备注
- 来源父图号集合
- 来源任务单序号集合
- 来源文件集合
- 匹配状态

### 页签 3：`展开明细`
Treeview：`detail_tree`

建议列：
- 输入工作表
- 输入行号
- 输入序号
- 输入图号
- 输入名称
- 输入数量
- 来源文件
- 来源工作表
- 父行号
- 父序号
- 父图号
- 父名称
- 子行号
- 子序号
- 子图号
- 子名称
- 厚度
- 材质
- 原数量
- 原总数量
- 重算总数量
- 备注
- 结果状态
- 行类型

### 页签 4：`未找到`
Treeview：`not_found_tree`

建议列：
- 输入工作表
- 输入行号
- 输入序号
- 输入图号
- 输入名称
- 输入数量
- 原因

### 页签 5：`异常报告`
Treeview：`exception_tree`

建议列：
- 异常级别
- 异常类型
- 输入图号
- 输入名称
- 来源文件
- 来源工作表
- 关联图号
- 提示信息
- 建议处理

### 页签 6：`运行日志`
- `log_text`

---

## 7. 按钮与事件流

## 7.1 按钮清单

| 按钮 | 建议方法名 | 作用 | 成功后动作 |
|---|---|---|---|
| 选择任务单 | `choose_task_file()` | 选择任务单 Excel | 自动填充输出文件名；加载工作表列表 |
| 选择 BOM 文件夹 | `choose_bom_folder()` | 选择旧 BOM 库目录 | 更新状态栏 |
| 选择输出文件 | `choose_output_file()` | 设置导出路径 | 更新状态栏 |
| 识别字段 | `_detect_task_columns()` | 自动识别任务单表头与字段映射 | 填充各映射下拉框；生成识别提示 |
| 预览任务单 | `_preview_task_items()` | 预览输入查询项 | 填充 `task_preview_tree` |
| 校验输入 | `_validate_before_run()` | 做执行前校验 | 输出错误列表或显示“校验通过” |
| 开始执行 | `start_search()` 或 `_start_summary()` | 根据模式开始后台线程 | 禁用按钮、显示进度、清空旧结果 |
| 清空结果 | `_clear_results()` | 清空结果页签数据与状态 | 重置摘要与错误数 |
| 清空日志 | `clear_log()` | 清空日志文本框 | 保留当前结果表 |

## 7.2 推荐事件流（汇总模式）

### Flow A：选择任务单
1. 点击“选择任务单”
2. `choose_task_file()`
3. 自动调用 `_load_task_sheets()`
4. 若 `output_file_var` 为空，自动生成：`任务单文件名_汇总BOM.xlsx`
5. 更新状态：`已加载任务单，等待字段识别`

### Flow B：识别字段
1. 点击“识别字段”
2. `_detect_task_columns()`
3. 读取所选工作表前 30 行
4. 调用现有 `detect_header()` 或其增强版
5. 用 `HEADER_ALIASES` 给 `drawing/name/quantity/sequence/remark` 自动匹配
6. 把结果写入各 `*_col_var`
7. 状态栏显示：
   - `字段识别完成：图号=图号，数量=数量，名称=名称`
   - 或提示缺失字段

### Flow C：预览任务单
1. 点击“预览任务单”
2. `_preview_task_items()`
3. 按当前字段映射抽取输入项
4. 在 `task_preview_tree` 展示前 N 条
5. 若存在空图号/空数量，标红并记入异常列表

### Flow D：执行汇总
1. 点击“开始执行”
2. `_validate_before_run()`
3. 若校验失败：
   - 不启动线程
   - 弹出统一错误摘要
   - 在“异常报告”页签写入校验错误
4. 若校验通过：
   - `_set_running_state(True)`
   - 清空旧结果
   - 启动后台线程 `_summary_worker()`

### Flow E：后台处理
1. 读取任务单输入项
2. 扫描 BOM 文件夹
3. 建立索引
4. 搜索并展开父子项
5. 按汇总规则生成汇总BOM、明细、未找到、异常
6. 导出 Excel
7. 回到主线程更新页签内容与摘要

### Flow F：完成回调
1. `_on_search_success()` / `_on_summary_success()`
2. 填充各 Treeview
3. 状态栏显示：
   - `执行完成：输入 126 条，汇总 438 条，未找到 9 条，异常 4 条`
4. 若 `open_after_export_var=True`，则打开结果文件
5. 若存在跳过文件或异常，自动切到“异常报告”页签

---

## 8. 输入校验规则与错误提示文案

## 8.1 执行前校验

| 校验项 | 条件 | 严重级别 | 建议文案 |
|---|---|---|---|
| 任务单文件为空 | `task_file_var` 为空 | 错误 | `请选择任务单 Excel 文件。` |
| 任务单文件不存在 | 路径不存在 | 错误 | `任务单文件不存在，请重新选择。` |
| 任务单扩展名不支持 | 非 Excel 后缀 | 错误 | `任务单文件格式不支持，仅支持 .xlsx/.xlsm/.xltx/.xltm/.xls。` |
| 工作表未选择 | 多工作表场景下未选 | 错误 | `请选择要处理的任务单工作表。` |
| BOM 文件夹为空 | `bom_folder_var` 为空 | 错误 | `请选择 BOM 文件夹。` |
| BOM 文件夹不存在 | 路径不存在 | 错误 | `BOM 文件夹不存在，请重新选择。` |
| 输出路径为空 | `output_file_var` 为空 | 错误 | `请选择结果输出路径。` |
| 图号列未映射 | `drawing_col_var` 为空 | 错误 | `任务单中未识别到“图号”列，请手动指定。` |
| 汇总模式缺少数量列 | `run_mode=summary` 且 `quantity_col_var` 为空 | 错误 | `汇总模式必须指定“数量”列。` |
| 导出对象全未选中 | 所有 `export_*_var` 为 False | 错误 | `请至少选择一个导出内容。` |
| 任务单无有效图号 | 抽取后 0 条记录 | 错误 | `任务单中没有识别到有效图号，请检查字段映射。` |
| BOM 目录无 Excel | 扫描后为空 | 错误 | `BOM 文件夹下没有可搜索的 Excel 文件。` |
| 名称列未映射 | `name_col_var` 为空 | 警告 | `未指定名称列，多来源匹配时可能无法辅助判定。` |
| 序号列未映射 | `sequence_col_var` 为空 | 警告 | `未指定序号列，来源任务序号集合将为空。` |
| 备注列未映射 | `remark_col_var` 为空 | 提示 | `未指定备注列，将不输出任务单备注。` |

## 8.2 执行中错误提示

| 场景 | 建议文案 |
|---|---|
| 读取任务单失败 | `任务单读取失败：{错误信息}` |
| 某个 BOM 文件跳过 | `跳过文件：{文件名}，原因：{错误信息}` |
| `.xls` 无法转换 | `当前环境缺少 Excel COM 支持，无法读取 .xls 文件：{文件名}` |
| 找到父图号但无子项 | `图号 {drawing} 找到父项，但未提取到子项，请检查序号列。` |
| 命中多个来源 | `图号 {drawing} 命中多个来源，已按“{模式}”策略处理。` |
| 数量换算失败 | `图号 {drawing} 的部分子项数量无法换算，已写入异常报告。` |

## 8.3 完成提示

### 成功提示
```text
执行完成。
任务单条数: {total_queries}
汇总BOM行数: {summary_rows}
展开明细行数: {detail_rows}
未找到: {not_found_count}
异常数: {exception_count}
结果文件: {output_path}
```

### 部分成功提示
```text
执行完成，但存在异常。
未找到: {not_found_count}
异常数: {exception_count}
跳过文件: {skipped_file_count}
请先查看“异常报告”页签再使用结果文件。
```

---

## 9. 结果表格列设计

## 9.1 Tkinter 结果页签列

### A. 汇总BOM（主结果）
| 列名 | 来源 | 说明 |
|---|---|---|
| 序号 | 汇总结果生成时重排 | 不直接取旧BOM序号 |
| 物料ID | 子项/父项 `material_id` | 优先子项，父项兜底 |
| 图号 | 子项/父项 `drawing` | 优先子项，父项兜底 |
| 名称 | 子项/父项 `name` | 优先子项，父项兜底 |
| 厚度 | `thickness` | 无值可空 |
| 材质 | `material` | 无值可空 |
| 汇总总数量 | 汇总引擎计算 | 多来源累计后的结果 |
| 备注 | `remark` + 冲突提示 | 备注与异常标签可拼接 |
| 来源父图号集合 | 查询项/父项 | 用于追溯 |
| 来源任务单序号集合 | 查询项 `sequence` | 用于追溯 |
| 来源文件集合 | `workbook_path.name` | 用于追溯 |
| 匹配状态 | 汇总状态 | 如 `AGGREGATED` / `CONFLICT_SPLIT` |

### B. 展开明细
| 列名 | 对应代码来源 |
|---|---|
| 输入工作表 | `QueryItem.source_sheet` |
| 输入行号 | `QueryItem.source_row` |
| 输入序号 | `QueryItem.sequence` |
| 输入图号 | `QueryItem.drawing` |
| 输入名称 | `QueryItem.name` |
| 输入数量 | `QueryItem.quantity` |
| 来源文件 | `SheetTable.workbook_path.name` |
| 来源工作表 | `SheetTable.sheet_name` |
| 父行号 | `parent.excel_row` |
| 父序号 | `parent.sequence` |
| 父图号 | `parent.drawing` |
| 父名称 | `parent.name` |
| 子行号 | `child.excel_row` |
| 子序号 | `child.sequence` |
| 子图号 | `child.drawing` |
| 子名称 | `child.name` |
| 厚度 | `child.thickness` |
| 材质 | `child.material` |
| 原数量 | `child.quantity` |
| 原总数量 | `child.total_quantity` |
| 重算总数量 | 数量换算结果 |
| 备注 | `child.remark` |
| 结果状态 | `已提取子项` / `仅父项，无子项` / 其他异常 |
| 行类型 | `PARENT` / `CHILD` / `NOTE` |

### C. 未找到
沿用现有 `NOT_FOUND_HEADERS`，建议将 `状态` 列改名为 `原因`，更符合用户理解。

### D. 异常报告
建议新增，不复用现有工作表：
- 异常级别
- 异常类型
- 输入工作表
- 输入行号
- 输入图号
- 输入名称
- 来源文件
- 来源工作表
- 关联父图号
- 关联子图号
- 异常说明
- 建议处理

---

## 10. 导出参数设计

## 10.1 建议的导出配置对象

建议在 UI 层收集为一个字典或 dataclass：

```python
export_options = {
    "mode": self.run_mode_var.get(),
    "output_path": self.output_file_var.get().strip(),
    "export_summary": self.export_summary_var.get(),
    "export_detail": self.export_detail_var.get(),
    "export_not_found": self.export_not_found_var.get(),
    "export_exception": self.export_exception_var.get(),
    "open_after_export": self.open_after_export_var.get(),
}
```

## 10.2 导出工作表建议

| 工作表名 | 是否建议默认导出 | 说明 |
|---|---|---|
| `汇总BOM` | 是 | 新BOM主输出 |
| `展开明细` | 是 | 保留任务单到旧BOM的展开过程 |
| `未找到` | 是 | 未命中的输入项 |
| `异常报告` | 是 | 冲突、数量异常、多来源等 |
| `搜索结果` | 否 | 仅兼容旧模式时保留 |

## 10.3 输出命名建议
- `任务单名_汇总BOM.xlsx`
- `任务单名_汇总BOM_YYYYMMDD_HHMM.xlsx`（如需避免覆盖）

## 10.4 覆盖确认
若输出路径已存在，建议弹窗：
- 标题：`确认覆盖`
- 文案：`输出文件已存在，是否覆盖？`

---

## 11. 界面字段与业务字段映射

这是实现“旧BOM搜刮并汇总成新BOM”的关键部分。

## 11.1 任务单输入字段 -> 查询模型 `QueryItem`

| UI 映射字段 | 任务单业务含义 | 目标模型字段 | 用途 |
|---|---|---|---|
| `task_sheet_var` | 输入工作表 | `QueryItem.source_sheet` | 追溯来源 |
| Excel 行号（系统生成） | 输入行号 | `QueryItem.source_row` | 追溯来源 |
| `sequence_col_var` | 任务单序号 | `QueryItem.sequence` | 新BOM来源任务序号集合 |
| `drawing_col_var` | 父项图号 | `QueryItem.drawing` / `drawing_base` | 旧BOM匹配主键 |
| `name_col_var` | 父项名称 | `QueryItem.name` | 多来源歧义辅助判断 |
| `quantity_col_var` | 任务数量 | `QueryItem.quantity` | 子项总数量重算依据 |
| `task_no_col_var` | 任务单号 | 建议扩展字段 `task_no` | 输出追溯、文件命名、异常归组 |
| `remark_col_var` | 任务单备注 | 建议扩展字段 `input_remark` | 导出备注与追溯 |

## 11.2 旧BOM字段 -> 原始行模型 `RowRecord`

| 旧BOM字段 | 当前模型字段 | 对新BOM的作用 |
|---|---|---|
| 序号 | `sequence` | 父子边界识别 |
| 物料ID | `material_id` | 汇总主键优先项 |
| 图号 | `drawing` / `drawing_base` | 子件识别、弱主键 |
| 名称 | `name` | 展示与冲突辅助 |
| 厚度 | `thickness` | 汇总拆分条件 |
| 材质 | `material` | 汇总拆分条件 |
| 数量 | `quantity` | 数量换算回退依据 |
| 总数量 | `total_quantity` | 优先数量换算依据 |
| 备注 | `remark` | 追溯与异常提示 |

## 11.3 查询模型 + 旧BOM -> 展开明细业务字段

| 展开明细字段 | 映射来源 |
|---|---|
| 输入工作表 | `QueryItem.source_sheet` |
| 输入行号 | `QueryItem.source_row` |
| 输入序号 | `QueryItem.sequence` |
| 输入图号 | `QueryItem.drawing` |
| 输入名称 | `QueryItem.name` |
| 输入数量 | `QueryItem.quantity` |
| 来源文件 | `SheetTable.workbook_path.name` |
| 来源工作表 | `SheetTable.sheet_name` |
| 父图号/父名称 | `group.parent` |
| 子图号/子名称 | `child` |
| 原数量 | `child.quantity` |
| 原总数量 | `child.total_quantity` |
| 重算总数量 | `get_display_total_quantity()` 或汇总引擎结果 |
| 结果状态 | 搜索/展开状态 |

## 11.4 展开明细 -> 新BOM汇总字段

| 新BOM业务字段 | 推荐来源 | 规则 |
|---|---|---|
| 序号 | 汇总结果生成时重排 | 不使用旧BOM层级序号 |
| 物料ID | `child.material_id` 优先；父项兜底 | 汇总一级键 |
| 图号 | `child.drawing` 优先；父项兜底 | 汇总一级/二级键 |
| 名称 | `child.name` 优先；父项兜底 | 展示字段 |
| 厚度 | `child.thickness` | 规格拆分字段 |
| 材质 | `child.material` | 规格拆分字段 |
| 汇总总数量 | 重算总数量累计 | 汇总核心指标 |
| 备注 | 子项备注 + 异常提示 | 输出说明 |
| 来源父图号集合 | `QueryItem.drawing` + `parent.drawing` | 追溯字段 |
| 来源任务单序号集合 | `QueryItem.sequence` 去重集合 | 追溯字段 |
| 来源文件集合 | `SheetTable.workbook_path.name` 去重集合 | 追溯字段 |
| 匹配状态 | 汇总状态机 | `AGGREGATED/CONFLICT_SPLIT/QTY_UNRESOLVED/...` |

---

## 12. 与现有代码的对接建议

## 12.1 可直接复用的现有逻辑
- `HEADER_ALIASES`
- `detect_header()`
- `collect_workbook_paths()`
- `build_index()`
- `search_queries()`
- `extract_children()`
- `get_display_total_quantity()` 中的数量换算基础逻辑

## 12.2 需要增强的部分
1. `collect_queries()`
   - 当前完全自动识别
   - 需改为支持“按 UI 指定列映射收集任务项”

2. `SearchSummary`
   - 当前字段过少
   - 建议补充：
     - `summary_rows`
     - `detail_rows`
     - `exception_count`
     - `validation_warning_count`

3. `write_output()`
   - 当前只输出 `搜索结果/搜索明细/未找到`
   - 需扩展为：
     - `汇总BOM`
     - `展开明细`
     - `未找到`
     - `异常报告`

4. `BOMSearcherApp._on_search_success()`
   - 当前只弹窗
   - 需改为：
     - 填充各 `Treeview`
     - 更新状态栏
     - 根据异常数量自动切页

---

## 13. 推荐实现顺序（开发清单）

### 第一批：UI骨架
- [ ] 把 `__init__()` 中的状态变量抽到 `_init_state_vars()`
- [ ] 把 `_build_ui()` 拆成多个 `_build_xxx_panel()`
- [ ] 新增左侧配置区 + 右侧 Notebook
- [ ] 保留原 `log_text` 作为日志页签

### 第二批：输入与映射
- [ ] 实现任务单文件选择后自动加载工作表
- [ ] 实现字段自动识别与手动改选
- [ ] 实现任务单预览表
- [ ] 实现执行前校验

### 第三批：结果展示
- [ ] 新增 `summary_tree`
- [ ] 新增 `detail_tree`
- [ ] 新增 `not_found_tree`
- [ ] 新增 `exception_tree`
- [ ] 成功回调中填充表格

### 第四批：导出与提示
- [ ] 增加导出选项复选框
- [ ] 增加覆盖确认
- [ ] 增加完成摘要弹窗
- [ ] 增加异常摘要提示

### 第五批：业务对齐
- [ ] 把“搜索模式”与“汇总模式”分开
- [ ] 汇总模式默认输出 `汇总BOM`
- [ ] 汇总模式保留来源追溯与异常报告
- [ ] 明确说明行是否参与汇总

---

## 14. 最终结论

对于当前仓库，真正需要的不是“加几个按钮”，而是把 `BOMSearcherApp` 从一个简单文件选择器，升级成一个面向任务单的 **Tkinter BOM 汇总工作台**。

第一阶段建议仍在 `bom_searcher.py` 中落地上述界面区块和状态变量，优先完成：
1. 运行模式切换；
2. 任务单字段映射；
3. 结果表格预览；
4. 导出选项；
5. 错误与异常可视化。

这样后端汇总逻辑一旦补齐，GUI 就可以直接承接“旧BOM搜刮并汇总成新BOM”的完整业务流程。