import pandas as pd

# Read the Excel file
try:
    df = pd.read_excel('1111.xlsx')
    print("Excel file successfully read!")
    print(f"Number of rows: {len(df)}")
    print(f"Number of columns: {len(df.columns)}")
    print(f"Columns: {list(df.columns)}")
    print("\nFirst 10 rows:")
    print(df.head(10))
except Exception as e:
    print(f"Error reading Excel file: {e}")