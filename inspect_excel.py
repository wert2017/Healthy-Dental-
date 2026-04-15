import pandas as pd
import sys

try:
    file_path = r'c:\HD\HISTORIA HD SUR.xlsx'
    df = pd.read_excel(file_path)
    
    print("Columns in Excel File:")
    print(df.columns.tolist())
    
    print("\nFirst 5 rows:")
    # print all columns without truncating
    pd.set_option('display.max_columns', None)
    print(df.head(5).to_string())
    
    print(f"\nTotal rows: {len(df)}")
except Exception as e:
    print(f"Error reading file: {e}")
