# 图块资源命名与存储规范 (Block Resource Naming and Storage Standards)

## 1. 核心原则 (Core Principles)
- **唯一性 (Uniqueness)**: 每一种几何形状（Geometry）对应且仅对应一个唯一的图块名称（Block Name）。
- **一致性 (Consistency)**: 相同内容的图块在不同文件中必须使用相同的名称。
- **无冲突 (No Conflicts)**: 禁止不同内容的图块使用相同的名称。

## 2. 命名规范 (Naming Conventions)
- **优先保留原名**: 对于已存在的图块，优先保留其原始名称（如物料编码、图号等）。
- **冲突处理 (Conflict Resolution)**:
  - 当发现多个不同几何形状共用同一个名称（如 `BlockA`）时：
    - 保留最常用或最早出现的版本为原名 `BlockA`。
    - 其他变体按顺序添加后缀 `_v2`, `_v3`, ... (例如 `BlockA_v2`)。
- **别名合并 (Alias Merging)**:
  - 当发现完全相同的几何形状有多个名称（如 `BlockA` 和 `BlockB`）时：
    - 选取出现频率最高或格式最规范的名称作为**标准名**。
    - 将所有引用统一更新为标准名，并删除其他别名定义。

## 3. 存储规范 (Storage Conventions)
- **项目内存储**: 图块定义直接存储于使用它们的 DXF 项目文件中。
- **去重维护**: 
  - 单个 DXF 文件内不得包含重复内容的块定义（已被合并）。
  - 跨文件的同名图块必须保证内容一致。

## 4. 维护流程 (Maintenance Workflow)
1. **定期检查**: 使用 `find_duplicates.py` 扫描项目目录，检测潜在的新增冲突。
2. **自动化清理**: 运行 `normalize_blocks.py` 自动执行上述命名与合并规则。
3. **清单生成**: 使用 `generate_block_report.py` 更新 `block_resource_list.csv` 资源清单。
