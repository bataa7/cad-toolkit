import sys
import os

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from block_finder import BlockFinder

def test_unicode_decoding():
    """测试block_finder中的Unicode转义序列解码功能"""
    test_cases = [
        # 测试用例：包含各种Unicode转义序列格式的文本
        r'\\U+5f2f\\U+677f',  # 法兰
        r'\\U5f2f\\U677f',     # 法兰
        r'\\u+5f2f\\u+677f',   # 法兰
        r'\\u5f2f\\u677f',     # 法兰
        r'法兰',                # 直接的汉字
        r'1303000024013 \\U+5f2f\\U+677f 101008005460',  # 混合文本
    ]
    
    print("测试block_finder中的Unicode转义序列解码功能：")
    print("=" * 60)
    
    block_finder = BlockFinder()
    
    for i, test_text in enumerate(test_cases):
        print(f"\n测试用例 {i+1}: {repr(test_text)}")
        print("-" * 40)
        
        try:
            result = block_finder._decode_unicode_escape(test_text)
            print(f"处理结果: {repr(result)}")
            print(f"是否包含问号: {'?' in result}")
            print(f"是否包含原始转义序列: {'\\U+' in result or '\\U' in result or '\\u+' in result or '\\u' in result}")
        except Exception as e:
            print(f"处理出错: {e}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_unicode_decoding()