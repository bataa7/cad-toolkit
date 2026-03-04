import os
import sys
import logging
from text_processor import TextProcessor

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_text_processing():
    """测试文本处理功能，分析汉字显示为问号的问题"""
    processor = TextProcessor()
    
    # 测试用例：包含各种格式的文本
    test_cases = [
        # 正常中文文本
        "法兰",
        # 包含DXF格式标记的中文文本
        "{\\fSimSun|b0|i0|c134|p2;法兰}",
        # 包含Unicode转义序列的文本
        "{\\fSimSun|b0|i0|c134|p2;\\U+5f2f\\U+677f}",
        # 包含下划线的标识符
        "____1303000024016",
        # 混合文本
        "1303000024013 法兰 101008005460",
        # 包含特殊字符的文本
        "1303000024013-法兰_101008005460"
    ]
    
    print("测试文本处理功能：")
    print("=" * 60)
    
    for i, test_text in enumerate(test_cases):
        print(f"\n测试用例 {i+1}: {repr(test_text)}")
        print("-" * 40)
        
        try:
            result = processor.clean_text_for_block_name(test_text)
            print(f"处理结果: {repr(result)}")
            print(f"结果类型: {type(result)}")
            print(f"是否包含问号: {'?' in result}")
        except Exception as e:
            print(f"处理出错: {e}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_text_processing()
