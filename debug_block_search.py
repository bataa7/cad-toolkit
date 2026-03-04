import os
import sys
from block_finder import BlockFinder

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def debug_block_search():
    """Debug the block search process"""
    finder = BlockFinder()
    
    # Load Excel file
    excel_file = '1111.xlsx'
    print(f"Loading Excel file: {excel_file}")
    
    import pandas as pd
    df = pd.read_excel(excel_file)
    print(f"Excel file loaded successfully with {len(df)} rows")
    
    # Extract material info
    material_info = finder.extract_material_info(df)
    print(f"Extracted {len(material_info)} material info entries")
    
    # Print first 10 material info entries
    print("\nFirst 10 material info entries:")
    for i, (identifier, info) in enumerate(list(material_info.items())[:10]):
        print(f"{i+1}. Identifier: {identifier}, Qty: {info['total_qty']}, Material: {info['material']}, Thickness: {info['thickness']}")
    
    # Check DXF files
    dxf_files = []
    cad_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cad')
    if os.path.exists(cad_dir):
        for file in os.listdir(cad_dir):
            if file.endswith('.dxf'):
                dxf_files.append(os.path.join(cad_dir, file))
    
    print(f"\nFound {len(dxf_files)} DXF files:")
    for dxf_file in dxf_files:
        print(f"- {os.path.basename(dxf_file)}")
    
    # Test block search on first DXF file
    if dxf_files:
        test_file = dxf_files[0]
        print(f"\nTesting block search on: {os.path.basename(test_file)}")
        
        found_blocks = finder.search_blocks_in_dxf(test_file, material_info)
        print(f"Found {len(found_blocks)} blocks in this file")
        
        for identifier, blocks in found_blocks.items():
            print(f"- Identifier: {identifier}, Blocks found: {len(blocks)}")
            for block, info in blocks:
                print(f"  - Block name: {block.name}")

if __name__ == "__main__":
    debug_block_search()