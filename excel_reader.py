import os
import logging
import pandas as pd
from typing import Dict, Optional, Tuple

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ExcelReader:
    """
    Excel读取器，负责从Excel文件中读取物料ID、图号和总数量信息
    """
    
    def __init__(self, file_path: Optional[str] = None):
        """
        初始化Excel读取器
        
        参数:
        file_path: Excel文件路径
        """
        self.file_path = file_path
        self.data: Optional[pd.DataFrame] = None
        self.material_mapping: Dict[str, int] = {}  # 物料ID或图号到总数量的映射
        self.row_data_mapping: Dict[str, Dict] = {} # 物料ID或图号到完整行数据的映射
    
    def load_file(self) -> bool:
        """
        加载Excel文件
        
        返回:
        bool: 是否加载成功
        """
        if not self.file_path or not os.path.exists(self.file_path):
            logger.error(f"Excel文件不存在: {self.file_path}")
            return False
        
        try:
            # 读取Excel文件
            self.data = pd.read_excel(self.file_path)
            logger.info(f"成功加载Excel文件: {self.file_path}")
            logger.info(f"Excel文件包含 {len(self.data)} 行数据")
            logger.info(f"Excel文件列名: {list(self.data.columns)}")
            return True
        except Exception as e:
            logger.error(f"加载Excel文件时出错: {e}")
            return False
    
    def build_material_mapping(self) -> Dict[str, tuple]:
        """
        构建物料ID或图号到总数量和数量列表的映射
        
        返回:
        Dict[str, tuple]: 物料ID或图号到(total_qty, quantities_list)的映射
        """
        if self.data is None:
            logger.error("Excel文件未加载")
            return {}
        
        try:
            mapping = {}  # 存储 (总数量, [每次的数量])
            
            # 尝试识别物料ID、图号和总数量列
            material_id_col = None
            drawing_num_col = None
            total_qty_col = None
            
            # 遍历列名，寻找匹配的列
            for col in self.data.columns:
                col_lower = str(col).lower()
                if not material_id_col and any(keyword in col_lower for keyword in ['物料id', '物料编号', 'material id']):
                    material_id_col = col
                elif not drawing_num_col and any(keyword in col_lower for keyword in ['图号', '图纸编号', 'drawing']):
                    drawing_num_col = col
                elif not total_qty_col and any(keyword in col_lower for keyword in ['总数量', '总量', 'total']):
                    total_qty_col = col
            
            logger.info(f"识别到的列: 物料ID列='{material_id_col}', 图号列='{drawing_num_col}', 总数量列='{total_qty_col}'")
            
            # 如果没有识别到总数量列，尝试使用数量列
            if not total_qty_col:
                for col in self.data.columns:
                    col_lower = str(col).lower()
                    if any(keyword in col_lower for keyword in ['数量', 'qty']):
                        total_qty_col = col
                        logger.info(f"使用数量列作为总数量列: {total_qty_col}")
                        break
            
            if not total_qty_col:
                logger.error("未找到总数量列或数量列")
                return {}
            
            # 构建映射
            for index, row in self.data.iterrows():
                # 将行数据转换为字典
                row_dict = row.to_dict()
                
                # 尝试使用物料ID
                if material_id_col and pd.notna(row[material_id_col]):
                    try:
                        # 转换为整数再转字符串，去除小数点
                        material_id = str(int(row[material_id_col])).strip()
                    except (ValueError, TypeError):
                        # 如果转换失败，直接使用原始字符串
                        material_id = str(row[material_id_col]).strip()
                    
                    if material_id:
                        self.row_data_mapping[material_id] = row_dict
                        try:
                            total_qty = int(row[total_qty_col])
                            if material_id in mapping:
                                # 处理重复的物料ID，进行叠加
                                current_total, quantities = mapping[material_id]
                                new_total = current_total + total_qty
                                new_quantities = quantities + [total_qty]
                                mapping[material_id] = (new_total, new_quantities)
                                logger.info(f"物料ID {material_id} 重复，已叠加数量: {new_total}, 数量列表: {new_quantities}")
                            else:
                                mapping[material_id] = (total_qty, [total_qty])
                                logger.info(f"添加物料ID映射: {material_id} -> {total_qty}")
                        except (ValueError, TypeError):
                            logger.warning(f"总数量列值无效: {row[total_qty_col]}")
                
                # 尝试使用图号
                if drawing_num_col and pd.notna(row[drawing_num_col]):
                    drawing_num = str(row[drawing_num_col]).strip()
                    if drawing_num:
                        self.row_data_mapping[drawing_num] = row_dict
                        try:
                            total_qty = int(row[total_qty_col])
                            if drawing_num in mapping:
                                # 处理重复的图号，进行叠加
                                current_total, quantities = mapping[drawing_num]
                                new_total = current_total + total_qty
                                new_quantities = quantities + [total_qty]
                                mapping[drawing_num] = (new_total, new_quantities)
                                logger.info(f"图号 {drawing_num} 重复，已叠加数量: {new_total}, 数量列表: {new_quantities}")
                            else:
                                mapping[drawing_num] = (total_qty, [total_qty])
                                logger.info(f"添加图号映射: {drawing_num} -> {total_qty}")
                        except (ValueError, TypeError):
                            logger.warning(f"总数量列值无效: {row[total_qty_col]}")
            
            # 记录重复的物料ID或图号
            duplicates_count = 0
            for key, (total, quantities) in mapping.items():
                if len(quantities) > 1:
                    duplicates_count += 1
                    logger.info(f"{key}: 重复 {len(quantities)} 次，数量列表: {quantities}, 总数量: {total}")
            
            if duplicates_count > 0:
                logger.info(f"发现 {duplicates_count} 个重复的物料ID或图号")
            
            self.material_mapping = mapping
            logger.info(f"成功构建物料映射，包含 {len(mapping)} 个条目")
            return mapping
        except Exception as e:
            logger.error(f"构建物料映射时出错: {e}")
            return {}
    
    def get_total_quantity(self, identifier: str) -> Optional[tuple]:
        """
        根据物料ID或图号获取总数量和数量列表
        
        参数:
        identifier: 物料ID或图号
        
        返回:
        Optional[tuple]: (总数量, 数量列表)，如果未找到则返回None
        """
        if not self.material_mapping:
            self.build_material_mapping()
        
        # 直接查找
        if identifier in self.material_mapping:
            return self.material_mapping[identifier]
        
        # 部分匹配查找
        for key in self.material_mapping:
            if identifier in key or key in identifier:
                return self.material_mapping[key]
        
        return None
    
    def get_row_data(self, identifier: str) -> Optional[Dict]:
        """
        根据物料ID或图号获取完整行数据
        
        参数:
        identifier: 物料ID或图号
        
        返回:
        Optional[Dict]: 行数据字典，如果未找到则返回None
        """
        if not self.material_mapping:
            self.build_material_mapping()
        
        # 直接查找
        if identifier in self.row_data_mapping:
            return self.row_data_mapping[identifier]
        
        # 部分匹配查找
        for key in self.row_data_mapping:
            if identifier in key or key in identifier:
                return self.row_data_mapping[key]
        
        return None

    def find_identifier_in_texts(self, text_objects: list) -> Optional[str]:
        """
        在文本对象列表中查找物料ID或图号
        
        参数:
        text_objects: CAD文本对象列表
        
        返回:
        Optional[str]: 找到的标识符，如果未找到则返回None
        """
        if not self.material_mapping:
            self.build_material_mapping()
            
        if not self.material_mapping:
            return None
            
        # 收集所有文本内容
        all_texts = []
        for text_obj in text_objects:
            content = text_obj.get('content', '').strip()
            if content:
                all_texts.append(content)
        
        # 尝试在文本中找到物料ID或图号
        
        # 1. 优先检查精确匹配
        for text in all_texts:
            if text in self.material_mapping:
                logger.info(f"在文本中找到精确匹配的物料标识符: {text}")
                return text

        # 2. 检查 Excel ID 是否包含在 CAD 文本中 (例如 CAD文本="Item: 12345")
        for text in all_texts:
            for key in self.material_mapping.keys():
                if key in text:
                    logger.info(f"在CAD文本 '{text}' 中找到物料标识符 '{key}'")
                    return key

        # 3. 检查 CAD 文本是否包含在 Excel ID 中 (例如 CAD文本="12345" 是 "ID_12345" 的一部分)
        # 注意：为了避免误匹配短文本(如"3", "1"), 必须限制文本长度
        for text in all_texts:
            if len(text) < 6: # 忽略长度小于6的文本
                continue
            for key in self.material_mapping.keys():
                if text in key:
                    logger.info(f"CAD文本 '{text}' 是物料标识符 '{key}' 的一部分")
                    return key
        
        return None

    def update_cad_texts_based_on_excel(self, text_objects: list, doc) -> Tuple[bool, int]:
        """
        根据Excel文件更新CAD文本对象
        
        参数:
        text_objects: CAD文本对象列表
        doc: DXF文档对象
        
        返回:
        Tuple[bool, int]: (是否成功, 更新的文本数量)
        """
        if not self.material_mapping:
            self.build_material_mapping()
        
        if not self.material_mapping:
            logger.error("物料映射为空，无法更新CAD文本")
            return False, 0
        
        try:
            updated_count = 0
            
            # 首先收集所有文本内容，用于识别物料ID或图号
            all_texts = []
            for text_obj in text_objects:
                content = text_obj.get('content', '').strip()
                if content:
                    all_texts.append(content)
            
            logger.info(f"收集到 {len(all_texts)} 个文本对象")
            logger.info(f"文本内容: {all_texts}")
            
            # 尝试在文本中找到物料ID或图号
            found_identifiers = []
            
            # 1. 优先检查精确匹配
            for text in all_texts:
                if text in self.material_mapping:
                    found_identifiers.append(text)
                    logger.info(f"在文本中找到精确匹配的物料标识符: {text}")
                    break
            
            # 2. 检查 Excel ID 是否包含在 CAD 文本中
            if not found_identifiers:
                for text in all_texts:
                    for key in self.material_mapping.keys():
                        if key in text:
                            found_identifiers.append(key)
                            logger.info(f"在CAD文本 '{text}' 中找到物料标识符 '{key}'")
                            break
                    if found_identifiers: break
            
            # 3. 检查 CAD 文本是否包含在 Excel ID 中 (限制长度)
            if not found_identifiers:
                for text in all_texts:
                    if len(text) < 6: continue
                    for key in self.material_mapping.keys():
                        if text in key:
                            found_identifiers.append(key)
                            logger.info(f"CAD文本 '{text}' 是物料标识符 '{key}' 的一部分")
                            break
                    if found_identifiers: break
            
            if not found_identifiers:
                logger.warning("未在CAD文本中找到任何物料ID或图号")
                return True, 0
            
            # 使用第一个找到的标识符
            identifier = found_identifiers[0]
            qty_info = self.material_mapping.get(identifier)
            
            if qty_info is None:
                logger.warning(f"未找到标识符 {identifier} 对应的总数量")
                return True, 0
            
            total_qty, quantities = qty_info
            
            # 确定显示格式：有重复时显示叠加格式，无重复时显示普通格式
            display_qty = total_qty
            if len(quantities) > 1:
                # 有重复，显示叠加格式，如8+8
                display_qty = '+'.join(map(str, quantities))
                logger.info(f"使用标识符 {identifier}，有重复数量，叠加格式为 {display_qty}，总数量为 {total_qty}")
            else:
                logger.info(f"使用标识符 {identifier}，对应的总数量为 {total_qty}")
            
            # 更新文本对象中的数字
            for text_obj in text_objects:
                entity = text_obj.get('entity')
                content = text_obj.get('content', '').strip()
                
                if entity:
                    # 替换多种格式的数字
                    import re
                    
                    # 处理"共"和"件"之间的文本，替换为Excel中的数量
                    if '共' in content:
                        # 替换"共"后的内容为Excel中的数量（有重复时显示叠加格式）
                        new_content = re.sub(r'共\s*[\d\s+]+(\s*件)?', f'共{display_qty}件' if '件' in content else f'共{display_qty}', content)
                    # 2. 替换纯数字文本（始终显示总数量）
                    elif content.isdigit():
                        new_content = str(total_qty)
                    # 3. 替换包含数字的文本（保留其他内容，始终显示总数量）
                    else:
                        new_content = re.sub(r'\d+', str(total_qty), content)
                    
                    if new_content != content:
                        # 更新文本内容
                        try:
                            if hasattr(entity.dxf, 'text'):
                                entity.dxf.text = new_content
                                logger.info(f"更新文本: {content} -> {new_content}")
                                updated_count += 1
                        except Exception as e:
                            logger.error(f"更新文本时出错: {e}")
            
            logger.info(f"成功更新 {updated_count} 个文本对象")
            return True, updated_count
        except Exception as e:
            logger.error(f"更新CAD文本时出错: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False, 0
