# 新BOM汇总后端实现边界与对接说明

## 0. 结论摘要

当前项目的“旧BOM汇总生成新BOM”能力，已经基于 `bom_searcher.py` 完成第一版可落地实现：
- 输入源仍然是 **待查 Excel + BOM 文件夹 + 输出文件路径**
- 处理链路为 **读取待查图号 → 建索引 → 匹配父项 → 提取子项 → 重算数量 → 导出搜索结果/汇总BOM/明细/未找到**
- 新增的 `汇总BOM` 工作表，已经可以作为“新 BOM 草稿”使用
- 当前未引入数据库；**数据库 Schema 变更：无**

但从业务一致性来看，当前实现仍有几处需要确认或二次修正，尤其是：
1. `汇总BOM` 当前会把“无图号的工艺说明/备注行”也当作可汇总项，这是**高优先级待修正点**
2. 同一图号若在多个旧 BOM 文件中重复出现，当前会**全部计入汇总**，是否应按版本/文件优先级去重，需业务确认
3. 聚合键当前使用 `图号主编码(drawing_base)`，如果业务要求按“完整图号”区分版本/括号尾码，则需要调整

---

## 1. 接口定义

> 当前项目尚未提供 HTTP 服务接口，现状是 **内部函数接口 + CLI 接口 + Tkinter 界面入口**。为了便于后续服务化，这里同时给出建议的 OpenAPI 定义。

### 1.1 当前内部函数接口

```python
run_search(
    input_file: Path,
    bom_folder: Path,
    output_file: Path,
    log: Callable[[str], None] | None = None,
) -> SearchSummary
```

### 1.2 当前命令行接口

```bash
python bom_searcher.py --input "C:\待查.xlsx" --bom-folder "C:\BOM目录" --output "C:\输出.xlsx"
```

参数说明：
- `input`：待查 Excel，提供要生成新 BOM 的目标父项清单
- `bom-folder`：旧 BOM 来源目录，递归扫描 Excel 文件
- `output`：输出结果文件路径

### 1.3 建议的 HTTP/OpenAPI 接口定义（供后续服务化）

```yaml
openapi: 3.0.3
info:
  title: BOM Summary API
  version: 1.0.0
paths:
  /api/bom/summary:
    post:
      summary: 从待查Excel和旧BOM目录生成新BOM汇总
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - inputFile
                - bomFolder
                - outputFile
              properties:
                inputFile:
                  type: string
                  description: 待查Excel绝对路径
                bomFolder:
                  type: string
                  description: 旧BOM目录绝对路径
                outputFile:
                  type: string
                  description: 输出Excel绝对路径
                aggregateMode:
                  type: string
                  enum: [children-first, children-only, parent-fallback]
                  default: parent-fallback
                  description: 汇总策略
                drawingMatchMode:
                  type: string
                  enum: [drawing-base, full-drawing]
                  default: drawing-base
                  description: 图号匹配/聚合规则
      responses:
        '200':
          description: 生成成功
          content:
            application/json:
              schema:
                type: object
                properties:
                  totalQueries:
                    type: integer
                  totalResults:
                    type: integer
                  notFoundCount:
                    type: integer
                  outputPath:
                    type: string
                  scannedFiles:
                    type: integer
                  skippedFiles:
                    type: array
                    items:
                      type: string
        '400':
          description: 参数错误或输入内容不可解析
        '500':
          description: BOM读取/导出失败
```

---

## 2. 数据库 Schema 变更

**无。**

当前实现完全基于 Excel 文件读写与内存聚合：
- 无 NestJS / FastAPI API 层
- 无 TypeORM / Prisma / 数据库存储
- 无持久化表结构变更

如果后续要做服务端任务记录，可再单独设计：
- `bom_job`
- `bom_job_file`
- `bom_summary_item`
- `bom_not_found_item`

但这不属于当前首轮实现范围。

---

## 3. 输入参数与输入源

## 3.1 输入参数

`run_search()` 当前依赖 3 个主参数、1 个可选日志回调：

| 参数 | 类型 | 来源 | 用途 |
|---|---|---|---|
| `input_file` | `Path` | CLI / Tkinter | 待查 Excel |
| `bom_folder` | `Path` | CLI / Tkinter | 旧 BOM 文件夹 |
| `output_file` | `Path` | CLI / Tkinter | 输出 Excel |
| `log` | `Callable[[str], None] \| None` | CLI `print` / GUI 文本框 | 过程日志 |

## 3.2 输入源落点

### 待查 Excel
来源函数：`collect_queries`

职责：
- 扫描每个工作表
- 自动识别表头
- 抽取每一行的 `图号 / 序号 / 名称 / 数量`
- 形成 `QueryItem`

### 旧 BOM 目录
来源函数：
- `collect_workbook_paths`
- `build_index`
- `load_tables_from_workbook`

职责：
- 递归遍历目录中的 Excel 文件
- 跳过临时文件 `~$`
- 跳过结果文件（文件名含“搜索结果”）
- 识别并索引 BOM 行中的父图号/子图号候选

### GUI 输入源
Tkinter 入口：
- `choose_input_file`
- `choose_bom_folder`
- `choose_output_file`
- `start_search`
- `_search_worker`

对接关系：
- GUI 负责收集路径
- `_search_worker` 在线程中调用 `run_search`
- `log` 回调写入 GUI 文本框

---

## 4. 汇总流程关键步骤

## 4.1 表头识别与字段标准化

关键函数：
- `normalize_text`
- `normalize_header`
- `detect_header`
- `make_row_record`

规则：
- 自动把中文全角括号转成半角括号
- 去空白、换行、制表符
- 通过 `HEADER_ALIASES` 识别常见别名列
- 至少识别到 `图号` 列，才视为有效表

## 4.2 待查数据读取

关键函数：`collect_queries`

处理：
- 每个工作表识别为表格后，逐行抽取 `QueryItem`
- 没有 `drawing_base` 的行直接跳过
- 当前不会校验数量是否为空；数量为空时仍允许查询

## 4.3 旧 BOM 索引建立

关键函数：
- `collect_workbook_paths`
- `load_tables_from_workbook`
- `build_index`

处理：
- 递归扫描 BOM 文件夹
- 对每个有效工作表，逐行提取 `RowRecord`
- 使用 `row.drawing_base` 建立索引：
  ```python
  index[drawing_base] -> list[(SheetTable, row_index)]
  ```

## 4.4 父项匹配与子项提取

关键函数：
- `search_queries`
- `extract_children`

处理：
1. 用 `query.drawing_base` 在索引中查找候选父项
2. 每个命中的父项都生成一个 `SearchGroup`
3. `extract_children` 按序号层级提取子项：
   - 父序号是自然数（如 `1` / `2`）时，持续取到下一个自然数序号前
   - `1.1`、`1.2` 等子序号会被视为子项
   - 同组中的“无层级序号但有内容”的行也会被带出
   - 空序号但有名称/备注/数量的说明行也会被带出

## 4.5 数量重算

关键函数：`get_display_total_quantity`

规则：
- 父项：直接使用待查 Excel 的数量，若为空则回退原 BOM `总数量`
- 子项：
  1. 优先按 `子项总数量 × 输入数量 ÷ 父项总数量` 比例换算
  2. 若比例换算缺条件，则退化为 `子项数量 × 输入数量`
  3. 再不满足时，回退 `输入数量` 或原 `总数量`

这一步是“新 BOM 汇总”最关键的业务计算点。

## 4.6 新 BOM 汇总

关键函数：
- `aggregate_groups`
- `write_aggregated_sheet`

当前实现：
1. 若 `SearchGroup` 有子项，则汇总 `children`
2. 若无子项，则回退汇总 `parent`
3. 调用 `get_display_total_quantity` 先计算每个候选项在当前查询下的重算 `总数量`
4. 再按聚合键累加

---

## 5. 字段映射与去重/合并规则落点

## 5.1 输入字段映射

### 待查 Excel → `QueryItem`

| Excel列 | `QueryItem` 字段 | 说明 |
|---|---|---|
| 序号 | `sequence` | 输出到搜索结果父项序号 |
| 图号 | `drawing` / `drawing_base` | 匹配旧 BOM 的核心键 |
| 名称 | `name` | 明细追踪 |
| 数量 | `quantity` | 参与父项/子项总数量重算 |

### 旧 BOM → `RowRecord`

| Excel列 | `RowRecord` 字段 | 说明 |
|---|---|---|
| 序号 | `sequence` | 控制层级提取 |
| 物料ID | `material_id` | 汇总键组成部分 |
| 图号 | `drawing` / `drawing_base` | 匹配与汇总主键 |
| 名称 | `name` | 汇总键组成部分 |
| 厚度 | `thickness` | 汇总键组成部分 |
| 材质 | `material` | 汇总键组成部分 |
| 数量 | `quantity` | 汇总项展示单件数量 |
| 总数量 | `total_quantity` | 参与重算 |
| 备注 | `remark` | 汇总键组成部分 |

## 5.2 去重/合并规则代码落点

### 图号匹配规则
落点：`extract_drawing_base`

当前逻辑：
- `101002000250（248010310）` 与 `101002000250` 会被归并为相同 `drawing_base`
- 也就是：**匹配时默认忽略括号尾码/格式差异**

### 汇总聚合键
落点：`aggregate_groups`

当前聚合键：
```python
(
    row.material_id,
    row.drawing_base,
    row.name,
    row.thickness,
    row.material,
    row.remark,
)
```

含义：
- 同 `物料ID`
- 同图号主编码
- 同名称
- 同厚度
- 同材质
- 同备注

才会被视为同一汇总项。

### 数量字段合并规则
落点：`AggregatedBOMItem.add_occurrence`

当前策略：
- `总数量`：若能解析为数字，则做求和
- `数量`：若同一聚合项出现多个不同值，则最终留空

这是一个偏保守的展示策略，避免输出错误的单件用量。

---

## 6. 导出结果结构

输出文件当前包含 4 个工作表：

## 6.1 `搜索结果`

用途：
- 保留“按输入项逐组展开”的原始拉取结果
- 前端/业务可用它核对某个父项是从哪个旧 BOM 抓到哪些子项

结构：
- 列头固定为 `BOM_RESULT_HEADERS`
- 父项在前，子项在后
- 父项序号沿用待查 Excel 的序号
- 子项序号为空

## 6.2 `汇总BOM`

用途：
- 真正面向“新 BOM 草稿”
- 把搜索结果中的物料项聚合后输出

结构：
- 也使用 `BOM_RESULT_HEADERS`
- 当前序号列固定留空
- 主要可用列：`物料ID / 图号 / 名称 / 厚度 / 材质 / 数量 / 总数量 / 备注`

## 6.3 `搜索明细`

用途：
- 问题追踪 / 结果审计
- 能反查“输入哪一行命中了哪个文件、哪个sheet、哪一行父项、哪一行子项”

## 6.4 `未找到`

用途：
- 记录完全未命中任何旧 BOM 父项的输入图号
- 用于人工补 BOM 或补源文件

---

## 7. 错误处理

## 7.1 当前已实现的错误处理

| 场景 | 当前处理 |
|---|---|
| 输入文件不存在 | `FileNotFoundError` |
| BOM目录不存在 | `FileNotFoundError` |
| 输入 Excel 未识别到图号列或有效图号 | `RuntimeError` |
| BOM 文件夹无可搜索 Excel | `RuntimeError` |
| `.xls` 缺少 Excel COM 支持 | 单文件报错并加入 `skipped_files` 或直接抛错场景 |
| 单个 BOM 文件解析失败 | 跳过该文件，记录到 `skipped_files`，不中断整体流程 |
| GUI 环境缺少 tkinter | `RuntimeError`，提示改用 CLI |

## 7.2 建议补强的错误处理

1. **汇总BOM过滤无物料说明行**
   - 当前 `aggregate_groups` 会把“工艺说明/备注行”纳入汇总
   - 建议在汇总前新增过滤：至少要有 `drawing_base` 或 `material_id`

2. **重复来源告警**
   - 同一个 `drawing_base` 若在多个旧 BOM 文件重复命中，当前全部纳入
   - 建议新增日志或单独工作表标记“多来源重复命中”

3. **数量异常告警**
   - 当 `query.quantity` / `row.total_quantity` 无法转成数字时，目前直接走降级分支
   - 建议在 `搜索明细` 或日志中明确标记：`数量按降级规则回退`

4. **聚合冲突告警**
   - 同聚合项若出现多个不同 `quantity`，现在只是清空数量列
   - 建议增加一列 `汇总冲突说明` 或写入日志

---

## 8. 日志记录

## 8.1 当前日志机制

当前日志是**函数回调式日志**，无独立日志框架：
- CLI 模式：`log=print`
- Tkinter 模式：`log=lambda msg: self.root.after(0, self.log, msg)`

当前已记录的关键步骤：
- 正在读取待查 Excel
- 待查图号数量
- 待扫描 BOM 文件数
- 索引完成数量
- 搜索完成结果数 / 未命中数
- 输出文件路径
- 跳过的损坏/不可读文件

## 8.2 建议日志补充

建议新增以下日志点：
- 每个输入图号命中的候选数
- 多来源重复命中告警
- 汇总BOM最终条数
- 被过滤掉的说明行数量
- 数量重算降级次数

---

## 9. 与 Tkinter 界面的对接点

## 9.1 当前对接方式

Tkinter 目前无需改动即可直接承载新 BOM 汇总能力，因为：
- GUI 最终只调用 `run_search`
- `run_search` 已经统一导出 `汇总BOM`
- 界面层不需要额外传参即可获得新工作表

关键入口：
- `start_search`：校验 3 个路径已选
- `_search_worker`：后台线程调用 `run_search`
- `_on_search_success`：弹窗展示统计结果

## 9.2 当前 GUI 层已知缺口

1. 成功提示里只展示：
   - 待查图号数
   - 结果行数
   - 未命中数
   - 输出路径

   **未展示：**
   - `汇总BOM` 条数
   - `skipped_files` 数量摘要
   - 是否存在重复来源/冲突项

2. GUI 没有汇总策略开关：
   - 不能选择 `children-only` / `parent-fallback`
   - 不能选择 `drawing-base` / `full-drawing`

## 9.3 GUI 建议改造点

最小改造建议：
- 新增只读提示：输出文件包含 `汇总BOM`
- 成功弹窗补充：`汇总BOM 条数`

后续增强建议：
- 新增复选框/下拉：
  - 是否忽略说明行
  - 图号匹配方式
  - 多来源重复命中处理策略

---

## 10. 与测试验证的对接点

## 10.1 当前已覆盖的测试

当前 `tests/test_bom_searcher.py` 已覆盖：
1. 提取自然数父项下的子项和空序号说明行
2. 提取非 `1.1` 格式但仍属于同组的行
3. 无子项时父项单独输出
4. 完全未匹配时写入 `未找到`
5. 多个旧 BOM 的相同子项在 `汇总BOM` 中合并
6. 无子项时父项回退写入 `汇总BOM`

## 10.2 建议新增测试

高优先级建议补充以下测试：
1. **说明行不进入汇总BOM**
2. **同图号在两个旧 BOM 文件重复出现的处理规则**
3. **同聚合项但 `quantity` 不一致时数量列清空**
4. **括号尾码不同但主图号相同的汇总行为**
5. **输入数量为空 / 非数字时的降级行为**
6. **`.xls` 文件在无 COM 环境下的跳过行为**

### 单元测试示例

```python
def test_note_rows_should_not_be_aggregated_into_summary_bom(self) -> None:
    # 目标：验证“工艺说明”类无图号/无物料ID行不会出现在汇总BOM
    ...
```

---

## 11. 当前实现与业务规则的偏差 / 建议修正点

### P0：汇总BOM应排除说明行

**现状**：
- `extract_children` 会保留说明行，这是正确的，因为 `搜索结果` 需要完整还原上下文
- 但 `aggregate_groups` 当前会把这些说明行也纳入 `汇总BOM`

**风险**：
- 新 BOM 草稿里会出现无图号、无物料ID、只有“工艺说明”名称的伪物料行

**建议修正**：
- 新增 `should_include_in_aggregate(row)`
- 规则建议：至少满足 `row.drawing_base` 或 `row.material_id` 之一

### P1：重复来源是否全量累加需要确认

**现状**：
- 同一输入图号命中多个旧 BOM 文件时，当前全部加入 `groups`
- `汇总BOM` 会把这些来源全部累加

**风险**：
- 如果 BOM 目录里同时存在旧版/新版/备份文件，可能重复计算

**建议修正**：
- 增加策略参数：
  - `all-matches`
  - `first-match`
  - `latest-file`
  - `manual-review`

### P1：聚合键是否应使用完整图号而非主图号

**现状**：
- 汇总键使用 `drawing_base`
- 如括号尾码或后缀表示版本差异，可能被合并

**建议修正**：
- 若业务强调版本隔离，改为：
  - `material_id + drawing(完整图号) + 名称 + 厚度 + 材质 + 备注`

### P2：SearchSummary 未返回汇总BOM统计

**现状**：
- `SearchSummary.total_results` 仅代表 `搜索结果` 行数
- 不包含 `汇总BOM` 条数

**建议修正**：
- 在 `SearchSummary` 中新增：
  - `aggregated_items`
  - `duplicate_match_count`
  - `warning_count`

---

## 12. 最小可落地的下一步改造建议

如果只做一轮最小但高价值修正，建议按下面顺序推进：

### 第一步：修正汇总BOM过滤规则
改函数：
- `aggregate_groups`
- 新增 `should_include_in_aggregate`

目的：
- 避免说明行污染新 BOM

### 第二步：补充汇总告警与统计
改函数：
- `write_aggregated_sheet`
- `write_output`
- `SearchSummary`

目的：
- 让 GUI / CLI 能看到汇总条数和警告信息

### 第三步：把重复来源策略参数化
改函数：
- `search_queries`
- `run_search`
- `parse_args`
- Tkinter 界面参数区

目的：
- 防止旧版/备份文件重复累加

---

## 13. 对接建议（给 Leader / 前端 / 测试）

### 给 Leader
- 当前版本已可生成“新 BOM 草稿”
- 但在正式交付前，建议先确认三条业务口径：
  1. 工艺说明是否进入汇总BOM（建议否）
  2. 同图号多来源是否全量累加（建议可配置）
  3. 聚合按主图号还是完整图号（建议明确）

### 给前端/Tkinter
- 现阶段无需改调用方式
- 只要继续调用 `run_search`，输出文件内就会多出 `汇总BOM`
- 若要提升可用性，优先补充成功提示中的汇总条数和风险提示

### 给测试
- 现有测试可继续回归
- 下一批测试优先验证：说明行过滤、重复来源、图号版本差异

---

## 14. 代码落点清单（便于开发直接修改）

| 目标 | 代码落点 |
|---|---|
| 输入表头识别 | `HEADER_ALIASES`, `detect_header` |
| 待查数据读取 | `collect_queries` |
| BOM 文件扫描 | `collect_workbook_paths`, `load_tables_from_workbook` |
| 索引建立 | `build_index` |
| 父项匹配 | `search_queries` |
| 子项提取 | `extract_children` |
| 数量重算 | `get_display_total_quantity` |
| 新BOM聚合 | `aggregate_groups`, `AggregatedBOMItem` |
| 汇总导出 | `write_aggregated_sheet`, `write_output` |
| GUI 触发 | `start_search`, `_search_worker` |
| CLI 触发 | `parse_args`, `main` |

---

## 15. 当前状态说明

- 后端首轮实现：**已完成**
- 汇总BOM导出：**已落地**
- README：**已更新**
- 自动化测试：**已通过**
- 业务规则最终校准：**待确认 3 个关键口径（说明行、重复来源、完整图号）**
