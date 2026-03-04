import pandas as pd

def debug_material_ids():
    """Debug material IDs in Excel file"""
    excel_file = '1111.xlsx'
    print(f"Loading Excel file: {excel_file}")
    
    df = pd.read_excel(excel_file)
    
    # Show actual material ID values
    print("\nActual material ID values:")
    print("Raw value | String representation")
    print("-" * 50)
    
    for i, value in enumerate(df['物料ID'].head(20)):
        print(f"{value} | {str(value)}")
    
    # Check unique material IDs
    print(f"\nUnique material IDs: {len(df['物料ID'].unique())}")
    
    # Check material IDs in DXF file
    print("\nMaterial IDs found in DXF file:")
    dxf_material_ids = [
        '1303000024013', '1303000024079', '1303000024083', '1303000024084', 
        '1303000024086', '1303000024087', '1303000024705', '1303000024706', 
        '1303000024707', '1303000024701', '1303000024016', '1303000024026', 
        '1303000024027', '1303000024014', '1303000024015'
    ]
    
    print("First 15 material IDs from DXF file:")
    for mid in dxf_material_ids:
        print(f"- {mid}")
    
    # Check if any of these are in the Excel file
    print("\nChecking if DXF material IDs exist in Excel:")
    for mid in dxf_material_ids[:5]:
        # Check as string
        in_excel = any(str(df['物料ID'].iloc[i]) == mid for i in range(len(df)))
        print(f"Material ID {mid} in Excel: {in_excel}")

if __name__ == "__main__":
    debug_material_ids()