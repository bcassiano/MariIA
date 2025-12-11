import sys
import os
sys.path.append(os.getcwd())
from src.database.connector import DatabaseConnector

db = DatabaseConnector()
query = "SELECT DISTINCT Vendedor FROM FAL_IA_Dados_Vendas_Televendas WHERE Vendedor LIKE '%Renata%'"
df = db.get_dataframe(query)

if not df.empty:
    with open('debug_output.txt', 'w', encoding='utf-8') as f:
        f.write(f"Columns: {df.columns.tolist()}\n\n")
        f.write("First Row Data:\n")
        for col, val in df.iloc[0].items():
            f.write(f"{col}: {val}\n")
        
        f.write("\nAll Rows for this Doc:\n")
        f.write(df.to_string())
else:
    print("Document not found.")
