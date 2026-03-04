import re

def test_unicode_decoding():
    """测试Unicode转义序列解码功能"""
    test_cases = [
        # 测试用例：包含各种Unicode转义序列格式的文本
        r'\\U+5f2f\\U+677f',  # 法兰
        r'\\U5f2f\\U677f',     # 法兰
        r'\\u+5f2f\\u+677f',   # 法兰
        r'\\u5f2f\\u677f',     # 法兰
        r'法兰',                # 直接的汉字
    ]
    
    print("测试Unicode转义序列解码功能：")
    print("=" * 60)
    
    for i, test_text in enumerate(test_cases):
        print(f"\n测试用例 {i+1}: {repr(test_text)}")
        print("-" * 40)
        
        try:
            def _decode_unicode(m):
                hexstr = m.group(1)
                try:
                    # 支持4-6位十六进制数
                    cp = int(hexstr, 16)
                    return chr(cp)
                except Exception as e:
                    print(f"  解码错误: {e}")
                    return m.group(0)
            
            # 处理多种Unicode转义序列格式
            result = re.sub(r'\\U\+([0-9A-Fa-f]{4,6})', _decode_unicode, test_text)
            result = re.sub(r'\\U([0-9A-Fa-f]{4,6})', _decode_unicode, result)
            result = re.sub(r'\\u\+([0-9A-Fa-f]{4})', _decode_unicode, result)
            result = re.sub(r'\\u([0-9A-Fa-f]{4})', _decode_unicode, result)
            
            print(f"处理结果: {repr(result)}")
            print(f"是否包含问号: {'?' in result}")
        except Exception as e:
            print(f"处理出错: {e}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_unicode_decoding()