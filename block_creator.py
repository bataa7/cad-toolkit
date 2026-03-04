import os
import logging
from typing import List, Dict, Any, Optional, Tuple, TYPE_CHECKING

# 仅在类型检查时导入ezdxf，运行时延迟导入
if TYPE_CHECKING:
    import ezdxf

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BlockCreator:
    """
    块创建器，负责将CAD文件中的图形对象组合成块并使用文本内容命名
    """
    
    def __init__(self):
        # 延迟导入CADReader和TextProcessor
        from cad_reader import CADReader
        from text_processor import TextProcessor
        self.cad_reader = CADReader("")
        self.text_processor = TextProcessor()
        # 延迟导入ExcelReader
        from excel_reader import ExcelReader
        self.excel_reader = ExcelReader()
    
    def _calculate_insertion_point(self, entities: List["Any"]) -> Tuple[float, float, float]:
        """
        计算块的插入点
        
        参数:
        entities: 实体列表
        
        返回:
        tuple: 插入点坐标 (x, y, z)
        """
        if not entities:
            return (0.0, 0.0, 0.0)
        
        # 尝试找到一个有insert属性的实体作为插入点
        for entity in entities:
            if hasattr(entity.dxf, 'insert'):
                return tuple(entity.dxf.insert)
        
        # 如果没有找到有insert属性的实体，计算所有实体的边界框中心点
        try:
            # 收集所有实体的边界框
            min_x, min_y, max_x, max_y = float('inf'), float('inf'), float('-inf'), float('-inf')
            
            for entity in entities:
                if hasattr(entity, 'bounding_box'):
                    bbox = entity.bounding_box()
                    if bbox:
                        min_x = min(min_x, bbox[0][0])
                        min_y = min(min_y, bbox[0][1])
                        max_x = max(max_x, bbox[1][0])
                        max_y = max(max_y, bbox[1][1])
            
            # 如果找到了有效边界，计算中心点
            if min_x != float('inf') and min_y != float('inf'):
                center_x = (min_x + max_x) / 2
                center_y = (min_y + max_y) / 2
                return (center_x, center_y, 0.0)
        except Exception as e:
            logger.warning(f"计算边界框时出错: {e}")
        
        # 默认返回原点
        return (0.0, 0.0, 0.0)
    
    def create_block_from_entities(self, doc: "ezdxf.document.Drawing", 
                                  entities: List["Any"], block_name: str,
                                  insertion_point: Optional[Tuple[float, float, float]] = None) -> Optional[str]:
        """
        从实体列表创建单个块
        
        参数:
        doc: DXF文档对象
        entities: 要添加到块中的实体列表
        block_name: 块名称
        insertion_point: 块插入点，如果为None则自动计算
        
        返回:
        str: 成功创建的块名称，如果失败则返回None
        """
        if not entities or not block_name:
            logger.warning("无效的实体列表或块名")
            return None
        
        try:
            # 如果块名已存在，直接返回已有块名，不再新建新块
            if block_name in doc.blocks:
                logger.info(f"块名已存在，直接使用已有块: {block_name}")
                return block_name
            # 创建新块
            block = doc.blocks.new(name=block_name)
            logger.info(f"创建单个块: {block_name}")
            # 将所有实体复制到一个块中
            copied_count = 0
            skipped_count = 0
            entity_types_copied = {}
            
            for entity in entities:
                try:
                    entity_type = entity.dxftype()
                    
                    # 对于不同类型的实体，使用不同的复制方法
                    if entity_type == 'LINE':
                        # 对于线条，确保复制所有属性
                        start = entity.dxf.start
                        end = entity.dxf.end
                        layer = entity.dxf.layer
                        color = entity.dxf.color
                        
                        # 创建新的线条实体
                        line = block.add_line(start, end)
                        line.dxf.layer = layer
                        line.dxf.color = color
                        copied_count += 1
                    else:
                        # 对于其他类型的实体，使用copy方法
                        block_entity = entity.copy()
                        block.add_entity(block_entity)
                        copied_count += 1
                    
                    # 更新复制的实体类型统计
                    if entity_type in entity_types_copied:
                        entity_types_copied[entity_type] += 1
                    else:
                        entity_types_copied[entity_type] = 1
                except Exception as e:
                    skipped_count += 1
                    logger.warning(f"复制实体时出错 ({entity.dxftype()}): {e}")
            
            logger.info(f"成功将 {copied_count} 个实体添加到块 '{block_name}'")
            logger.info(f"跳过了 {skipped_count} 个实体")
            logger.info(f"复制的实体类型统计: {entity_types_copied}")
            return block_name
        except Exception as e:
            logger.error(f"创建块时出错: {e}")
            return None
    
    def replace_entities_with_block(self, doc: "ezdxf.document.Drawing", 
                                   modelspace: "ezdxf.layouts.Modelspace", 
                                   entities: List["Any"], block_name: str,
                                   insertion_point: Optional[Tuple[float, float, float]] = None,
                                   write_material_thickness_attrib: bool = False,
                                   write_id_drawing_name_attrib: bool = False,
                                   attributes_data: Optional[Dict] = None) -> bool:
        """
        将所有实体替换为一个块引用
        
        参数:
        doc: DXF文档对象
        modelspace: 模型空间
        entities: 要替换的实体列表
        block_name: 块名称
        insertion_point: 块插入点，如果为None则自动计算
        write_material_thickness_attrib: 是否写入材质/厚度属性
        write_id_drawing_name_attrib: 是否写入物料ID/图号/名称属性
        attributes_data: 属性数据字典（通常来自Excel）
        
        返回:
        bool: 操作是否成功
        """
        try:
            # 计算插入点
            if insertion_point is None:
                insertion_point = self._calculate_insertion_point(entities)
            
            # 创建单个块
            created_block_name = self.create_block_from_entities(doc, entities, block_name, insertion_point)
            if not created_block_name:
                return False
            
            # 删除原始实体（只删除模型空间中实际存在的实体）
            deleted_count = 0
            
            # 删除原始实体（使用更可靠的方式）
            deleted_count = 0
            
            # 遍历模型空间中的所有实体，删除匹配的实体
            entities_in_modelspace = list(modelspace)
            for entity_in_space in entities_in_modelspace:
                # 检查当前实体是否在要删除的列表中
                for entity_to_delete in entities:
                    # 比较实体的句柄或其他唯一标识符
                    try:
                        if hasattr(entity_in_space, 'dxf') and hasattr(entity_to_delete, 'dxf'):
                            if entity_in_space.dxf.handle == entity_to_delete.dxf.handle:
                                modelspace.delete_entity(entity_in_space)
                                deleted_count += 1
                                logger.info(f"删除实体: 类型={entity_in_space.dxftype()}, 句柄={entity_in_space.dxf.handle}")
                                break
                    except Exception as e:
                        logger.debug(f"比较实体时出错: {e}")
            
            logger.info(f"成功删除 {deleted_count} 个实体")
            
            # 在模型空间中插入单个块引用
            blockref = modelspace.add_blockref(created_block_name, insertion_point)
            logger.info(f"在模型空间中插入单个块引用: {created_block_name}")
            logger.info(f"块引用位置: {insertion_point}")
            
            # 准备属性值
            material_val = ""
            thickness_val = ""
            id_val = ""
            drawing_val = ""
            name_val = ""
            total_qty_val = ""
            
            # 优先使用传入的 attributes_data
            if attributes_data:
                # 尝试从字典中获取值，支持多种列名
                
                # 辅助函数：查找值
                def find_val(keys):
                    for k in keys:
                        # 遍历字典的所有键，进行不区分大小写的匹配 (同时去除首尾空格)
                        for data_key, data_val in attributes_data.items():
                            clean_data_key = str(data_key).strip()
                            if clean_data_key == k:
                                val = str(data_val).strip()
                                if val.lower() == 'nan': return "" # 处理 nan
                                return val
                            if k in clean_data_key and ("ID" in k or "图号" in k): # 宽松匹配ID
                                val = str(data_val).strip()
                                if val.lower() == 'nan': return "" # 处理 nan
                                return val
                    return ""

                # 材质
                for key in attributes_data:
                    clean_key = str(key).strip()
                    if '材质' in clean_key or 'Material' in clean_key:
                         val = str(attributes_data[key]).strip()
                         if val.lower() == 'nan': val = "" # 处理 nan
                         if val and val != "组件": # 过滤组件
                             material_val = val
                             break
                
                # 厚度
                for key in attributes_data:
                    clean_key = str(key).strip()
                    if '板厚' in clean_key or '厚度' in clean_key or 'Thickness' in clean_key:
                        val = str(attributes_data[key]).strip()
                        if val.lower() == 'nan': val = "" # 处理 nan
                        if val and val != "组件":
                            if val.endswith('.0'): val = val[:-2]
                            thickness_val = val
                            break
                
                # 物料ID
                for key in attributes_data:
                    clean_key = str(key).strip()
                    if '物料ID' in clean_key or '物料编号' in clean_key:
                        id_val = str(attributes_data[key]).strip()
                        if id_val.lower() == 'nan': id_val = "" # 处理 nan
                        if id_val.endswith('.0'): id_val = id_val[:-2]
                        break
                        
                # 图号
                for key in attributes_data:
                    clean_key = str(key).strip()
                    if '图号' in clean_key or 'Drawing' in clean_key:
                        drawing_val = str(attributes_data[key]).strip()
                        if drawing_val.lower() == 'nan': drawing_val = "" # 处理 nan
                        break
                
                # 名称
                for key in attributes_data:
                    clean_key = str(key).strip()
                    if '名称' in clean_key or 'Name' in clean_key:
                        name_val = str(attributes_data[key]).strip()
                        if name_val.lower() == 'nan': name_val = "" # 处理 nan
                        break

                # 总数量
                for key in attributes_data:
                    clean_key = str(key).strip()
                    if '总数量' in clean_key or 'Total' in clean_key:
                        total_qty_val = str(attributes_data[key]).strip()
                        if total_qty_val.lower() == 'nan': total_qty_val = "" # 处理 nan
                        break
                if not total_qty_val: # 尝试找数量列
                     for key in attributes_data:
                        clean_key = str(key).strip()
                        if clean_key == '数量' or clean_key == 'Qty':
                            total_qty_val = str(attributes_data[key]).strip()
                            if total_qty_val.lower() == 'nan': total_qty_val = "" # 处理 nan
                            break
            
            # 如果没有从Excel获取到值，尝试从文本实体中解析 (后备方案)
            if not any([material_val, thickness_val, id_val, drawing_val, name_val]):
                import re
                
                # 从实体中提取所有文本
                all_texts = []
                for ent in entities:
                    if ent.dxftype() in ('TEXT', 'MTEXT', 'ATTRIB'):
                        try:
                            all_texts.append(ent.dxf.text)
                        except:
                            pass
                
                for text in all_texts:
                    # 材质
                    if not material_val and ("材质" in text or "Material" in text):
                        material_val = text
                    # 厚度
                    if not thickness_val and ("厚度" in text or "Thickness" in text or text.startswith("T") and text[1:].isdigit()):
                        thickness_val = text
                    # 图号/ID (简单假设数字较长的)
                    if len(re.findall(r'\d', text)) > 6:
                        if not id_val: id_val = text
                        elif not drawing_val: drawing_val = text

            # 添加属性
            if write_material_thickness_attrib:
                blockref.add_attrib(tag='材质', text=material_val, insert=insertion_point, dxfattribs={'height': 10, 'style': 'Standard'})
                blockref.add_attrib(tag='厚度', text=thickness_val, insert=(insertion_point[0], insertion_point[1]-20), dxfattribs={'height': 10, 'style': 'Standard'})
            
            if write_id_drawing_name_attrib:
                blockref.add_attrib(tag='物料ID', text=id_val, insert=(insertion_point[0], insertion_point[1]-40), dxfattribs={'height': 10, 'style': 'Standard'})
                blockref.add_attrib(tag='图号', text=drawing_val, insert=(insertion_point[0], insertion_point[1]-60), dxfattribs={'height': 10, 'style': 'Standard'})
                blockref.add_attrib(tag='名称', text=name_val, insert=(insertion_point[0], insertion_point[1]-80), dxfattribs={'height': 10, 'style': 'Standard'})
                blockref.add_attrib(tag='总数量', text=total_qty_val, insert=(insertion_point[0], insertion_point[1]-100), dxfattribs={'height': 10, 'style': 'Standard'})

            return True
            
        except Exception as e:
            logger.error(f"替换实体为块时出错: {e}")
            return False
    
    def process_cad_file(self, input_file: str, output_file: Optional[str] = None, 
                        text_strategy: str = 'first_valid', 
                        clear_existing_blocks: bool = False, 
                        output_dir: Optional[str] = None, 
                        excel_file: Optional[str] = None,
                        write_material_thickness_attrib: bool = False,
                        write_id_drawing_name_attrib: bool = False,
                        row_data: Optional[Dict] = None) -> Optional[str]:
        """
        处理CAD文件，将所有图形对象组合成单个块并用文本内容命名
        
        参数:
        input_file: 输入文件路径
        output_file: 输出文件路径，如果为None则自动生成
        text_strategy: 文本选择策略
        clear_existing_blocks: 是否清理现有的块定义
        output_dir: 输出目录
        excel_file: Excel文件路径，用于参照物料ID或图号更新CAD文本
        write_material_thickness_attrib: 是否写入材质/厚度属性
        write_id_drawing_name_attrib: 是否写入物料ID/图号/名称属性
        row_data: 对应Excel行数据
        
        返回:
        str: 输出文件路径，如果处理失败则返回None
        """
        # 设置CAD读取器的文件路径
        self.cad_reader.file_path = input_file
        
        # 加载文件
        if not self.cad_reader.load_file():
            return None
        
        # 可选：清理现有的块定义（保留标准块）
        if clear_existing_blocks:
            self._clear_existing_blocks(self.cad_reader.doc)
        
        # 获取文本对象
        text_objects = self.cad_reader.get_text_objects()
        
        # 如果提供了Excel文件，根据Excel文件更新CAD文本
        if excel_file and os.path.exists(excel_file):
            logger.info(f"使用Excel文件更新CAD文本: {excel_file}")
            self.excel_reader.file_path = excel_file
            if self.excel_reader.load_file():
                success, updated_count = self.excel_reader.update_cad_texts_based_on_excel(text_objects, self.cad_reader.doc)
                if success:
                    logger.info(f"成功更新 {updated_count} 个CAD文本对象")
                    # 重新获取文本对象，确保使用更新后的文本内容
                    text_objects = self.cad_reader.get_text_objects()
                    logger.info("已重新获取更新后的文本对象")
                else:
                    logger.warning("更新CAD文本失败")
            else:
                logger.warning(f"无法加载Excel文件: {excel_file}")
        
        # 生成块名，如果没有文本对象则使用默认名称
        if not text_objects:
            logger.warning("未找到文本对象，将使用默认名称")
            block_name = "DEFAULT_BLOCK"
        else:
            # 使用文本对象生成块名
            block_name = self.text_processor.generate_block_name_from_texts(text_objects, text_strategy)
            if not block_name:
                logger.warning("无法生成有效的块名，将使用默认名称")
                block_name = "DEFAULT_BLOCK"

        # 获取所有几何实体 (不分解块，保留原始块引用结构，防止出现重复实体)
        geometric_entities = self.cad_reader.get_geometric_entities(explode_blocks=False)
        logger.info(f"获取到 {len(geometric_entities)} 个几何实体")
        
        # 将文本对象中的实体也添加到要包含在块中的实体列表
        if text_objects:
            # 只添加字典中的entity对象，而不是整个字典
            added_text_count = 0
            for text_obj in text_objects:
                # 仅添加非嵌套的文本对象（嵌套文本在块引用中已包含）
                if not text_obj.get('is_nested', False):
                    geometric_entities.append(text_obj['entity'])
                    added_text_count += 1
            logger.info(f"已将 {added_text_count} 个非嵌套文本对象添加到实体列表中")
            logger.info(f"添加文本对象后，实体列表总长度: {len(geometric_entities)}")
        
        if not geometric_entities:
            logger.warning("未找到几何实体，无法创建块")
            return None

        logger.info(f"将使用所有几何实体创建单个块: {block_name}")

        # 替换所有实体为单个块
        success = self.replace_entities_with_block(
            self.cad_reader.doc,
            self.cad_reader.modelspace,
            geometric_entities,
            block_name,
            write_material_thickness_attrib=write_material_thickness_attrib,
            write_id_drawing_name_attrib=write_id_drawing_name_attrib,
            attributes_data=row_data
        )
        if not success:
            logger.error("替换实体为块失败")
            return None
        
        # 确定输出文件名
        if output_file is None:
            # 使用指定的输出目录，如果没有则使用输入文件的目录
            directory = output_dir if output_dir else os.path.dirname(input_file)
            ext = os.path.splitext(input_file)[1]
            
            # 生成安全的文件名（限制长度并移除不允许的字符）
            safe_block_name = block_name[:50]  # 限制长度
            # 移除不允许的文件名字符
            import re
            safe_block_name = re.sub(r'[<>"/\\|?*]', '_', safe_block_name)
            # 移除多余的空格
            safe_block_name = ' '.join(safe_block_name.split())
            
            output_file = os.path.join(directory, f"{safe_block_name}{ext}")
        
        # 保存文件
        try:
            self.cad_reader.doc.saveas(output_file)
            logger.info(f"文件已成功保存到: {output_file}")
            return output_file
        except Exception as e:
            logger.error(f"保存文件时出错: {e}")
            return None
            
    def _clear_existing_blocks(self, doc: "ezdxf.document.Drawing"):
        """
        清理文档中现有的块定义，保留标准块
        
        参数:
        doc: DXF文档对象
        """
        # 保留的标准块列表
        standard_blocks = ['*Model_Space', '*Paper_Space', '*Paper_Space0']
        
        # 需要删除的块名列表
        blocks_to_delete = []
        
        # 收集需要删除的块名
        for block in doc.blocks:
            if block.name not in standard_blocks:
                blocks_to_delete.append(block.name)
        
        # 删除收集的块
        for block_name in blocks_to_delete:
            try:
                del doc.blocks[block_name]
                logger.info(f"已删除现有块: {block_name}")
            except Exception as e:
                logger.warning(f"删除块 {block_name} 时出错: {e}")

# 示例用法
if __name__ == "__main__":
    # 这个模块通常不会直接运行，而是被导入使用
    print("这是BlockCreator模块，提供块创建和管理功能")








