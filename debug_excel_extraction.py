import os
import sys
import pandas as pd

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def debug_excel_extraction():
    """Debug Excel file extraction"""
    excel_file = '1111.xlsx'
    print(f"Loading Excel file: {excel_file}")
    
    df = pd.read_excel(excel_file)
    print(f"Excel file loaded successfully with {len(df)} rows")
    print(f"Columns: {list(df.columns)}")
    
    # Show material ID and drawing number columns
    print("\nMaterial ID and Drawing Number columns:")
    print(df[['物料ID', '图号']].head(20))
    
    # Check unique material IDs
    material_ids = df['物料ID'].unique()
    print(f"\nUnique material IDs: {len(material_ids)}")
    print(f"First 10 material IDs: {material_ids[:10]}")
    
    # Check for duplicate material IDs
    duplicate_material_ids = df[df.duplicated('物料ID', keep=False)]['物料ID'].unique()
    print(f"\nDuplicate material IDs: {len(duplicate_material_ids)}")
    print(f"First 10 duplicate material IDs: {duplicate_material_ids[:10]}")
    
    # Check drawing numbers
    drawing_nums = df['图号'].unique()
    print(f"\nUnique drawing numbers: {len(drawing_nums)}")
    print(f"First 10 drawing numbers: {drawing_nums[:10]}")

if __name__ == "__main__":
    debug_excel_extraction()