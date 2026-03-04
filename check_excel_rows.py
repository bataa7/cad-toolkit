import pandas as pd
import os

excel_file = "1111.xlsx"
if not os.path.exists(excel_file):
    excel_file = "888.xlsx"

print(f"Checking {excel_file}...")
df = pd.read_excel(excel_file)

# Keywords to search
keywords = ["101002010375", "1303000017614", "1303000017615", "1303000017616"]

print(f"Total rows: {len(df)}")
print(f"Columns: {list(df.columns)}")

for idx, row in df.iterrows():
    row_str = str(row.values)
    found = False
    for kw in keywords:
        if kw in row_str:
            found = True
            break
    
    if found:
        print(f"\nRow {idx}:")
        # Print relevant columns
        for col in df.columns:
            val = row[col]
            if pd.notna(val):
                print(f"  {col}: {val}")
