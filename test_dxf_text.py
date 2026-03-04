import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from cad_reader import CADReader
from text_processor import TextProcessor

def test_dxf_text_processing():
    # 测试CAD读取器和文本处理器
    cad_reader = CADReader('cad/测.dxf')
    text_processor = TextProcessor()
    
    if cad_reader.load_file():
        print('成功加载DXF文件')
        print('=' * 60)
        
        # 获取文本对象
        text_objects = cad_reader.get_text_objects()
        print(f'找到 {len(text_objects)} 个文本对象')
        print('-' * 40)
        
        # 处理每个文本对象
        for i, text_obj in enumerate(text_objects[:5]):  # 只显示前5个
            content = text_obj['content']
            print(f'文本 {i+1}:')
            print(f'  原始内容: {repr(content)}')
            print(f'  包含问号: {"?" in content}')
            
            # 处理文本
            processed = text_processor.clean_text_for_block_name(content)
            print(f'  处理后: {repr(processed)}')
            print(f'  处理后包含问号: {"?" in processed}')
            print()
        
        print('=' * 60)
    else:
        print('无法加载DXF文件')

if __name__ == '__main__':
    test_dxf_text_processing()
