
import pandas as pd
import os
import sys

# Adiciona o diretório raiz ao path
sys.path.append(os.path.abspath(os.path.join(os.getcwd())))

from src.database.connector import DatabaseConnector

db = DatabaseConnector()
card_code = "C007119" # Sample from screenshot
query = "SELECT TOP 5 * FROM FAL_IA_Dados_Vendas_Televendas WHERE Codigo_Cliente = :card_code"
try:
    df = db.get_dataframe(query, params={"card_code": card_code})
    print(f"Data for {card_code}:")
    if df.empty:
        print("Empty DataFrame returned for this CardCode.")
    else:
        print(df.to_markdown())
    
    if df.empty:
        print("\nChecking first 5 rows of the table to see column names and sample values:")
        df_sample = db.get_dataframe("SELECT TOP 5 * FROM FAL_IA_Dados_Vendas_Televendas")
        print(df_sample.to_markdown())
        print("\nColumns:", df_sample.columns.tolist())

except Exception as e:
    print(f"Error: {e}")
