import os
import sys
import re
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from cad_reader import CADReader

def test_unicode_decoding():
    """测试Unicode转义序列解码"""
    # 测试用例：包含各种Unicode转义序列的文本
    test_cases = [
        # 正常中文文本
        "法兰",
        # 包含Unicode转义序列的文本
        "\\U+5f2f\\U+677f",
        "\\U5f2f\\U677f",
        "\\u+5f2f\\u+677f",
        "\\u5f2f\\u677f",
        # 混合格式
        "1303000024013 \\U+5f2f\\U+677f 101008005460",
        # 包含DXF格式标记的文本
        "{\\fSimSun|b0|i0|c134|p2;\\U+5f2f\\U+677f}"
    ]
    
    print("测试Unicode转义序列解码：")
    print("=" * 60)
    
    # 测试当前的正则表达式
    def test_current_regex():
        print("\n测试当前正则表达式：")
        print("-" * 40)
        
        # 当前的正则表达式
        pattern = re.compile(r'(\\U\\+|\\U|\\u\\+|\\u)([0-9A-Fa-f]+)')
        
        def decode_unicode(m):
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
        
        for test_text in test_cases:
            result = pattern.sub(decode_unicode, test_text)
            print(f"输入: {repr(test_text)}")
            print(f"输出: {repr(result)}")
            print(f"是否包含问号: {'?' in result}")
    
    # 测试修复后的正则表达式
    def test_fixed_regex():
        print("\n测试修复后的正则表达式：")
        print("-" * 40)
        
        # 修复后的正则表达式
        pattern = re.compile(r'(\\U\+|\\U|\\u\+|\\u)([0-9A-Fa-f]+)')
        
        def decode_unicode(m):
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
        
        for test_text in test_cases:
            result = pattern.sub(decode_unicode, test_text)
            print(f"输入: {repr(test_text)}")
            print(f"输出: {repr(result)}")
            print(f"是否包含问号: {'?' in result}")
    
    # 运行测试
    test_current_regex()
    test_fixed_regex()
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_unicode_decoding()
