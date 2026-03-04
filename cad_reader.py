import ezdxf
import os
import re
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CADReader:
    """
    CAD文件读取器，负责读取CAD文件并识别其中的图形和文本对象
    """
    
    def __init__(self, file_path):
        self.file_path = file_path
        self.doc = None
        self.modelspace = None
        
    def load_file(self):
        """
        加载CAD文件
        
        返回:
        bool: 文件加载是否成功
        """
        if not os.path.exists(self.file_path):
            logger.error(f"文件不存在: {self.file_path}")
            return False
        
        try:
            self.doc = ezdxf.readfile(self.file_path)
            self.modelspace = self.doc.modelspace()
            logger.info(f"成功加载CAD文件: {self.file_path}")
            return True
        except ezdxf.DXFError as e:
            logger.error(f"读取DXF文件时出错: {e}")
            return False
        except Exception as e:
            logger.error(f"加载文件时出错: {e}")
            return False
    
    def get_text_objects(self):
        """
        获取文件中的所有文本对象
        
        返回:
        list: 文本对象列表，每个元素是包含实体、内容和位置的字典
        """
        if not self.modelspace:
            logger.warning("模型空间未初始化，请先调用load_file方法")
            return []
        
        texts = []
        
        # 递归从块引用中提取文本
        def extract_texts_from_entity(entity, is_nested=False):
            entity_type = entity.dxftype()
            
            if entity_type == 'TEXT':
                text_content = entity.dxf.text
                # 将类似 "\U+4ef6"、"\U4ef6"、"\u+4ef6"、"\u4ef6" 这样的码点序列转换为对应的 Unicode 字符
                try:
                    # 处理 Unicode 转义序列
                    def _decode_unicode(m):
                        full_match = m.group(0)
                        hexstr = ''
                        
                        # 提取十六进制部分
                        if '+' in full_match:
                            hexstr = full_match.split('+')[1]
                        else:
                            # 对于 \UXXXX 或 \uXXXX 格式
                            if full_match.startswith('\\U'):
                                hexstr = full_match[2:]
                            elif full_match.startswith('\\u'):
                                hexstr = full_match[2:]
                        
                        try:
                            # 尝试将任意长度的十六进制数转换为 Unicode 字符
                            cp = int(hexstr, 16)
                            return chr(cp)
                        except Exception:
                            return full_match
                    
                    # 使用更简单和更灵活的正则表达式来匹配各种 Unicode 转义序列
                    # 匹配 \U+XXXX、\U+XXXXX、\U+XXXXXX、\UXXXX、\UXXXXX、\UXXXXXX、\u+XXXX、\uXXXX 等格式
                    text_content = re.sub(r'(\\U\+|\\U|\\u\+|\\u)([0-9A-Fa-f]+)', _decode_unicode, text_content)
                    
                    # 清理可能存在的多余空格
                    text_content = ' '.join(text_content.split())
                except Exception as e:
                    logger.warning(f"解析 TEXT 中的 Unicode 转义序列时出错: {e}")
                logger.info(f"找到TEXT实体，内容: {repr(text_content)}")
                texts.append({
                    'entity': entity,
                    'content': text_content,
                    'position': (entity.dxf.insert[0], entity.dxf.insert[1]),
                    'type': 'TEXT',
                    'is_nested': is_nested
                })
            elif entity_type == 'MTEXT':
                # 多行文本：优先使用 ezdxf 的 plain_text()（若可用）以获取已处理过的纯文本内容；
                # 否则回退到 entity.text 或 entity.dxf.text。不要使用错误的 latin1->unicode_escape 解码，
                # 该方法会破坏中文字符。
                raw_text = getattr(entity, 'text', '')
                dxf_text = getattr(entity.dxf, 'text', '')
                logger.info(f"找到MTEXT实体，raw_text: {repr(raw_text)}, dxf_text: {repr(dxf_text)}")

                try:
                    # 处理 Unicode 转义序列 - 使用更直接的逐字符解析方法
                    def decode_unicode_escape(text):
                        result = []
                        i = 0
                        while i < len(text):
                            if text[i] == '\\' and i + 1 < len(text):
                                # 找到转义字符
                                if text[i+1] in ['U', 'u']:
                                    # 处理 Unicode 转义序列
                                    prefix = text[i+1]
                                    i += 2  # 跳过 \U 或 \u
                                    hex_part = []
                                    
                                    # 跳过可能存在的 + 号
                                    if i < len(text) and text[i] == '+':
                                        i += 1
                                    
                                    # 收集十六进制数字
                                    while i < len(text) and text[i] in '0123456789ABCDEFabcdef':
                                        hex_part.append(text[i])
                                        i += 1
                                    
                                    # 尝试转换为 Unicode 字符
                                    if hex_part:
                                        hex_str = ''.join(hex_part)
                                        try:
                                            # 处理标准的4位和8位Unicode编码
                                            if len(hex_str) == 4 or len(hex_str) == 8:
                                                cp = int(hex_str, 16)
                                                result.append(chr(cp))
                                            # 处理5位的特殊情况，如\U+51714（应该是\U+5171）
                                            elif len(hex_str) == 5:
                                                # 尝试取前4位
                                                cp = int(hex_str[:4], 16)
                                                result.append(chr(cp))
                                                # 将剩余的1位作为普通字符添加
                                                result.append(hex_str[4])
                                            # 处理其他长度
                                            else:
                                                cp = int(hex_str, 16)
                                                result.append(chr(cp))
                                        except Exception:
                                            # 如果转换失败，将原始转义序列添加到结果中
                                            result.append('\\' + prefix + '+' + hex_str)
                                    else:
                                        # 如果没有收集到十六进制数字，将原始字符添加到结果中
                                        result.append('\\' + prefix)
                                else:
                                    # 处理其他转义序列
                                    result.append(text[i])
                                    i += 1
                            else:
                                # 普通字符
                                result.append(text[i])
                                i += 1
                        
                        return ''.join(result)
                    
                    # 解码 Unicode 转义序列
                    decoded_text = decode_unicode_escape(raw_text)
                    
                    # 提取 DXF 格式标记中的文本内容，同时保留格式标记前后的文本
                    def extract_text_from_dxf_format(text):
                        # 匹配 DXF 格式标记，如 {\fSimSun|b0|i0|c134|p2;\U+5f2f\U+677f}
                        pattern = re.compile(r'\{\\f[^}]*;([^}]*)\}')
                        
                        # 提取所有格式标记中的文本
                        extracted_parts = []
                        last_end = 0
                        
                        for match in pattern.finditer(text):
                            # 保留格式标记前面的文本
                            if match.start() > last_end:
                                extracted_parts.append(text[last_end:match.start()])
                            # 提取格式标记中的文本
                            extracted_parts.append(match.group(1))
                            last_end = match.end()
                        
                        # 保留最后一个格式标记后面的文本
                        if last_end < len(text):
                            extracted_parts.append(text[last_end:])
                        
                        return ''.join(extracted_parts)
                    
                    # 提取 DXF 格式标记中的文本
                    text_content = extract_text_from_dxf_format(decoded_text)
                    
                    # 清理可能存在的多余空格
                    text_content = ' '.join(text_content.split())
                except Exception as e:
                    logger.warning(f"解析 MTEXT 中的 Unicode 转义序列时出错: {e}")
                    text_content = raw_text if raw_text else dxf_text
                texts.append({
                    'entity': entity,
                    'content': text_content,
                    'position': (entity.dxf.insert[0], entity.dxf.insert[1]) if hasattr(entity.dxf, 'insert') else (0, 0),
                    'type': 'MTEXT',
                    'is_nested': is_nested
                })
            elif entity_type == 'ATTRIB':
                # 处理属性实体，这在块定义中很常见
                try:
                    text_content = entity.dxf.text
                    logger.info(f"找到ATTRIB实体，内容: {repr(text_content)}")
                    
                    # 清理文本内容
                    if text_content:
                        # 清理可能存在的多余空格
                        text_content = ' '.join(text_content.split())
                        texts.append({
                            'entity': entity,
                            'content': text_content,
                            'position': (entity.dxf.insert[0], entity.dxf.insert[1]) if hasattr(entity.dxf, 'insert') else (0, 0),
                            'type': 'ATTRIB',
                            'is_nested': is_nested
                        })
                except Exception as e:
                    logger.warning(f"处理ATTRIB实体时出错: {e}")
            elif entity_type == 'INSERT':
                # 处理块引用，从引用的块定义中提取文本
                try:
                    block_name = entity.dxf.name
                    if block_name in self.doc.blocks:
                        block = self.doc.blocks[block_name]
                        logger.info(f"找到块引用: {block_name}，从块定义中提取文本")
                        # 遍历块定义中的所有实体
                        for block_entity in block:
                            extract_texts_from_entity(block_entity, is_nested=True)
                except Exception as e:
                    logger.warning(f"处理块引用时出错: {e}")
        
        # 遍历模型空间中的所有实体
        for entity in self.modelspace:
            extract_texts_from_entity(entity, is_nested=False)
        
        logger.info(f"找到 {len(texts)} 个文本对象")
        return texts
    
    def get_geometric_entities(self, exclude_types=None, explode_blocks=True):
        """
        获取文件中的所有几何图形实体
        
        参数:
        exclude_types: 要排除的实体类型列表，默认为['TEXT', 'MTEXT']，不再排除INSERT类型
        explode_blocks: 是否递归分解块引用，默认为True
        
        返回:
        list: 几何实体列表
        """
        if not self.modelspace:
            logger.warning("模型空间未初始化，请先调用load_file方法")
            return []
        
        if exclude_types is None:
            # 修改：不再排除INSERT类型，这样就能处理块引用
            exclude_types = ['TEXT', 'MTEXT']
        
        geometric_entities = []
        entity_counts = {}
        
        # 递归从块引用中提取几何实体
        def extract_geometric_entities(entity):
            entity_type = entity.dxftype()
            
            # 更新实体计数
            if entity_type in entity_counts:
                entity_counts[entity_type] += 1
            else:
                entity_counts[entity_type] = 1
            
            # 如果是块引用，且需要分解
            if entity_type == 'INSERT' and explode_blocks:
                try:
                    block_name = entity.dxf.name
                    if block_name in self.doc.blocks:
                        block = self.doc.blocks[block_name]
                        logger.info(f"找到块引用: {block_name}，从块定义中提取几何实体")
                        # 遍历块定义中的所有实体
                        for block_entity in block:
                            extract_geometric_entities(block_entity)
                except Exception as e:
                    logger.warning(f"处理块引用时出错: {e}")
            # 如果不是排除的类型，则认为是几何实体
            # 注意：如果entity_type是INSERT但explode_blocks为False，它会进入这里（只要INSERT不在exclude_types中）
            elif entity_type not in exclude_types:
                geometric_entities.append(entity)
        
        # 遍历模型空间中的所有实体
        for entity in self.modelspace:
            extract_geometric_entities(entity)
        
        # 记录找到的实体类型和数量
        logger.info(f"实体类型统计: {entity_counts}")
        logger.info(f"找到 {len(geometric_entities)} 个几何实体")
        
        return geometric_entities
    
    def analyze_file(self):
        """
        分析文件内容，返回文本和几何实体的统计信息
        
        返回:
        dict: 包含文件分析结果的字典
        """
        if not self.load_file():
            return None
        
        texts = self.get_text_objects()
        geometric_entities = self.get_geometric_entities()
        
        # 提取文本内容列表
        text_contents = [text['content'] for text in texts]
        
        analysis_result = {
            'file_path': self.file_path,
            'text_count': len(texts),
            'text_contents': text_contents,
            'geometric_entity_count': len(geometric_entities)
        }
        
        logger.info(f"文件分析完成: {analysis_result}")
        return analysis_result

# 示例用法
if __name__ == "__main__":
    # 这个模块通常不会直接运行，而是被导入使用
    print("这是CADReader模块，提供CAD文件读取和对象识别功能")
