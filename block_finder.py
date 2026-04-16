import re
import os
import logging
import traceback
from typing import List, Dict, Any, Optional, Tuple, Set
import ezdxf
from ezdxf.math import Matrix44
from ezdxf.addons import Importer
import pandas as pd

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def compute_block_center_and_size(src_block) -> Tuple[float, float, float, float]:
    """
    计算块的几何包围盒中心和尺寸
    
    参数:
    src_block: 源块对象
    
    返回:
    tuple: (中心X, 中心Y, 宽度, 高度)
    """
    try:
        from ezdxf import bbox
        extents = bbox.extents(src_block)
        if extents.has_data:
            width = extents.extmax.x - extents.extmin.x
            height = extents.extmax.y - extents.extmin.y
            center_x = (extents.extmin.x + extents.extmax.x) / 2.0
            center_y = (extents.extmin.y + extents.extmax.y) / 2.0
            return (center_x, center_y, width, height)
    except Exception as e:
        logger.warning(f"使用ezdxf.bbox计算包围盒失败，回退到手动计算: {e}")

    min_x = min_y = float('inf')
    max_x = max_y = float('-inf')
    found = False
    
    # 遍历块中的所有实体，计算包围盒
    for entity in src_block:
        try:
            entity_type = entity.dxftype()
            
            # 尝试使用virtual_entities获取精确边界（针对INSERT, DIMENSION等）
            if hasattr(entity, 'virtual_entities'):
                try:
                    for ve in entity.virtual_entities():
                        # 递归调用或者简单获取点
                        # 这里简化处理：获取所有点
                        points = []
                        if hasattr(ve.dxf, 'start'): points.append(ve.dxf.start)
                        if hasattr(ve.dxf, 'end'): points.append(ve.dxf.end)
                        if hasattr(ve.dxf, 'center'): 
                            points.append(ve.dxf.center)
                            # 如果是圆/弧，加上半径范围
                            if hasattr(ve.dxf, 'radius'):
                                r = ve.dxf.radius
                                points.append((ve.dxf.center[0]-r, ve.dxf.center[1]-r))
                                points.append((ve.dxf.center[0]+r, ve.dxf.center[1]+r))
                        if hasattr(ve, 'get_points'): points.extend(ve.get_points())
                        if hasattr(ve, 'vertices'): 
                            points.extend([v.dxf.location for v in ve.vertices])
                        
                        for p in points:
                            px, py = float(p[0]), float(p[1])
                            min_x = min(min_x, px); min_y = min(min_y, py)
                            max_x = max(max_x, px); max_y = max(max_y, py)
                            found = True
                    # 如果成功处理了virtual_entities，继续下一个实体
                    if found: continue
                except Exception:
                    pass

            # 处理具有插入点的实体（如块引用）
            if hasattr(entity.dxf, 'insert'):
                insert_point = entity.dxf.insert
                px, py = float(insert_point[0]), float(insert_point[1])
                min_x = min(min_x, px); min_y = min(min_y, py)
                max_x = max(max_x, px); max_y = max(max_y, py)
                found = True
            
            # 处理具有起点和终点的实体（如线段）
            if hasattr(entity.dxf, 'start') and hasattr(entity.dxf, 'end'):
                start_point = entity.dxf.start
                end_point = entity.dxf.end
                for point in (start_point, end_point):
                    px, py = float(point[0]), float(point[1])
                    min_x = min(min_x, px); min_y = min(min_y, py)
                    max_x = max(max_x, px); max_y = max(max_y, py)
                    found = True
            
            # 处理具有中心的实体（如圆/弧）
            if hasattr(entity.dxf, 'center'):
                center_point = entity.dxf.center
                px, py = float(center_point[0]), float(center_point[1])
                radius = float(entity.dxf.radius) if hasattr(entity.dxf, 'radius') else 0.0
                min_x = min(min_x, px - radius); min_y = min(min_y, py - radius)
                max_x = max(max_x, px + radius); max_y = max(max_y, py + radius)
                found = True
            
            # 处理多点实体（如折线）
            try:
                if entity_type == 'LWPOLYLINE':
                    points = list(entity.get_points()) if hasattr(entity, 'get_points') else []
                    for point in points:
                        px, py = float(point[0]), float(point[1])
                        min_x = min(min_x, px); min_y = min(min_y, py)
                        max_x = max(max_x, px); max_y = max(max_y, py)
                        found = True
                elif entity_type == 'POLYLINE':
                    for v in entity.vertices:
                        px, py = float(v.dxf.location[0]), float(v.dxf.location[1])
                        min_x = min(min_x, px); min_y = min(min_y, py)
                        max_x = max(max_x, px); max_y = max(max_y, py)
                        found = True
                elif entity_type == 'SPLINE':
                    points = []
                    if len(entity.fit_points) > 0:
                        points.extend(entity.fit_points)
                    if len(entity.control_points) > 0:
                        points.extend(entity.control_points)
                    
                    for p in points:
                        px, py = float(p[0]), float(p[1])
                        min_x = min(min_x, px); min_y = min(min_y, py)
                        max_x = max(max_x, px); max_y = max(max_y, py)
                        found = True
                elif entity_type == 'ELLIPSE':
                    # 简化处理：使用中心点和长轴端点
                    center = entity.dxf.center
                    major = entity.dxf.major_axis
                    p1 = (center[0] + major[0], center[1] + major[1])
                    p2 = (center[0] - major[0], center[1] - major[1])
                    # 短轴方向近似
                    ratio = entity.dxf.ratio
                    # 简单的包围盒近似
                    pts = [center, p1, p2]
                    for p in pts:
                        px, py = float(p[0]), float(p[1])
                        min_x = min(min_x, px); min_y = min(min_y, py)
                        max_x = max(max_x, px); max_y = max(max_y, py)
                        found = True
            except Exception:
                pass
        except Exception:
            continue

    # 如果没有找到实体，返回默认值
    if not found:
        return (0.0, 0.0, 0.0, 0.0)
    
    # 计算中心坐标和尺寸
    center_x = (min_x + max_x) / 2.0
    center_y = (min_y + max_y) / 2.0
    width = max_x - min_x
    height = max_y - min_y
    
    return (center_x, center_y, width, height)

class BlockFinder:
    """
    块查找器，负责根据Excel文件中的物料ID或图号筛寻DXF文件中的块
    """
    
    def __init__(self, text_strategy: str = 'first_valid'):
        # 延迟导入
        from cad_reader import CADReader
        from text_processor import TextProcessor
        self.cad_reader = CADReader("")
        self.text_processor = TextProcessor()
        self.text_strategy = text_strategy

    def _normalize_column_label(self, label: Any) -> str:
        """
        规范化表头名称，尽量消除大小写、空格、连字符差异。
        """
        normalized = str(label).strip().lower()
        normalized = re.sub(r"[\s\-]+", "_", normalized)
        normalized = re.sub(r"_+", "_", normalized).strip("_")
        return normalized

    def _column_keyword_matches(self, normalized_column: str, keyword: str) -> bool:
        """
        判断列名是否匹配关键字。

        英文关键字使用精确匹配，避免 `material` 错误匹配 `material_id`；
        中文关键字保留包含匹配，兼容“主材质”“零件名称”等扩展表头。
        """
        normalized_keyword = self._normalize_column_label(keyword)
        if not normalized_keyword:
            return False

        if re.search(r"[a-z]", normalized_keyword):
            return normalized_column == normalized_keyword

        return normalized_keyword in normalized_column

    def _resolve_merged_identifier_map(
        self,
        merged_identifier_map: Dict[str, str],
        visible_identifiers: Set[str],
    ) -> Dict[str, str]:
        """
        将合并链路解析到最终仍然可见的代表标识符。
        """
        resolved_map: Dict[str, str] = {}

        for identifier, representative in merged_identifier_map.items():
            if identifier in visible_identifiers:
                continue

            current = representative
            seen = {identifier}
            while current in merged_identifier_map and current not in visible_identifiers and current not in seen:
                seen.add(current)
                current = merged_identifier_map[current]

            if current in visible_identifiers:
                resolved_map[identifier] = current

        return resolved_map
    
    def load_excel(self, excel_file: str) -> Optional[pd.DataFrame]:
        """
        加载Excel文件
        
        参数:
        excel_file: Excel文件路径
        
        返回:
        Optional[pd.DataFrame]: Excel数据，加载失败则返回None
        """
        try:
            df = pd.read_excel(excel_file)
            logger.info(f"成功加载Excel文件: {excel_file}")
            logger.info(f"Excel文件包含 {len(df)} 行数据")
            logger.info(f"Excel文件列名: {list(df.columns)}")
            return df
        except Exception as e:
            logger.error(f"加载Excel文件时出错: {e}")
            return None
    
    def _identify_columns(self, df: pd.DataFrame) -> Dict[str, str]:
        """
        识别Excel文件中的列
        
        参数:
        df: Excel数据
        
        返回:
        Dict[str, str]: 列类型到列名的映射
        """
        # 列类型到关键字的映射
        column_keywords = {
            'material_id': ['物料id', '物料编号', 'material id', 'material_id', 'item id', 'item_id', 'part id', 'part_id'],
            'drawing_num': ['图号', '图纸编号', 'drawing', 'drawing no', 'drawing_no', 'drawing number'],
            'total_qty': ['总数量', '总量', 'total', 'total qty', 'total_qty', '数量合计'],
            'material': ['材质', '材料', 'material', 'material type'],
            'thickness': ['厚度', '厚', 'thickness', 'thick'],
            'name': ['名称', '零件名称', '部件名称', '零件名', '品名', 'name', 'part name', 'part_name'],
            'remark': ['备注', '备注栏', 'remark', 'note', '单号', '订单号', '批号'],
            'sequence': ['序号', '编号', 'no', 'num', 'number', 'index']
        }
        
        column_map = {}
        
        for col in df.columns:
            normalized_col = self._normalize_column_label(col)
            for col_type, keywords in column_keywords.items():
                if col_type not in column_map:
                    for keyword in keywords:
                        if self._column_keyword_matches(normalized_col, keyword):
                            column_map[col_type] = col
                            break
        
        # 特殊处理888.xlsx文件的列名
        if '规格' in df.columns:
            column_map['thickness'] = '规格'
        
        return column_map

    def _normalize_identifier(self, identifier: str) -> str:
        """
        规范化标识符，去除括号及其后面的内容，只保留括号前的部分
        """
        if not identifier:
            return identifier
        # 按英文括号分割
        identifier = identifier.split('(')[0]
        # 按中文括号分割
        identifier = identifier.split('（')[0]
        return identifier.strip()

    def extract_material_info(self, df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
        """
        从Excel数据中提取物料信息
        
        参数:
        df: Excel数据
        
        返回:
        Dict[str, Dict[str, Any]]: 物料ID或图号到详细信息的映射
        """
        material_info = {}
        
        # 识别列
        column_map = self._identify_columns(df)
        material_id_col = column_map.get('material_id')
        drawing_num_col = column_map.get('drawing_num')
        total_qty_col = column_map.get('total_qty')
        material_col = column_map.get('material')
        thickness_col = column_map.get('thickness')
        name_col = column_map.get('name')
        remark_col = column_map.get('remark')
        sequence_col = column_map.get('sequence')
        
        logger.info(f"识别到的列: 物料ID列='{material_id_col}', 图号列='{drawing_num_col}', \
                   总数量列='{total_qty_col}', 材质列='{material_col}', 厚度列='{thickness_col}', 名称列='{name_col}', 备注列='{remark_col}', 序号列='{sequence_col}'")
        
        # 处理数据
        def parse_qty(val):
            # 解析数量字段，支持数字、字符串形式的加法表达(如 '5+5')，若无法解析返回 1
            try:
                if pd.isna(val):
                    return 1
                if isinstance(val, (int, float)):
                    return int(val)
                s = str(val).strip()
                if '+' in s:
                    parts = [p.strip() for p in s.split('+') if p.strip()]
                    total = 0
                    for p in parts:
                        try:
                            total += int(p)
                        except Exception:
                            try:
                                total += int(float(p))
                            except Exception:
                                pass
                    return total if total > 0 else 1
                # 普通字符串数字
                return int(float(s))
            except Exception:
                return 1

        # 先收集所有行的信息，用于后续备注继承处理
        row_data_list = []  # 存储每行的信息：{'index': index, 'sequence': seq, 'remark': remark, 'identifiers': ids, 'row_info': {...}}
        
        for index, row in df.iterrows():
            # 获取本行的所有有效标识符
            identifiers_in_row = []
            
            # 1. 提取物料ID
            material_id_str = ""
            if material_id_col and pd.notna(row[material_id_col]):
                try:
                    material_id_value = row[material_id_col]
                    if isinstance(material_id_value, float):
                        if material_id_value.is_integer():
                            val = str(int(material_id_value)).strip()
                        else:
                            val = str(material_id_value).strip().rstrip('.0').rstrip('0').rstrip('.')
                    else:
                        val = str(int(material_id_value)).strip()
                except (ValueError, TypeError):
                    val = str(row[material_id_col]).strip()
                material_id_str = val
                norm_val = self._normalize_identifier(val)
                if norm_val:
                    identifiers_in_row.append(norm_val)

            # 2. 提取图号
            drawing_num_str = ""
            if drawing_num_col and pd.notna(row[drawing_num_col]):
                val = str(row[drawing_num_col]).strip()
                drawing_num_str = val
                norm_val = self._normalize_identifier(val)
                if norm_val:
                    identifiers_in_row.append(norm_val)

            # 去重
            identifiers_in_row = list(set(identifiers_in_row))
            
            # 如果没有有效标识符，跳过
            if not identifiers_in_row:
                continue

            qty = parse_qty(row[total_qty_col]) if total_qty_col else 1
            
            material_val = row[material_col] if material_col and pd.notna(row[material_col]) else ''
            thickness_val = row[thickness_col] if thickness_col and pd.notna(row[thickness_col]) else ''
            name_val = row[name_col] if name_col and pd.notna(row[name_col]) else ''
            
            # 提取序号值
            sequence_val = None
            if sequence_col and pd.notna(row[sequence_col]):
                try:
                    seq_value = row[sequence_col]
                    if isinstance(seq_value, (int, float)):
                        sequence_val = float(seq_value)
                    else:
                        sequence_val = float(str(seq_value).strip())
                except (ValueError, TypeError):
                    pass
            
            # 提取备注值（单号）
            remark_val = ''
            if remark_col and pd.notna(row[remark_col]):
                try:
                    remark_value = row[remark_col]
                    if isinstance(remark_value, (int, float)):
                        if float(remark_value).is_integer():
                            remark_val = str(int(remark_value)).strip()
                        else:
                            remark_val = str(remark_value).strip()
                    else:
                        remark_val = str(remark_value).strip()
                except (ValueError, TypeError):
                    remark_val = str(row[remark_col]).strip()

            # 创建共享的 info 对象
            # 注意：不在这里添加 row_allocations，而是在下面根据需要创建新字典
            info = {
                'total_qty': qty,
                'material': material_val,
                'thickness': thickness_val,
                'material_id': material_id_str,
                'drawing_num': drawing_num_str,
                'name': name_val,
                'remark': remark_val,
                'row_index': index  # 保留行索引作为参考（如第一行）
            }
            
            # 存储行数据用于后续备注继承
            row_data_list.append({
                'index': index,
                'sequence': sequence_val,
                'remark': remark_val,
                'identifiers': identifiers_in_row,
                'info': info,
                'qty': qty
            })
        
        # 备注继承：根据序号层级关系，将大组件的备注继承给子集
        # 大组件：序号是整数（如 1, 2, 3）
        # 子集：序号是小数（如 1.1, 1.2, 2.1），整数部分对应大组件
        parent_remarks = {}  # parent_sequence_int -> remark
        for row_data in row_data_list:
            seq = row_data['sequence']
            remark = row_data['remark']
            
            if seq is not None and remark:
                # 判断是否是大组件（整数）
                if seq == int(seq):
                    parent_remarks[int(seq)] = remark
        
        # 将大组件的备注继承给子集
        for row_data in row_data_list:
            seq = row_data['sequence']
            remark = row_data['remark']
            
            if seq is not None and not remark:
                # 没有备注，尝试从大组件继承
                parent_seq = int(seq)
                if parent_seq in parent_remarks:
                    inherited_remark = parent_remarks[parent_seq]
                    row_data['remark'] = inherited_remark
                    row_data['info']['remark'] = inherited_remark
                    logger.info(f"行 {row_data['index']}: 序号 {seq} 继承大组件 {parent_seq} 的备注 '{inherited_remark}'")
        
        # 现在处理收集到的行数据，构建 material_info
        for row_data in row_data_list:
            index = row_data['index']
            identifiers_in_row = row_data['identifiers']
            info = row_data['info']
            qty = row_data['qty']
            remark_val = row_data['remark']
            
            # 过滤掉材质和厚度均为"组件"的行（不用于块搜索，但备注仍用于继承）
            if str(info.get('material', '')).strip() == '组件' and str(info.get('thickness', '')).strip() == '组件':
                logger.info(f"跳过行 {index}: 材质和厚度均为'组件'（不用于块搜索）")
                continue
            
            # 确定标识符类型
            id_type = 'unknown'
            if material_id_col and pd.notna(df.at[index, material_id_col]):
                id_type = 'material_id'
            elif drawing_num_col and pd.notna(df.at[index, drawing_num_col]):
                id_type = 'drawing_num'

            for identifier in identifiers_in_row:
                if identifier in material_info:
                    # 如果标识符已存在
                    existing_info = material_info[identifier]
                    if not existing_info.get('material_id') and info.get('material_id'):
                        existing_info['material_id'] = info['material_id']
                    if not existing_info.get('drawing_num') and info.get('drawing_num'):
                        existing_info['drawing_num'] = info['drawing_num']
                    if not existing_info.get('name') and info.get('name'):
                        existing_info['name'] = info['name']
                    # 合并备注值：收集所有非空的备注
                    if remark_val:
                        existing_remarks = existing_info.get('remarks', [])
                        if existing_info.get('remark') and existing_info['remark'] not in existing_remarks:
                            existing_remarks.append(existing_info['remark'])
                        if remark_val not in existing_remarks:
                            existing_remarks.append(remark_val)
                        existing_info['remarks'] = existing_remarks
                    # 更新数量：通过添加行分配信息
                    if 'row_allocations' not in existing_info:
                        # 这是一个防御性检查，正常情况下新创建的info都会有row_allocations
                        existing_info['row_allocations'] = {existing_info.get('row_index', -1): existing_info.get('total_qty', 0)}
                    
                    # 只有当该行还未被记录时才添加（避免同一行的重复标识符导致的重复）
                    # 注意：identifiers_in_row 已经去重，所以对于同一个 identifier，index 只会出现一次
                    if index not in existing_info['row_allocations']:
                        existing_info['row_allocations'][index] = qty
                        # 重新计算总数量
                        existing_info['total_qty'] = sum(existing_info['row_allocations'].values())
                else:
                    # 新标识符
                    new_info = info.copy()
                    new_info['id_type'] = id_type
                    # 初始化行分配信息：行索引 -> 该行数量
                    new_info['row_allocations'] = {index: qty}
                    # 初始化备注列表
                    new_info['remarks'] = [remark_val] if remark_val else []
                    material_info[identifier] = new_info
        
        logger.info(f"成功提取 {len(material_info)} 个物料信息")
        # 打印前10个提取的物料信息，用于调试
        logger.info("前10个提取的物料信息:")
        for i, (id, info) in enumerate(list(material_info.items())[:10]):
            logger.info(f"{i+1}. {id} - 数量: {info['total_qty']}, 材质: {info['material']}, 厚度: {info['thickness']}")
        return material_info
    
    def _normalize_text_for_search(self, text: str) -> str:
        """
        规范化文本以进行搜索匹配：
        1. 统一连字符（将各种破折号、下划线统一为标准连字符 -）
        2. 去除空格
        3. 统一大小写（虽然本场景多为数字，但防万一）
        """
        if not text:
            return ""
        # 替换常见分隔符为标准连字符
        text = text.replace('_', '-').replace('—', '-').replace('－', '-')
        # 去除空格
        text = text.replace(' ', '')
        # 统一大写
        return text.upper()
    
    def _remark_matches_file(self, remark: str, filename: str) -> bool:
        """
        检查备注值（单号）是否匹配DXF文件名
        
        匹配规则：
        1. 精确匹配：备注值 == 文件名
        2. 文件名以备注值开头（如 "260326-版本2" 匹配 "260326"）
        3. 备注值以文件名开头（如备注 "260326 某描述" 匹配文件 "260326"）
        4. 备注值中包含文件名（要求文件名长度>=4，避免短串误匹配）
        5. 文件名中包含备注值（要求备注值长度>=4）
        
        参数:
        remark: 备注值（如单号 "260326"）
        filename: DXF文件名（不含扩展名）
        
        返回:
        bool: 是否匹配
        """
        if not remark or not filename:
            return False
        
        remark_clean = remark.strip()
        filename_clean = filename.strip()
        
        if not remark_clean or not filename_clean:
            return False
        
        # 精确匹配
        if remark_clean == filename_clean:
            return True
        
        # 文件名以备注值开头（如 "260326-版本2" 匹配 "260326"）
        if filename_clean.startswith(remark_clean):
            return True
        
        # 备注值以文件名开头（如备注 "260326 某描述" 匹配文件 "260326"）
        if remark_clean.startswith(filename_clean):
            return True
        
        # 备注值中包含文件名（要求文件名足够长以避免误匹配）
        if len(filename_clean) >= 4 and filename_clean in remark_clean:
            return True
        
        # 文件名中包含备注值（要求备注值足够长）
        if len(remark_clean) >= 4 and remark_clean in filename_clean:
            return True
        
        return False

    def search_blocks_in_dxf(self, dxf_file: str, material_info: Dict[str, Dict[str, Any]]) -> Dict[str, List[Any]]:
        """
        在DXF文件中搜索包含指定物料ID或图号的块
        
        参数:
        dxf_file: DXF文件路径
        material_info: 物料信息映射
        
        返回:
        Dict[str, List[Any]]: 物料ID或图号到找到的块的映射
        """
        # 设置CAD读取器的文件路径
        self.cad_reader.file_path = dxf_file
        
        # 加载文件
        if not self.cad_reader.load_file():
            logger.error(f"无法加载DXF文件: {dxf_file}")
            return {}
        
        found_blocks = {}
        
        # 预编译标识符，用于更精确的匹配
        identifiers = list(material_info.keys())
        # 按长度排序，优先匹配长标识符（避免子字符串匹配问题）
        identifiers.sort(key=len, reverse=True)
        
        # 遍历所有块
        for block in self.cad_reader.doc.blocks:
            # 跳过匿名块和布局块
            if block.name.startswith('*'):
                continue
            
            # 提取块中的文本内容
            block_texts = []
            block_text_full = ''
            block_text_raw = ''  # 新增：收集原始文本用于搜索
            text_objects = []  # 用于存储文本对象，以便使用与BlockCreator相同的文本处理逻辑
            
            for entity in block:
                try:
                    entity_type = entity.dxftype()
                    
                    # 收集文本内容
                    if entity_type in ['TEXT', 'MTEXT', 'ATTRIB']:
                        try:
                            if entity_type == 'TEXT':
                                text_content = entity.dxf.text
                            elif entity_type == 'MTEXT':
                                text_content = entity.dxf.text
                            elif entity_type == 'ATTRIB':
                                text_content = entity.dxf.text
                            
                            if text_content:
                                # 累加原始文本（去除DXF格式标记后）
                                # 简单的清理，保留空格和原始符号
                                simple_cleaned = self.text_processor.strip_dxf_tags(text_content)
                                block_text_raw += ' ' + simple_cleaned

                                # 构建文本对象，与BlockCreator使用的格式一致
                                text_object = {
                                    'entity': entity,
                                    'content': text_content,
                                    'type': entity_type
                                }
                                text_objects.append(text_object)
                                
                                # 清理文本内容（用于块名生成）
                                cleaned_text = self.text_processor.clean_text_for_block_name(text_content)
                                block_texts.append(cleaned_text)
                                block_text_full += ' ' + cleaned_text
                        except Exception as e:
                            logger.warning(f"处理块 {block.name} 中的文本时出错: {e}")
                except Exception:
                    continue
            
            # 清理完整文本
            block_text_full = block_text_full.strip()
            block_text_raw = block_text_raw.strip()
            
            # 创建无空格版本，用于跨实体匹配
            # 对于原始文本，只去除空格
            block_text_raw_no_spaces = block_text_raw.replace(' ', '')
            
            # 同时也保留旧的匹配逻辑作为备选（虽然它可能引入了下划线）
            block_text_no_spaces = block_text_full.replace(' ', '')
            
            # 如果没有直接的文本匹配，尝试使用与BlockCreator相同的文本处理逻辑
            if not block_text_full and text_objects:
                # 使用与BlockCreator相同的方法生成块名
                generated_text = self.text_processor.generate_block_name_from_texts(text_objects, self.text_strategy)
                if generated_text and generated_text != "Block":
                    block_text_full = generated_text
                    block_text_no_spaces = block_text_full.replace(' ', '')
                    # 对于生成文本，也作为raw处理
                    block_text_raw = generated_text
                    block_text_raw_no_spaces = generated_text.replace(' ', '')
                    block_texts.append(generated_text)
            
            # 检查块中是否包含物料ID或图号
            # 使用更精确的匹配，避免子字符串匹配问题
            matched_identifiers = set()
            
            # 准备待匹配的文本列表
            # 优先匹配 block_text_raw (最接近原始数据)
            # 然后是 block.name
            # 然后是 block_text_full (经过清理的)
            
            # 如果块名本身也包含有价值信息，加入规范化处理
            normalized_block_name = self._normalize_text_for_search(block.name)
            normalized_block_text = self._normalize_text_for_search(block_text_full)
            normalized_block_raw = self._normalize_text_for_search(block_text_raw)
            
            for identifier in identifiers:
                if not identifier:
                    continue
                
                # 1. 直接包含匹配 (在原始文本中)
                if identifier in block_text_raw or identifier in block.name or identifier in block_text_full:
                    matched_identifiers.add(identifier)
                    continue
                
                # 2. 无空格匹配 (在原始文本无空格版中)
                id_no_spaces = identifier.replace(' ', '')
                if id_no_spaces and (id_no_spaces in block_text_raw_no_spaces or 
                                   id_no_spaces in block_text_no_spaces or 
                                   id_no_spaces in block.name.replace(' ', '')):
                    matched_identifiers.add(identifier)
                    continue

                # 3. 规范化模糊匹配（处理连字符不一致等问题）
                normalized_id = self._normalize_text_for_search(identifier)
                if normalized_id and (normalized_id in normalized_block_raw or 
                                    normalized_id in normalized_block_name or 
                                    normalized_id in normalized_block_text):
                    matched_identifiers.add(identifier)

            # 后处理：如果一个标识符是另一个已匹配标识符的子字符串，则移除较短的标识符
            # 这样可以防止例如 "101002010375" 错误地匹配到 "101002010375-2" 的块
            # 并导致该块被两个标识符同时认领（进而导致数量重复计算）
            final_identifiers = set()
            # 按长度降序排序（长的在前）
            sorted_matches = sorted(matched_identifiers, key=len, reverse=True)
            for i, match in enumerate(sorted_matches):
                is_substring = False
                for existing in final_identifiers:
                    # 检查当前match是否是已存在的（更长的）identifier的子字符串
                    # 注意：这里需要更严格的判断，单纯的 substring 可能误杀
                    # 但在图号/物料ID的场景下，通常 longer match is better
                    if match in existing:
                        is_substring = True
                        break
                if not is_substring:
                    final_identifiers.add(match)
            matched_identifiers = final_identifiers
            
            # 处理匹配结果
            for identifier in matched_identifiers:
                if identifier not in found_blocks:
                    found_blocks[identifier] = []
                
                # 只添加一次该块到每个匹配的标识符
                # 检查是否已经添加过
                block_already_added = False
                for existing_block, _ in found_blocks[identifier]:
                    if existing_block.name == block.name:
                        block_already_added = True
                        break
                
                if not block_already_added:
                    found_blocks[identifier].append((block, material_info[identifier]))
                    logger.info(f"在DXF文件 {dxf_file} 中找到包含 {identifier} 的块: {block.name}")
        
        return found_blocks
    
    def _parse_thickness_value(self, thickness_str: str) -> float:
        """
        解析厚度字符串为数值，用于排序
        支持 "T2", "2.0", "2mm", "T2.5" 等格式
        """
        if not thickness_str:
            return 999999.0  # 未知厚度排在最后
        
        try:
            # 提取字符串中的所有数字（包括小数）
            import re
            match = re.search(r"(\d+(\.\d+)?)", str(thickness_str))
            if match:
                return float(match.group(1))
            return 999999.0
        except Exception:
            return 999999.0

    def merge_blocks(self, found_blocks: Dict[str, List[Any]], output_file: str,
                     center_align: bool = True,
                     block_spacing: float = 600.0,
                     edge_spacing: float = 100.0,
                     use_edge_spacing: bool = True,
                     group_spacing: float = 800.0,
                     attribs_config: Dict[str, bool] = None, # 替代旧的两个布尔参数
                     write_material_thickness_attrib: bool = None, # 兼容旧参数（如果有调用方）
                     write_id_drawing_name_attrib: bool = None,    # 兼容旧参数
                     label_height: float = 50.0,
                     label_color: int = 1,
                     thickness_label_height: float = 30.0,
                     thickness_label_color: int = 3,
                     remove_duplicates: bool = False) -> bool:
        """
        合并找到的块到一个新的DXF文件
        
        参数:
        found_blocks: 找到的块映射
        output_file: 输出文件路径
        center_align: 是否以块中心对齐 (True: 中心对齐, False: 底部对齐)
        block_spacing: 块之间的间距（当不使用边到边距离时）
        edge_spacing: 块边到边的距离（当使用边到边距离时）
        use_edge_spacing: 是否使用块边到边距离
        group_spacing: 组之间的间距
        attribs_config: 属性写入配置字典 { 'key': bool }
        label_height: 组标签高度
        label_color: 组标签颜色
        thickness_label_height: 厚度标签高度
        thickness_label_color: 厚度标签颜色
        remove_duplicates: 是否删除重复线
        
        返回:
        bool: 操作是否成功
        """
        try:
            unique_found_blocks = {}
            for identifier, blocks_with_info in found_blocks.items():
                if not blocks_with_info:
                    continue
                if len(blocks_with_info) > 1:
                    names = [b.name for b, _ in blocks_with_info if hasattr(b, "name")]
                    logger.info(f"图号重复，保留第一个块: {identifier}, 候选块: {names}")
                unique_found_blocks[identifier] = [blocks_with_info[0]]

            # 兼容旧参数处理
            if attribs_config is None:
                attribs_config = {}
                if write_material_thickness_attrib is not None:
                    attribs_config['material'] = write_material_thickness_attrib
                    attribs_config['thickness'] = write_material_thickness_attrib
                if write_id_drawing_name_attrib is not None:
                    attribs_config['material_id'] = write_id_drawing_name_attrib
                    attribs_config['drawing_num'] = write_id_drawing_name_attrib
                    attribs_config['name'] = write_id_drawing_name_attrib
            
            # 创建新的DXF文档，使用R2010版本以确保良好的兼容性
            new_doc = ezdxf.new(dxfversion='R2010')
            
            # 设置中文字体样式
            if 'SimHei' not in new_doc.styles:
                new_doc.styles.new('SimHei', dxfattribs={'font': 'simhei.ttf'})
            
            # 设置Standard样式，避免使用txt.shx
            if 'Standard' in new_doc.styles:
                std_style = new_doc.styles.get('Standard')
                std_style.dxf.font = 'arial.ttf'
            else:
                new_doc.styles.new('Standard', dxfattribs={'font': 'arial.ttf'})

            # 设置TSSD_Rein样式（常见的钢筋字体），如果不存在则映射到simhei.ttf
            if 'TSSD_Rein' not in new_doc.styles:
                new_doc.styles.new('TSSD_Rein', dxfattribs={'font': 'simhei.ttf'})

            new_msp = new_doc.modelspace()
            
            # 按材质和厚度两级分组：先按材质分组，再按厚度分行
            # 结构：{ material: { thickness: [(identifier, block, info), ...] } }
            grouped_blocks = {}

            # 遍历所有唯一标识符
            for identifier, blocks_with_info in unique_found_blocks.items():
                if not blocks_with_info:
                    continue

                # 遍历所有找到的块
                for block, info in blocks_with_info:
                    # 读取材质与厚度
                    material = info.get('material', '未知材质')
                    # 处理材质为空字符串的情况
                    if not material:
                        material = '未知材质'
                    thickness = info.get('thickness', '')
                    thickness = str(thickness).strip() if thickness is not None else ''

                    # 初始化二级字典
                    if material not in grouped_blocks:
                        grouped_blocks[material] = {}
                    if thickness not in grouped_blocks[material]:
                        grouped_blocks[material][thickness] = []

                    grouped_blocks[material][thickness].append((identifier, block, info))
            
            logger.info(f"处理 {len(grouped_blocks)} 个材质组")
            
            # 准备任务
            import_tasks = {}  # source_doc -> list of tasks
            block_ref_tasks = []  # list of reference placement info
            
            # 计算放置位置
            x = 0
            y = 0
            
            # 对分组后的数据进行排序
            # 1. 材质排序（字母顺序）
            sorted_materials = sorted(grouped_blocks.keys())
            
            # 遍历每个材质组（每个材质下按厚度分行）
            for group_index, material in enumerate(sorted_materials):
                thickness_groups = grouped_blocks[material]
                
                # 对厚度进行排序（从小到大）
                sorted_thicknesses = sorted(thickness_groups.keys(), key=self._parse_thickness_value)
                
                total_blocks_in_material = sum(len(lst) for lst in thickness_groups.values())
                logger.info(f"处理组: 材质={material}, 共{total_blocks_in_material}个块（分{len(thickness_groups)}个厚度行）")

                # 为当前组设置起始X坐标和起始Y坐标
                current_x_base = x
                
                # 行的初始Y坐标
                row_y = y

                # 遍历每个厚度行，保证相同厚度的块在同一行
                for thickness_index, thickness in enumerate(sorted_thicknesses):
                    blocks = thickness_groups[thickness]
                    # 计算本行所有块的边界框信息
                    block_bboxes = []
                    max_row_height = 0
                    
                    for block_index, (identifier, block, info) in enumerate(blocks):
                        center_x, center_y, bbox_w, bbox_h = compute_block_center_and_size(block)
                        block_bboxes.append((center_x, center_y, bbox_w, bbox_h))
                        max_row_height = max(max_row_height, bbox_h)

                    # 标签位置设置在行下方
                    # 如果是底部对齐，基准线 row_y 就是底部，标签应在 row_y 之下
                    # 如果是中心对齐，基准线 row_y 是中心，标签应在 row_y - max_row_height/2 之下
                    if center_align:
                        label_y_base = row_y - (max_row_height / 2.0)
                    else:
                        label_y_base = row_y
                    
                    # 添加厚度小标签
                    thickness_label = f"厚度: {thickness}" if thickness else "厚度: 未知"
                    new_msp.add_text(thickness_label,
                                     dxfattribs={
                                         'insert': (current_x_base, label_y_base - 50),
                                         'height': thickness_label_height,
                                         'layer': '0',
                                         'color': thickness_label_color,
                                         'style': 'SimHei'
                                     })
                    
                    # 只有第一行添加材质标签
                    if thickness_index == 0:
                        new_msp.add_text(f"材质: {material}",
                                         dxfattribs={
                                             'insert': (current_x_base, label_y_base - 100),
                                             'height': label_height,
                                             'layer': '0',
                                             'color': label_color,
                                             'style': 'SimHei'
                                         })

                    # 为本行设置起始X坐标
                    current_edge_x = current_x_base
                    current_center_x = current_x_base

                    # 遍历当前厚度组内的块
                    for block_index, (identifier, block, info) in enumerate(blocks):
                        center_x_block, center_y_block, bbox_w, bbox_h = block_bboxes[block_index]
                        
                        # 计算插入点 X 坐标
                        if use_edge_spacing:
                            gap = edge_spacing if block_index > 0 else 0
                            insert_x = current_edge_x + gap + (bbox_w / 2.0)
                            current_edge_x = insert_x + (bbox_w / 2.0)
                        else:
                            step = max(block_spacing, bbox_w + 50)
                            if block_index == 0:
                                insert_x = current_center_x + (bbox_w / 2.0)
                            else:
                                insert_x = current_center_x + step
                            current_center_x = insert_x
                        
                        # 计算插入点 Y 坐标
                        if center_align:
                            insert_y = row_y
                        else:
                            insert_y = row_y + (bbox_h / 2.0)

                        unique_block_name = f"BLOCK_{group_index}_{thickness_index}_{block_index}_{identifier}"
                        
                        # 记录导入任务
                        source_doc = block.doc
                        if source_doc not in import_tasks:
                            import_tasks[source_doc] = []
                        import_tasks[source_doc].append({
                            'target_block_name': unique_block_name,
                            'source_block': block,
                            'offset': (center_x_block, center_y_block),
                            'info': info
                        })

                        # 记录引用任务
                        block_ref_tasks.append({
                            'name': unique_block_name,
                            'insert': (insert_x, insert_y),
                            'info': info,
                            'material': material,
                            'thickness': thickness
                        })

                    # 准备下一行，下移距离考虑当前行高度和组间距
                    row_y -= (max_row_height + group_spacing)

                # 更新下一材质组的起始 Y
                y = row_y
            
            # 执行导入任务
            for source_doc, tasks in import_tasks.items():
                if not tasks:
                    continue
                try:
                    # 使用 Importer 跨文档复制实体
                    importer = Importer(source_doc, new_doc)
                    
                    # 将导入的实体分配给目标块
                    for i, task in enumerate(tasks):
                        target_name = task['target_block_name']
                        src_block = task['source_block']
                        offset_x, offset_y = task['offset']
                        info = task['info']
                        
                        # 收集源块中的实体（跳过视口等非图形实体）
                        ents = [e for e in src_block if e.dxftype() != 'VIEWPORT']
                        
                        if not ents:
                            continue

                        # 创建新的块定义
                        new_block = new_doc.blocks.new(name=target_name)
                        
                        try:
                            # 直接导入到新块中
                            importer.import_entities(ents, target_layout=new_block)
                            
                            # 遍历新块中的实体进行处理（平移和文本更新）
                            # 注意：import_entities 后实体已经在 new_block 中了
                            for ent in new_block:
                                # 1. 平移实体到原点
                                try:
                                    ent.translate(-offset_x, -offset_y, 0)
                                except Exception:
                                    pass
                                
                                # 2. 文本处理（替换数量或解码）
                                try:
                                    if ent.dxftype() in ('TEXT', 'MTEXT', 'ATTRIB'):
                                        text = ent.dxf.text
                                        # 先解码，确保能识别编码后的"共"字
                                        decoded_text = self._decode_unicode_escape(text)
                                        
                                        if decoded_text and '共' in decoded_text:
                                            # 替换数量信息
                                            new_text = decoded_text.split('共')[0] + f'共{info["total_qty"]}件'
                                            ent.dxf.text = new_text
                                        else:
                                            ent.dxf.text = decoded_text
                                except Exception:
                                    pass

                            # 3. 删除重复线（如果启用）
                            if remove_duplicates:
                                self._remove_duplicate_entities(new_block)

                        except Exception as e:
                             logger.error(f"导入实体到块 {target_name} 时出错: {e}")
                    
                    # 完成导入，解决依赖关系
                    importer.finalize()
                                
                except Exception as e:
                    logger.error(f"处理文档导入任务时出错: {e}")
                    logger.error(traceback.format_exc())
                    continue

            # 创建块引用
            for ref in block_ref_tasks:
                unique_block_name = ref['name']
                insert_x, insert_y = ref['insert']
                info = ref['info']
                material = ref['material']
                thickness = ref['thickness']
                
                # 添加块引用
                blkref = new_msp.add_blockref(unique_block_name, (insert_x, insert_y))
                
                # 添加属性
                if attribs_config:
                    try:
                        material_id_val = info.get('material_id', '')
                        drawing_num_val = info.get('drawing_num', '')
                        name_val = info.get('name', '')
                        total_qty_val = info.get('total_qty', '')
                        
                        # 材质
                        if attribs_config.get('material', False) and material:
                            blkref.add_attrib(
                                tag='材质',
                                text=str(material),
                                insert=(insert_x, insert_y),
                                dxfattribs={'height': 10, 'style': 'Standard'}
                            )
                        
                        # 厚度
                        if attribs_config.get('thickness', False) and thickness:
                            blkref.add_attrib(
                                tag='厚度',
                                text=str(thickness),
                                insert=(insert_x, insert_y),
                                dxfattribs={'height': 10, 'style': 'Standard'}
                            )
                            
                        # 物料ID
                        if attribs_config.get('material_id', False):
                            blkref.add_attrib(
                                tag='物料ID',
                                text=str(material_id_val),
                                insert=(insert_x, insert_y),
                                dxfattribs={'height': 10, 'style': 'Standard'}
                            )
                            
                        # 图号
                        if attribs_config.get('drawing_num', False):
                            blkref.add_attrib(
                                tag='图号',
                                text=str(drawing_num_val),
                                insert=(insert_x, insert_y),
                                dxfattribs={'height': 10, 'style': 'Standard'}
                            )
                            
                        # 名称
                        if attribs_config.get('name', False):
                            blkref.add_attrib(
                                tag='名称',
                                text=str(name_val),
                                insert=(insert_x, insert_y),
                                dxfattribs={'height': 10, 'style': 'Standard'}
                            )
                            
                        # 总数量 (新增)
                        if attribs_config.get('total_qty', False):
                            blkref.add_attrib(
                                tag='总数量',
                                text=str(total_qty_val),
                                insert=(insert_x, insert_y),
                                dxfattribs={'height': 10, 'style': 'Standard'}
                            )
                            
                    except Exception:
                        pass
            
            new_doc.saveas(output_file)
            try:
                _ = ezdxf.readfile(output_file)
            except Exception as _e:
                logger.error(f"保存后的DXF自检失败: {_e}")
                return False
            logger.info(f"成功将找到的块合并保存到: {output_file}")
            total_merged = len(block_ref_tasks)
            logger.info(f"共合并 {total_merged} 个唯一的块")
            return True
        except Exception as e:
            logger.error(f"合并块时出错: {e}")
            logger.error(traceback.format_exc())
            return False
    
    def _remove_duplicate_entities(self, layout):
        """
        删除布局中的重复实体（简单的几何去重）
        
        策略：
        1. 遍历所有实体，计算其几何特征哈希
        2. 如果特征哈希已存在，则标记为删除
        3. 删除标记的实体
        """
        try:
            seen_hashes = set()
            to_delete = []
            
            # 支持的实体类型
            supported_types = {'LINE', 'CIRCLE', 'ARC', 'POINT', 'LWPOLYLINE', 'POLYLINE'}
            
            for entity in layout:
                dxftype = entity.dxftype()
                if dxftype not in supported_types:
                    continue
                    
                entity_hash = None
                
                try:
                    if dxftype == 'LINE':
                        # 线段：起点和终点（无序）
                        start = (round(entity.dxf.start[0], 4), round(entity.dxf.start[1], 4))
                        end = (round(entity.dxf.end[0], 4), round(entity.dxf.end[1], 4))
                        # 排序起点和终点以忽略方向
                        pts = sorted([start, end])
                        entity_hash = ('LINE', pts[0], pts[1], entity.dxf.layer)
                        
                    elif dxftype == 'CIRCLE':
                        # 圆：圆心和半径
                        center = (round(entity.dxf.center[0], 4), round(entity.dxf.center[1], 4))
                        radius = round(entity.dxf.radius, 4)
                        entity_hash = ('CIRCLE', center, radius, entity.dxf.layer)
                        
                    elif dxftype == 'ARC':
                        # 圆弧：圆心、半径、起始角、终止角
                        center = (round(entity.dxf.center[0], 4), round(entity.dxf.center[1], 4))
                        radius = round(entity.dxf.radius, 4)
                        start_angle = round(entity.dxf.start_angle, 4)
                        end_angle = round(entity.dxf.end_angle, 4)
                        entity_hash = ('ARC', center, radius, start_angle, end_angle, entity.dxf.layer)
                        
                    elif dxftype == 'POINT':
                        # 点：位置
                        loc = (round(entity.dxf.location[0], 4), round(entity.dxf.location[1], 4))
                        entity_hash = ('POINT', loc, entity.dxf.layer)
                        
                    elif dxftype in ('LWPOLYLINE', 'POLYLINE'):
                        # 多段线：所有顶点
                        points = []
                        if hasattr(entity, 'get_points'):
                             # LWPOLYLINE
                            for p in entity.get_points():
                                points.append((round(p[0], 4), round(p[1], 4)))
                        elif hasattr(entity, 'vertices'):
                            # POLYLINE
                            for v in entity.vertices:
                                points.append((round(v.dxf.location[0], 4), round(v.dxf.location[1], 4)))
                        
                        # 简单的闭合检查
                        is_closed = entity.closed if hasattr(entity, 'closed') else False
                        
                        # 如果是闭合的，顶点的起始点不重要，但这比较复杂
                        # 这里只做简单的完全匹配
                        entity_hash = (dxftype, tuple(points), is_closed, entity.dxf.layer)
                
                except Exception:
                    continue
                
                if entity_hash:
                    if entity_hash in seen_hashes:
                        to_delete.append(entity)
                    else:
                        seen_hashes.add(entity_hash)
            
            # 执行删除
            for entity in to_delete:
                layout.delete_entity(entity)
                
            if to_delete:
                logger.info(f"删除了 {len(to_delete)} 个重复实体")
                
        except Exception as e:
            logger.warning(f"删除重复实体时出错: {e}")

    def update_excel_with_results(
        self,
        excel_file: str,
        found_identifiers: List[str],
        output_file: str,
        merged_identifier_map: Optional[Dict[str, str]] = None,
        identifier_to_dxf_file: Optional[Dict[str, str]] = None,
    ) -> bool:
        """
        更新Excel文件，添加找到/未找到标记

        参数:
        excel_file: 原始Excel文件路径
        found_identifiers: 找到的物料ID或图号列表
        output_file: 输出Excel文件路径
        merged_identifier_map: 被合并到代表块的标识符映射
        identifier_to_dxf_file: 标识符到匹配的DXF文件名的映射

        返回:
        bool: 操作是否成功
        """
        try:
            found_identifiers = set(found_identifiers)
            merged_identifier_map = merged_identifier_map or {}
            identifier_to_dxf_file = identifier_to_dxf_file or {}

            # 加载Excel文件
            df = pd.read_excel(excel_file)
            
            # 识别列
            column_map = self._identify_columns(df)
            material_id_col = column_map.get('material_id')
            drawing_num_col = column_map.get('drawing_num')
            
            # 添加结果列
            df['查找结果'] = '未找到'
            df['匹配类型'] = ''
            df['合并到标识符'] = ''
            df['匹配CAD文件'] = ''
            
            # 更新结果
            found_count = 0
            merged_count = 0
            for index, row in df.iterrows():
                row_status = '未找到'
                match_type = ''
                merged_to = ''

                # 检查物料ID
                if material_id_col and pd.notna(row[material_id_col]):
                    try:
                        material_id = str(int(row[material_id_col])).strip()
                    except (ValueError, TypeError):
                        material_id = str(row[material_id_col]).strip()
                    
                    # 规范化
                    material_id = self._normalize_identifier(material_id)
                    
                    if material_id in found_identifiers:
                        row_status = '已找到'
                        match_type = '物料ID'
                    elif material_id in merged_identifier_map:
                        row_status = '已合并'
                        match_type = '物料ID'
                        merged_to = merged_identifier_map[material_id]
                
                # 检查图号
                if drawing_num_col and pd.notna(row[drawing_num_col]):
                    drawing_num = str(row[drawing_num_col]).strip()
                    
                    # 规范化
                    drawing_num = self._normalize_identifier(drawing_num)
                    
                    if row_status == '未找到':
                        if drawing_num in found_identifiers:
                            row_status = '已找到'
                            match_type = '图号'
                        elif drawing_num in merged_identifier_map:
                            row_status = '已合并'
                            match_type = '图号'
                            merged_to = merged_identifier_map[drawing_num]

                # 确定匹配的CAD文件名
                matched_cad_file = ''
                if row_status in ('已找到', '已合并'):
                    # 优先检查物料ID对应的CAD文件
                    if material_id_col and pd.notna(row[material_id_col]):
                        try:
                            mid = str(int(row[material_id_col])).strip()
                        except (ValueError, TypeError):
                            mid = str(row[material_id_col]).strip()
                        mid = self._normalize_identifier(mid)
                        if mid in identifier_to_dxf_file:
                            matched_cad_file = identifier_to_dxf_file[mid]
                    # 如果物料ID没有匹配到CAD文件，尝试图号
                    if not matched_cad_file and drawing_num_col and pd.notna(row[drawing_num_col]):
                        dnum = str(row[drawing_num_col]).strip()
                        dnum = self._normalize_identifier(dnum)
                        if dnum in identifier_to_dxf_file:
                            matched_cad_file = identifier_to_dxf_file[dnum]
                    # 如果是已合并的，检查合并到的标识符
                    if not matched_cad_file and merged_to:
                        if merged_to in identifier_to_dxf_file:
                            matched_cad_file = identifier_to_dxf_file[merged_to]

                df.at[index, '查找结果'] = row_status
                df.at[index, '匹配类型'] = match_type
                df.at[index, '合并到标识符'] = merged_to
                df.at[index, '匹配CAD文件'] = matched_cad_file

                if row_status == '已找到':
                    found_count += 1
                elif row_status == '已合并':
                    merged_count += 1
            
            # 保存更新后的文件
            df.to_excel(output_file, index=False)
            logger.info(f"成功更新Excel文件并保存到: {output_file}")
            logger.info(f"在Excel文件中找到 {found_count} 个匹配项")
            logger.info(f"在Excel文件中标记了 {merged_count} 个已合并项")
            return True
        except Exception as e:
            logger.error(f"更新Excel文件时出错: {e}")
            logger.error(traceback.format_exc())
            return False

    def _decode_unicode_escape(self, text: str) -> str:
        """
        解码Unicode转义序列，将类似 \\U+XXXX、\\UXXXX、\\u+XXXX、\\uXXXX 这样的序列转换为对应的Unicode字符

        参数:
        text: 包含Unicode转义序列的文本

        返回:
        str: 解码后的文本
        """
        if not text:
            return text
        
        try:
            import re
            
            def _decode_unicode(m):
                hexstr = m.group(1)
                try:
                    # 支持4-6位十六进制数
                    cp = int(hexstr, 16)
                    return chr(cp)
                except Exception:
                    return m.group(0)
            
            # 处理多种Unicode转义序列格式
            decoded_text = re.sub(r'\\U\+([0-9A-Fa-f]{4,6})', _decode_unicode, text)
            decoded_text = re.sub(r'\\U([0-9A-Fa-f]{4,6})', _decode_unicode, decoded_text)
            decoded_text = re.sub(r'\\u\+([0-9A-Fa-f]{4})', _decode_unicode, decoded_text)
            decoded_text = re.sub(r'\\u([0-9A-Fa-f]{4})', _decode_unicode, decoded_text)
            
            return decoded_text
        except Exception as e:
            logger.warning(f"解码Unicode转义序列时出错: {e}")
            return text
    
    def _filter_blocks_by_priority(self, all_found_blocks: Dict[str, List[Any]], material_info: Dict[str, Dict[str, Any]], progress_callback=None):
        """
        根据优先级过滤找到的块：
        对于每一行数据，如果物料ID已经找到了对应的块，则移除该行图号找到的块。
        这样可以避免重复，并优先使用物料ID的匹配结果。
        
        参数:
        all_found_blocks: 找到的块映射 {identifier: [blocks]}
        material_info: 物料信息映射 {identifier: info}
        """
        # 1. 按行构建映射：row_index -> { 'mat_found': False, 'draw_nums': [] }
        # 注意：一个identifier可能对应多个行，我们需要遍历 row_allocations
        rows_map = {}
        
        for identifier, info in material_info.items():
            # 获取该标识符关联的所有行
            row_allocations = info.get('row_allocations', {})
            # 如果没有行分配信息，尝试使用 row_index
            if not row_allocations and info.get('row_index') is not None:
                row_allocations = {info.get('row_index'): info.get('total_qty', 0)}
            
            id_type = info.get('id_type', 'unknown')
            
            for row_idx in row_allocations:
                if row_idx not in rows_map:
                    rows_map[row_idx] = {'mat_found': False, 'draw_nums': []}
                
                if id_type == 'material_id':
                    # 如果是物料ID，且已找到块，标记该行已由物料ID覆盖
                    if identifier in all_found_blocks and all_found_blocks[identifier]:
                        rows_map[row_idx]['mat_found'] = True
                elif id_type == 'drawing_num':
                    # 如果是图号，记录下来待检查
                    rows_map[row_idx]['draw_nums'].append(identifier)
        
        # 2. 遍历每一行进行过滤
        skipped_qty_total = 0
        removed_identifiers = 0
        
        for row_idx, data in rows_map.items():
            if data['mat_found']:
                # 该行已由物料ID覆盖，需要减少图号的贡献数量
                for did in data['draw_nums']:
                    if did in all_found_blocks and all_found_blocks[did]:
                        # 获取图号的 info 对象（共享的）
                        info = material_info[did]
                        
                        # 获取该图号在当前行的分配数量
                        row_allocs = info.get('row_allocations', {})
                        qty_in_row = row_allocs.get(row_idx, 0)
                        
                        if qty_in_row > 0:
                            # 减少数量
                            del row_allocs[row_idx]
                            info['total_qty'] -= qty_in_row
                            skipped_qty_total += qty_in_row
                            
                            # 如果该图号的总数量归零，说明其所有需求都已被物料ID覆盖
                            if info['total_qty'] <= 0:
                                if did in all_found_blocks:
                                    del all_found_blocks[did]
                                    removed_identifiers += 1
                                    if progress_callback:
                                        self._log_progress(progress_callback, f"图号 {did} 的所有需求均已被物料ID覆盖，移除该匹配结果")
        
        if skipped_qty_total > 0:
            if progress_callback:
                self._log_progress(progress_callback, f"共减少了 {skipped_qty_total} 件由图号匹配但已由物料ID覆盖的块需求，彻底移除了 {removed_identifiers} 个图号结果")

    def _get_block_content_key(self, block, recursion_depth=0):
        """
        生成块内容的唯一键（指纹），用于识别不同名称但内容相同的块。
        为了提高去重的鲁棒性，忽略文本、点等非几何实体，并降低坐标精度。
        """
        if recursion_depth > 2:  # 限制递归深度，防止无限递归
            # 如果是 Insert 对象，返回名字
            if hasattr(block, 'dxf'):
                return (block.dxf.name,)
            return (str(block),)

        # 关键修正：如果传入的是 Insert 实体（块引用），我们需要获取其对应的 Block Definition（块定义）
        # 因为直接遍历 Insert 实体只会得到属性（ATTRIB）和顶点（如果是多段线），而得不到块内的几何体。
        target_block = block
        if hasattr(block, 'dxftype') and block.dxftype() == 'INSERT':
            if block.doc and block.dxf.name in block.doc.blocks:
                target_block = block.doc.blocks.get(block.dxf.name)
            else:
                # 无法找到定义，只能退回到使用名字（可能是不在库中的块？）
                return (block.dxf.name,)

        entities_data = []
        precision = 2  # 降低精度到2位小数（0.01mm），忽略微小差异
        
        for entity in target_block:
            try:
                dxftype = entity.dxftype()
                
                # 忽略视口、点、文本、属性定义等非几何构件
                if dxftype in ('VIEWPORT', 'POINT', 'TEXT', 'MTEXT', 'ATTDEF', 'ATTRIB'):
                    continue
                
                # 基础数据：类型（不再包含图层，避免图层不同导致不匹配）
                ent_data = [dxftype]
                
                if dxftype == 'LINE':
                    # 对线段端点排序，确保方向无关
                    p1 = tuple(round(c, precision) for c in entity.dxf.start)
                    p2 = tuple(round(c, precision) for c in entity.dxf.end)
                    pts = sorted([p1, p2])
                    ent_data.append(tuple(pts))
                    
                elif dxftype == 'CIRCLE':
                    center = tuple(round(c, precision) for c in entity.dxf.center)
                    radius = round(entity.dxf.radius, precision)
                    ent_data.append(center)
                    ent_data.append(radius)
                    
                elif dxftype == 'ARC':
                    center = tuple(round(c, precision) for c in entity.dxf.center)
                    radius = round(entity.dxf.radius, precision)
                    start_angle = round(entity.dxf.start_angle, precision)
                    end_angle = round(entity.dxf.end_angle, precision)
                    ent_data.append(center)
                    ent_data.append(radius)
                    ent_data.append(start_angle)
                    ent_data.append(end_angle)
                    
                elif dxftype in ('LWPOLYLINE', 'POLYLINE'):
                    if dxftype == 'LWPOLYLINE':
                        points = entity.get_points()
                        # (x, y, start_width, end_width, bulge)
                        raw_pts = [ (round(p[0], precision), round(p[1], precision), round(p[4], precision)) for p in points ]
                    else:
                        # POLYLINE 2D/3D
                        raw_pts = [ tuple(round(c, precision) for c in v.dxf.location) for v in entity.vertices ]
                    
                    # 尝试规范化多段线顶点顺序（处理起点不同但形状相同的情况）
                    # 仅针对闭合多段线有效，但即使不闭合，尝试排序起始点也是一种策略
                    # 这里采用简单策略：寻找字典序最小的点作为起点，并重新排列
                    # 注意：需要保持点的相对顺序（顺时针/逆时针），不能随意sort
                    if raw_pts:
                        # 找到最小点的索引
                        min_idx = 0
                        min_pt = raw_pts[0]
                        for i, pt in enumerate(raw_pts):
                            if pt < min_pt:
                                min_pt = pt
                                min_idx = i
                        
                        # 旋转列表
                        if min_idx > 0:
                            raw_pts = raw_pts[min_idx:] + raw_pts[:min_idx]
                        
                        # TODO: 还可以考虑反转（逆时针/顺时针），但暂不处理，以免破坏手性
                    
                    ent_data.append(tuple(raw_pts))
                    
                elif dxftype == 'INSERT':
                    # 递归获取嵌套块的内容指纹
                    block_name = entity.dxf.name
                    nested_fingerprint = None
                    if block.doc and block_name in block.doc.blocks:
                        nested_block = block.doc.blocks.get(block_name)
                        nested_fingerprint = self._get_block_content_key(nested_block, recursion_depth + 1)
                    else:
                        nested_fingerprint = block_name # 无法获取定义，只能用名字

                    insert = tuple(round(c, precision) for c in entity.dxf.insert)
                    xscale = round(entity.dxf.get('xscale', 1.0), precision)
                    yscale = round(entity.dxf.get('yscale', 1.0), precision)
                    rotation = round(entity.dxf.rotation, precision)
                    
                    ent_data.append(nested_fingerprint) # 使用内容指纹代替名字
                    ent_data.append(insert)
                    ent_data.append(xscale)
                    ent_data.append(yscale)
                    ent_data.append(rotation)
                
                elif dxftype == 'ELLIPSE':
                    center = tuple(round(c, precision) for c in entity.dxf.center)
                    major_axis = tuple(round(c, precision) for c in entity.dxf.major_axis)
                    ratio = round(entity.dxf.ratio, precision)
                    start_param = round(entity.dxf.start_param, precision)
                    end_param = round(entity.dxf.end_param, precision)
                    ent_data.append(center)
                    ent_data.append(major_axis)
                    ent_data.append(ratio)
                    ent_data.append(start_param)
                    ent_data.append(end_param)
                
                entities_data.append(tuple(ent_data))
                
            except Exception:
                continue
        
        # 对实体数据进行排序，确保实体顺序无关
        entities_data.sort(key=lambda x: str(x))
        return tuple(entities_data)

    def _dedupe_blocks_by_content(self, all_found_blocks: Dict[str, List[Any]], progress_callback=None):
        """
        在每个标识符维度内去除内容重复的块，并合并数量信息。
        """
        removed_count = 0
        for identifier, blocks_with_info in list(all_found_blocks.items()):
            if not blocks_with_info:
                continue

            seen = {}
            deduped_list = []

            for block, info in blocks_with_info:
                block_key = self._get_block_content_key(block)
                if not block_key:
                    block_key = block.name

                if block_key not in seen:
                    seen[block_key] = info
                    deduped_list.append((block, info))
                    continue

                existing_info = seen[block_key]
                current_allocations = info.get('row_allocations', {})
                if not current_allocations:
                    current_allocations = {info.get('row_index', -1): info.get('total_qty', 0)}

                if 'accumulated_rows' not in existing_info:
                    base_allocations = existing_info.get('row_allocations', {})
                    if not base_allocations:
                        base_allocations = {existing_info.get('row_index', -1): existing_info.get('total_qty', 0)}
                    existing_info['accumulated_rows'] = base_allocations

                added_qty = 0
                for r_idx, r_qty in current_allocations.items():
                    if r_idx not in existing_info['accumulated_rows']:
                        existing_info['accumulated_rows'][r_idx] = r_qty
                        added_qty += r_qty

                if added_qty > 0:
                    existing_info['total_qty'] = sum(existing_info['accumulated_rows'].values())

                removed_count += 1

            all_found_blocks[identifier] = deduped_list

        if removed_count > 0 and progress_callback:
            self._log_progress(progress_callback, f"去除重复块 {removed_count} 个（同标识符内）")

    def process_files(self, excel_file: str, dxf_files: List[str], output_dir: str,
                      center_align: bool = True,
                      use_edge_spacing: bool = True,
                      block_spacing: float = 600.0,
                      edge_spacing: float = 100.0,
                      group_spacing: float = 800.0,
                      attribs_config: Dict[str, bool] = None, # 新增参数
                      write_material_thickness_attrib: bool = None, # 兼容参数
                      write_id_drawing_name_attrib: bool = None,    # 兼容参数
                      text_strategy: str = 'first_valid',
                      remove_duplicates: bool = False,
                      progress_callback=None) -> bool:
        """
        处理文件，执行完整的筛寻和合并流程
        
        参数:
        excel_file: Excel文件路径
        dxf_files: DXF文件列表
        output_dir: 输出目录
        center_align: 是否以块中心对齐
        use_edge_spacing: 是否使用块边到边距离
        block_spacing: 块之间的间距（当不使用边到边距离时）
        edge_spacing: 块边到边的距离（当使用边到边距离时）
        group_spacing: 组之间的间距
        attribs_config: 属性写入配置字典
        text_strategy: 文本选择策略
        remove_duplicates: 是否删除重复线
        progress_callback: 进度回调函数
        
        返回:
        bool: 操作是否成功
        """
        try:
            # 兼容旧参数处理
            if attribs_config is None:
                attribs_config = {}
                # 只有当显式传递了 True 时才设置，或者根据旧逻辑默认行为
                # 旧逻辑中这两个参数默认是 True，但这里参数默认值是 None
                # 如果调用方没传，我们假设需要保持默认行为吗？
                # 查看原定义：write_material_thickness_attrib: bool = True
                
                # 如果参数是 None，说明没有被传递（使用了默认值 None），我们需要确定默认行为
                # 为了保持向后兼容，如果旧参数未传（None），我们应该根据旧的默认值（True）来设置吗？
                # 但是 wait, 在这个函数签名修改前，默认值是 True。
                # 所以如果调用者依赖默认值，我们应该默认为 True。
                
                mat_thick_val = write_material_thickness_attrib if write_material_thickness_attrib is not None else True
                id_draw_val = write_id_drawing_name_attrib if write_id_drawing_name_attrib is not None else True
                
                attribs_config['material'] = mat_thick_val
                attribs_config['thickness'] = mat_thick_val
                attribs_config['material_id'] = id_draw_val
                attribs_config['drawing_num'] = id_draw_val
                attribs_config['name'] = id_draw_val
            
            # 设置文本策略
            self.text_strategy = text_strategy
            
            # 确保输出目录存在
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
                self._log_progress(progress_callback, f"创建输出目录: {output_dir}")
            
            # 加载Excel文件
            self._log_progress(progress_callback, "加载Excel文件...")
            df = self.load_excel(excel_file)
            if df is None:
                self._log_progress(progress_callback, "错误: 无法加载Excel文件")
                return False
            
            # 提取物料信息
            self._log_progress(progress_callback, "提取物料信息...")
            material_info = self.extract_material_info(df)
            if not material_info:
                self._log_progress(progress_callback, "错误: 无法提取物料信息")
                return False
            
            self._log_progress(progress_callback, f"成功提取 {len(material_info)} 个物料信息")
            
            # 在所有DXF文件中搜索块
            self._log_progress(progress_callback, f"开始在 {len(dxf_files)} 个DXF文件中搜索块...")
            all_found_blocks = {}
            processed_blocks = {}  # 用于跟踪已处理的块 (key -> {'info': info, 'identifier': identifier})
            merged_identifier_map = {}  # 被合并到代表块的标识符 -> 代表标识符
            identifier_to_dxf_file = {}  # 标识符 -> 匹配的DXF文件名
            total_dxf_files = len(dxf_files)
            
            # 构建备注值到标识符的映射，用于按备注匹配DXF文件名筛选
            remark_to_identifiers = {}  # remark_value -> set of identifiers
            no_remark_identifiers = set()  # 没有备注的标识符
            
            for identifier, info in material_info.items():
                remarks = info.get('remarks', [])
                if not remarks:
                    no_remark_identifiers.add(identifier)
                else:
                    for remark in remarks:
                        remark_to_identifiers.setdefault(remark, set()).add(identifier)
            
            # 确定每个DXF文件对应的备注匹配结果，以及哪些备注未匹配任何文件
            matched_remarks = set()  # 至少匹配一个DXF文件的备注值
            file_to_identifiers = {}  # dxf_file -> set of identifiers to search
            
            for dxf_file in dxf_files:
                dxf_basename = os.path.splitext(os.path.basename(dxf_file))[0]
                file_identifiers = set(no_remark_identifiers)  # 始终包含无备注的标识符
                
                for remark, identifiers in remark_to_identifiers.items():
                    if self._remark_matches_file(remark, dxf_basename):
                        file_identifiers.update(identifiers)
                        matched_remarks.add(remark)
                
                file_to_identifiers[dxf_file] = file_identifiers
            
            # 备注值未匹配任何DXF文件的标识符，应在所有文件中搜索（回退行为）
            unmatched_remark_identifiers = set()
            for remark, identifiers in remark_to_identifiers.items():
                if remark not in matched_remarks:
                    unmatched_remark_identifiers.update(identifiers)
            
            if unmatched_remark_identifiers:
                for dxf_file in dxf_files:
                    file_to_identifiers[dxf_file].update(unmatched_remark_identifiers)
            
            # 日志输出备注匹配信息
            if remark_to_identifiers:
                self._log_progress(progress_callback, f"备注匹配: {len(matched_remarks)} 个备注值匹配到DXF文件, {len(remark_to_identifiers) - len(matched_remarks)} 个备注值未匹配")
                for remark in sorted(matched_remarks):
                    matched_files = [os.path.basename(f) for f in dxf_files 
                                     if self._remark_matches_file(remark, os.path.splitext(os.path.basename(f))[0])]
                    self._log_progress(progress_callback, f"  备注 '{remark}' -> 匹配文件: {', '.join(matched_files)}")
            
            for i, dxf_file in enumerate(dxf_files, 1):
                relevant_identifiers = file_to_identifiers.get(dxf_file, set(no_remark_identifiers))
                
                if not relevant_identifiers:
                    self._log_progress(progress_callback, f"跳过DXF文件 {i}/{total_dxf_files}: {os.path.basename(dxf_file)} (无匹配的标识符)")
                    continue
                
                # 构建当前文件需要搜索的物料信息子集
                filtered_material_info = {k: v for k, v in material_info.items() if k in relevant_identifiers}
                
                self._log_progress(progress_callback, f"处理DXF文件 {i}/{total_dxf_files}: {os.path.basename(dxf_file)} (搜索 {len(filtered_material_info)}/{len(material_info)} 个标识符)")
                found_blocks = self.search_blocks_in_dxf(dxf_file, filtered_material_info)
                
                # 记录找到的标识符对应的DXF文件（首次匹配）
                for identifier in found_blocks.keys():
                    if identifier not in identifier_to_dxf_file:
                        identifier_to_dxf_file[identifier] = os.path.basename(dxf_file)
                
                # 按优先级排序标识符：物料ID优先于图号
                # 这样可以确保物料ID优先“认领”块，从而在后续的去重逻辑中保留物料ID的匹配结果
                sorted_identifiers = sorted(found_blocks.keys(), key=lambda k: 0 if material_info[k].get('id_type') == 'material_id' else 1)
                
                for identifier in sorted_identifiers:
                    blocks = found_blocks[identifier]
                    
                    # 即使 identifier 已经在 all_found_blocks 中，也需要处理（因为可能是新的文件中的同名零件）
                    # 之前的逻辑跳过了后续文件的同名零件，导致数量不正确
                    
                    # 如果是首次遇到该标识符
                    if identifier not in all_found_blocks:
                        all_found_blocks[identifier] = []

                    # 处理当前找到的块
                    # 确保只添加唯一的块（按块内容去重），并处理同一块被不同标识符匹配时的数量累加
                    unique_blocks = []
                    
                    # 已经存在的块列表（来自之前的DXF文件）
                    existing_blocks_list = all_found_blocks[identifier]

                    for block, info in blocks:
                        # 计算块内容的指纹
                        block_fingerprint = self._get_block_content_key(block)
                        
                        # 如果指纹为空（空块？），回退到使用块名
                        if not block_fingerprint:
                            block_key = block.name
                        else:
                            block_key = block_fingerprint

                        if block_key not in processed_blocks:
                            # 这是一个全新的块内容（在任何标识符下都没见过）
                            
                            # 初始化块的已处理行集合
                            if 'row_allocations' in info:
                                info['accumulated_rows'] = info['row_allocations'].copy()
                            else:
                                info['accumulated_rows'] = {info.get('row_index', -1): info.get('total_qty', 0)}
                            
                            info['total_qty'] = sum(info['accumulated_rows'].values())
                            
                            # 添加到当前标识符的列表中
                            existing_blocks_list.append((block, info))
                            
                            # 当前标识符已经拥有自己的代表块，不再视为“合并到别人”
                            merged_identifier_map.pop(identifier, None)

                            # 记录该块的信息对象
                            processed_blocks[block_key] = {
                                'info': info,
                                'identifier': identifier,
                            }
                        else:
                            # 如果该块内容已被处理（可能在之前的DXF文件中，或者被其他标识符处理过）
                            existing_entry = processed_blocks[block_key]
                            existing_info = existing_entry['info']
                            representative_identifier = existing_entry['identifier']
                            
                            # 检查这个块是否已经在当前标识符的列表中了
                            # 如果不在（比如它是被其他标识符引入的），我们需要将它添加到当前标识符吗？
                            # 不，我们只需要确保数量被累加到 existing_info 中。
                            # 但是，如果 existing_info 所属的块不在 existing_blocks_list 中，
                            # 那么当前标识符就“拥有”这个块的引用吗？
                            # 逻辑是：如果 Block A 被 ID1 引用，那么 ID2 引用 Block B (==A) 时，
                            # 应该增加 Block A 的数量，并且 ID2 应该也指向 Block A？
                            # 目前的代码结构是：all_found_blocks[ID] = [(Block, Info), ...]
                            # Info 对象是被共享的 (通过 processed_blocks)。
                            # 所以只要 Info 更新了，所有引用该 Info 的地方都会更新。
                            # 关键是：ID2 的列表中是否需要添加 (Block A, Info)？
                            # 如果 ID2 之前没有引用过 Block A，那么需要添加。
                            # 但是 Block A 是 ezdxf 对象，来自 File 1。当前 block 是 File 2 的对象。
                            # 我们不能把 File 1 的 Block A 添加到 File 2 的处理逻辑中... 
                            # 不对，all_found_blocks 最终用于 merge_blocks。
                            # merge_blocks 会读取 block 对象。
                            # 如果 ID2 的列表是空的，merge_blocks 就会跳过 ID2。
                            # 所以我们需要把 existing_info 对应的 block 添加到 ID2 的列表中吗？
                            # 或者，如果 ID2 和 ID1 指向同一个物理零件，我们只需要保留一个即可？
                            # 按照 merge_blocks 的逻辑：
                            # for identifier, blocks_with_info in found_blocks.items():
                            #     for block, info in blocks_with_info:
                            #         ...
                            # 如果我们不把块加到 ID2，ID2 就不会输出块。
                            # 如果加了，ID2 会输出块。
                            # 如果 ID1 和 ID2 是同一行数据的不同标识符（物料ID vs 图号），
                            # 后面有 _filter_blocks_by_priority 来删除 图号。
                            # 如果 ID1 和 ID2 是不同行... 那么它们都需要输出块（或者合并数量）。
                            # 现在的逻辑是：processed_blocks[block_key] = info。
                            # 这个 info 是第一次遇到该内容时创建的 info。
                            # 所有的后续遇到（无论哪个ID，无论哪个文件）都更新这个 info 的 quantity。
                            # 那么，最终输出时，这个 info.total_qty 是总数。
                            # 问题是：这个 info 关联的 block 对象只存在于第一个发现它的 ID 的列表中。
                            # 其他 ID 如果也引用这个内容，它们应该也需要一个条目吗？
                            # 如果 ID1 和 ID2 不同，且指向相同内容。
                            # 比如 ID1 (Row 1) -> Block A. ID2 (Row 2) -> Block B (==A).
                            # info (from A) gets qty from Row 1 + Row 2.
                            # ID1 list has (Block A, info).
                            # ID2 list has... nothing?
                            # 结果：merge_blocks 遍历 ID1，输出 Block A，数量为 Total.
                            # 遍历 ID2，空列表，跳过。
                            # 最终结果：1个块，数量正确。
                            # 这似乎是符合预期的“合并”。
                            
                            # 但是，如果 ID1 和 ID2 是完全不同的零件（只是长得一样），
                            # 比如两个不同料号的板子，形状一样。
                            # 用户可能希望在 DXF 中看到两个图，分别标记 ID1 和 ID2？
                            # 如果是这样，那么我们的“内容去重”就太激进了。
                            # 但是用户的诉求是“筛出的块有双份的情况”，说明他们想要合并。
                            # 所以目前的“合并所有相同几何体到一个条目”的策略应该是对的。
                            
                            # 回到跨文件问题：
                            # File 1: ID1 -> Block A. processed_blocks[fp(A)] = infoA. all_found_blocks[ID1] = [(A, infoA)].
                            # File 2: ID1 -> Block A'. fp(A') == fp(A).
                            # 查 processed_blocks，找到 infoA.
                            # 更新 infoA quantity.
                            # ID1 list 已经有 (A, infoA).
                            # 不需要添加 (A', infoA)。
                            # 结果：ID1 对应 Block A，数量包括 File 1 和 File 2 的。
                            # 这是正确的。
                            
                            # 唯一的问题是：如果是不同的 ID？
                            # File 1: ID1 -> Block A.
                            # File 2: ID2 -> Block B (==A).
                            # ID2 list is empty. infoA gets qty.
                            # Output: ID1 block with total qty. ID2 gets nothing.
                            # 这也符合“合并”。
                            
                            # 所以，结论是：
                            # 1. 只要更新 quantity 即可。
                            # 2. 不需要把 duplicate block 添加到 list 中（除非 list 为空且我们需要它代表该 ID？）
                            # 如果 ID2 是新的，且我们不加任何东西到 all_found_blocks[ID2]，
                            # 那么 update_excel 可能会认为 ID2 "Found" (因为 key 存在)，但 DXF 中没有 ID2 的图。
                            # 这可能导致困惑（Excel 说找到了，图里没有）。
                            # 但既然几何体一样，且数量合并了，图里有一个就够了。
                            # 如果用户希望看到 ID2 的标签... 那就麻烦了。
                            # 目前 merge_blocks 只打一个标签（基于第一个 ID）。
                            
                            # 实施：
                            
                            # 获取当前标识符的行分配信息
                            current_allocations = info.get('row_allocations', {})
                            if not current_allocations:
                                    current_allocations = {info.get('row_index', -1): info.get('total_qty', 0)}
                            
                            if 'accumulated_rows' not in existing_info:
                                existing_info['accumulated_rows'] = {existing_info.get('row_index', -1): existing_info.get('total_qty', 0)}
                            
                            # 合并新的行分配信息
                            added_qty = 0
                            for r_idx, r_qty in current_allocations.items():
                                if r_idx not in existing_info['accumulated_rows']:
                                    existing_info['accumulated_rows'][r_idx] = r_qty
                                    added_qty += r_qty
                            
                            if added_qty > 0:
                                existing_info['total_qty'] = sum(existing_info['accumulated_rows'].values())
                                self._log_progress(progress_callback, f"块 {block.name} (或同内容块) 由标识符 {identifier} 补充了 {added_qty} 件，总计: {existing_info['total_qty']}")
                            else:
                                self._log_progress(progress_callback, f"块 {block.name} 由标识符 {identifier} 引用，但所有行均已包含在内，不累加数量")

                            if identifier != representative_identifier:
                                merged_identifier_map.setdefault(identifier, representative_identifier)
                            
                            # 关键修正：如果我们没有向 existing_blocks_list 添加任何东西，
                            # 且它是该标识符的第一个块... 
                            # 如果 identifier 已经在 all_found_blocks 中（来自前一个文件），它可能有块。
                            # 如果是新 ID，列表为空。
                            # 如果列表为空，update_excel 会认为找到了吗？
                            # update_excel 检查 key 是否在 found_identifiers 中。
                            # all_found_blocks.keys() 包含 ID。
                            # 所以 Excel 会更新。
                            # DXF 只有一个块。
                            # 看起来是合理的。

                    # 记录日志
                    if not existing_blocks_list:
                         # 如果列表为空，说明该标识符找到的所有块都已合并到其他地方
                         self._log_progress(progress_callback, f"标识符 {identifier} 的块均已合并到现有块中")
                    else:
                         # 这里的日志可能不准确，因为 existing_blocks_list 包含累积的块
                         pass
            
            # 检查是否找到任何块
            if not all_found_blocks:
                self._log_progress(progress_callback, "警告: 未找到任何匹配的块")
                return False
            
            # 过滤块：如果物料ID已找到，则跳过同行的图号
            self._filter_blocks_by_priority(all_found_blocks, material_info, progress_callback)

            # 去除同标识符内的重复块（避免原块未清理导致的双份）
            self._dedupe_blocks_by_content(all_found_blocks, progress_callback)
            
            visible_found_blocks = {
                identifier: blocks_with_info
                for identifier, blocks_with_info in all_found_blocks.items()
                if blocks_with_info
            }
            visible_identifiers = set(visible_found_blocks.keys())
            resolved_merged_identifier_map = self._resolve_merged_identifier_map(
                merged_identifier_map,
                visible_identifiers,
            )

            if not visible_found_blocks:
                self._log_progress(progress_callback, "警告: 经过筛选与合并后，没有可输出的代表块")
                return False

            # 合并找到的块
            self._log_progress(progress_callback, f"开始合并 {len(visible_found_blocks)} 个块...")
            merged_file = os.path.join(output_dir, 'merged_blocks.dxf')
            merge_success = self.merge_blocks(visible_found_blocks, merged_file,
                                              center_align=center_align,
                                              block_spacing=block_spacing,
                                              edge_spacing=edge_spacing,
                                              use_edge_spacing=use_edge_spacing,
                                              group_spacing=group_spacing,
                                              attribs_config=attribs_config,
                                              remove_duplicates=remove_duplicates)
            
            if not merge_success:
                self._log_progress(progress_callback, "错误: 合并块失败")
                return False
            
            # 更新Excel文件
            self._log_progress(progress_callback, "更新Excel文件...")
            found_identifiers = list(visible_found_blocks.keys())
            updated_excel_file = os.path.join(output_dir, 'updated_' + os.path.basename(excel_file))
            excel_success = self.update_excel_with_results(
                excel_file,
                found_identifiers,
                updated_excel_file,
                merged_identifier_map=resolved_merged_identifier_map,
                identifier_to_dxf_file=identifier_to_dxf_file,
            )
            
            if not excel_success:
                self._log_progress(progress_callback, "警告: 更新Excel文件失败，但块合并成功")
            
            # 完成
            self._log_progress(progress_callback, f"\n{'='*60}")
            self._log_progress(progress_callback, "处理完成！")
            self._log_progress(progress_callback, f"合并后的块文件: {merged_file}")
            self._log_progress(progress_callback, f"更新后的Excel文件: {updated_excel_file}")
            self._log_progress(progress_callback, f"共找到并处理 {len(visible_found_blocks)} 个代表块")
            if resolved_merged_identifier_map:
                self._log_progress(progress_callback, f"另有 {len(resolved_merged_identifier_map)} 个标识符复用了已有代表块")
            self._log_progress(progress_callback, f"{'='*60}")
            
            return True
        except Exception as e:
            self._log_progress(progress_callback, f"错误: 处理过程中发生异常 - {str(e)}")
            logger.error(f"处理文件时出错: {e}")
            logger.error(traceback.format_exc())
            return False

    def _log_progress(self, callback, message):
        """
        记录进度信息
        
        参数:
        callback: 回调函数
        message: 进度消息
        """
        logger.info(message)
        if callback:
            try:
                callback(message)
            except Exception:
                pass

# 示例用法
if __name__ == "__main__":
    finder = BlockFinder()
    excel_file = "1111.xlsx"
    dxf_files = []  # 需要指定DXF文件路径
    output_dir = "output"
    finder.process_files(excel_file, dxf_files, output_dir)
