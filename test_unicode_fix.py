import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from text_processor import TextProcessor

def test_unicode_decoding():
    processor = TextProcessor()
    
    # 测试包含Unicode转义序列的文本
    test_cases = [
        '{\\fSimSun|b0|i0|c134|p2;\\U+5f2f\\U+677f}',
        '{\\fSimSun|b0|i0|c134|p2;\\U+5f2f\\U+677f}',
        '\\U+5f2f\\U+677f',
        '弯板'
    ]
    
    print('测试Unicode转义序列解码：')
    print('=' * 60)
    
    for test in test_cases:
        print(f'输入: {repr(test)}')
        result = processor.clean_text_for_block_name(test)
        print(f'输出: {repr(result)}')
        print(f'包含问号: {"?" in result}')
        print()

if __name__ == '__main__':
    test_unicode_decoding()
