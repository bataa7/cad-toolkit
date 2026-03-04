import pandas as pd

def debug_specific_ids():
    """Debug specific material IDs"""
    excel_file = '1111.xlsx'
    df = pd.read_excel(excel_file)
    
    # Check if specific IDs exist
    specific_ids = ['1303000020177', '1303000020101']
    
    print("Checking specific material IDs:")
    for sid in specific_ids:
        # Check as string
        found = any(str(int(value)) == sid for value in df['物料ID'] if pd.notna(value))
        print(f"ID {sid} found: {found}")
    
    # Check drawing numbers
    print("\nChecking drawing numbers:")
    print("First 20 drawing numbers:")
    for i, dn in enumerate(df['图号'].head(20)):
        print(f"{i+1}. {dn}")

if __name__ == "__main__":
    debug_specific_ids()