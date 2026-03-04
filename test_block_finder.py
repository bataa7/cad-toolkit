import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from block_finder import BlockFinder

def test_block_finder():
    finder = BlockFinder()
    excel_file = '1111.xlsx'
    output_dir = 'output_test'
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # 加载Excel文件
    df = finder.load_excel(excel_file)
    if df is None:
        print('无法加载Excel文件')
        return
    
    # 提取物料信息
    material_info = finder.extract_material_info(df)
    if not material_info:
        print('无法提取物料信息')
        return
    
    print(f'成功提取 {len(material_info)} 个物料信息')
    
    # 查找CAD目录中的DXF文件
    cad_dir = 'cad'
    dxf_files = []
    if os.path.exists(cad_dir):
        for file in os.listdir(cad_dir):
            if file.lower().endswith('.dxf'):
                dxf_files.append(os.path.join(cad_dir, file))
    
    if not dxf_files:
        print('未找到DXF文件')
        return
    
    print(f'找到 {len(dxf_files)} 个DXF文件')
    
    # 在所有DXF文件中搜索块
    all_found_blocks = {}
    processed_blocks = set()
    
    for dxf_file in dxf_files:
        print(f'处理DXF文件: {os.path.basename(dxf_file)}')
        found_blocks = finder.search_blocks_in_dxf(dxf_file, material_info)
        
        for identifier, blocks in found_blocks.items():
            if identifier not in all_found_blocks:
                unique_blocks = []
                for block, info in blocks:
                    block_key = block.name
                    if block_key not in processed_blocks:
                        unique_blocks.append((block, info))
                        processed_blocks.add(block_key)
                if unique_blocks:
                    all_found_blocks[identifier] = unique_blocks
    
    print(f'\n找到的块数量: {len(all_found_blocks)}')
    for identifier, blocks in all_found_blocks.items():
        print(f'标识符: {identifier}, 块数量: {len(blocks)}')
        for block, info in blocks:
            print(f'  - 块名: {block.name}')

if __name__ == '__main__':
    test_block_finder()
