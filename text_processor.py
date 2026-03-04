import re
import logging
from typing import List, Dict, Any, Optional

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TextProcessor:
    """
    文本处理器，负责从CAD文件中提取文本内容并生成合适的块名
    """
    
    def __init__(self):
        # 定义有效的块名模式（去除特殊字符和DXF格式标记）
        # 扩展正则表达式以匹配更多特殊字符和DXF格式标记
        self.invalid_chars_pattern = re.compile(r'[\\/:*?"<>|]')
        
        # 旧的模式保留，以免破坏依赖，但实际上不推荐使用
        self.dxf_format_pattern = re.compile(r'\{[^}]*;([^}]*)\}')
        self.font_format_pattern = re.compile(r'_f[a-zA-Z0-9_]*|_b[01]|_i[01]|_c\d+|_p\d+|_U_[0-9a-fA-F]+')
        self.unicode_escape_pattern = re.compile(r'\\U\+[0-9a-fA-F]{4}')
        
        # 新的正则表达式，用于 strip_dxf_tags
        self.dxf_tag_pattern = re.compile(r'\\[ACFHQTWfp][^;]*;')
        self.dxf_switch_pattern = re.compile(r'\\[LlkKoO]')

    def strip_dxf_tags(self, text: str) -> str:
        """
        移除文本中的DXF格式标记，但保留原始文本内容和空格
        
        参数:
        text: 原始文本内容
        
        返回:
        str: 去除标记后的文本
        """
        if not text:
            return ""
        
        # 1. Remove format tags ending with ;
        # \A...; \C...; \f...; \H...; \Q...; \T...; \W...; \p...;
        text = self.dxf_tag_pattern.sub('', text)
        
        # 2. Remove simple switches \L \l \O \o \k \K
        text = self.dxf_switch_pattern.sub('', text)
        
        # 3. Handle newlines
        text = text.replace(r'\P', ' ')
        
        # 4. Remove braces { and }
        text = text.replace('{', '').replace('}', '')
        
        return text

    def clean_text_for_block_name(self, text: str) -> str:
        """
        清理文本，使其适合作为块名
        
        参数:
        text: 原始文本内容
        
        返回:
        str: 清理后的文本，适合作为块名
        """
        if not text:
            return "Block"
        
        logger.info(f"原始文本: {repr(text)}")
        
        # 使用新的策略清理DXF标记
        cleaned = self.strip_dxf_tags(text)
        logger.info(f"去除DXF标记后: {repr(cleaned)}")
        
        # 后续处理：替换括号，处理无效字符
        
        # 将中文括号转换为英文括号
        processed_text = cleaned.replace('（', '(').replace('）', ')')
        
        # 去除首尾空白字符
        cleaned_text = processed_text.strip()
        
        # 替换无效字符为下划线
        cleaned_text = self.invalid_chars_pattern.sub('_', cleaned_text)
        logger.info(f"替换无效字符后: {repr(cleaned_text)}")
        
        # 只替换真正无效的字符，保留空格和合理的分隔符
        # 保留中文、英文字母、数字、下划线、英文括号、连字符和空格
        cleaned_text = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9_()\-\s]', '_', cleaned_text)
        logger.info(f"替换非允许字符后: {repr(cleaned_text)}")
        
        # 只将连续的空格替换为单个空格
        cleaned_text = re.sub(r'\s+', ' ', cleaned_text)
        logger.info(f"处理空格后: {repr(cleaned_text)}")
        
        # 将空格替换为下划线（AutoCAD块名不能包含空格）
        cleaned_text = cleaned_text.replace(' ', '_')
        logger.info(f"替换空格为下划线后: {repr(cleaned_text)}")
        
        # 替换连续的下划线为单个下划线
        cleaned_text = re.sub(r'_+', '_', cleaned_text)
        logger.info(f"处理连续下划线后: {repr(cleaned_text)}")
        
        # 如果文本过长，截断到合理长度（AutoCAD块名通常不超过255个字符）
        max_length = 255
        if len(cleaned_text) > max_length:
            cleaned_text = cleaned_text[:max_length]
        
        # 如果清理后文本为空，使用默认名称
        if not cleaned_text:
            cleaned_text = "Block"
        
        logger.info(f"最终块名: {repr(cleaned_text)}")
        return cleaned_text
    
    def select_best_text_for_block_name(self, text_objects: List[Dict[str, Any]]) -> Optional[str]:
        """
        从多个文本对象中选择最合适的一个作为块名
        
        参数:
        text_objects: 文本对象列表，每个对象包含实体、内容和位置
        
        返回:
        str: 选择的文本内容，如果没有合适的文本则返回None
        """
        if not text_objects:
            logger.warning("没有文本对象可供选择")
            return None
        
        # 1. 首先尝试找到非空且不只是空白字符的文本
        valid_texts = [
            text for text in text_objects 
            if text.get('content') and text.get('content').strip()
        ]
        
        if not valid_texts:
            logger.warning("所有文本对象都是空的或只包含空白字符")
            return None
        
        # 2. 如果有多个有效文本，可以根据不同的策略选择
        #    这里使用最简单的策略：选择第一个有效文本
        selected_text = valid_texts[0]
        raw_content = selected_text['content']
        
        # 3. 清理文本使其适合作为块名
        cleaned_content = self.clean_text_for_block_name(raw_content)
        
        logger.info(f"选择文本作为块名: 原始='{raw_content}', 清理后='{cleaned_content}'")
        return cleaned_content
    
    def generate_block_name_from_texts(self, text_objects: List[Dict[str, Any]], 
                                     strategy: str = 'first_valid') -> Optional[str]:
        """
        根据文本对象生成块名
        
        参数:
        text_objects: 文本对象列表
        strategy: 选择策略，支持'first_valid'（第一个有效文本）或'combine'（组合所有文本）
        
        返回:
        str: 生成的块名
        """
        if strategy == 'first_valid':
            return self.select_best_text_for_block_name(text_objects)
        elif strategy == 'combine':
            # 组合所有有效文本
            valid_texts = [
                text['content'].strip() for text in text_objects 
                if text.get('content') and text.get('content').strip()
            ]
            
            if not valid_texts:
                return None
            
            # 组合文本，用下划线分隔
            combined_text = '_'.join(valid_texts)
            return self.clean_text_for_block_name(combined_text)
        else:
            logger.warning(f"未知的选择策略: {strategy}，使用默认策略'first_valid'")
            return self.select_best_text_for_block_name(text_objects)
    
    def analyze_text_objects(self, text_objects: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        分析文本对象列表，返回统计信息
        
        参数:
        text_objects: 文本对象列表
        
        返回:
        dict: 文本分析结果
        """
        if not text_objects:
            return {
                'total_texts': 0,
                'valid_texts': 0,
                'empty_texts': 0,
                'text_types': {},
                'suggested_block_name': None
            }
        
        # 统计不同类型的文本
        text_types = {}
        valid_texts_count = 0
        empty_texts_count = 0
        
        for text in text_objects:
            text_type = text.get('type', 'UNKNOWN')
            text_types[text_type] = text_types.get(text_type, 0) + 1
            
            if text.get('content') and text.get('content').strip():
                valid_texts_count += 1
            else:
                empty_texts_count += 1
        
        # 生成建议的块名
        suggested_block_name = self.generate_block_name_from_texts(text_objects)
        
        analysis_result = {
            'total_texts': len(text_objects),
            'valid_texts': valid_texts_count,
            'empty_texts': empty_texts_count,
            'text_types': text_types,
            'suggested_block_name': suggested_block_name
        }
        
        return analysis_result
