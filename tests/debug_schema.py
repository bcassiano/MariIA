
import sys
import os
import pandas as pd

# Adiciona o diretório raiz ao path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from src.database.connector import DatabaseConnector

def debug_schema():
    try:
        db = DatabaseConnector()
        print("--- Checking Schema for FAL_IA_Dados_Vendas_Televendas ---")
        
        query = """
        SELECT COLUMN_NAME, DATA_TYPE 
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_NAME = 'FAL_IA_Dados_Vendas_Televendas' AND COLUMN_NAME = 'Valor_Liquido'
        """
        
        df = db.get_dataframe(query)
        print(df.to_markdown())
        
        print("\n--- Checking Sample Value ---")
        # Get a raw value without python casting if possible (hard with pandas)
        # We'll just print what we get
        query_val = "SELECT TOP 1 Valor_Liquido FROM FAL_IA_Dados_Vendas_Televendas WHERE Codigo_Cliente = 'C004843'"
        df_val = db.get_dataframe(query_val)
        print(f"Sample Value: {df_val.iloc[0]['Valor_Liquido']} (Type: {type(df_val.iloc[0]['Valor_Liquido'])})")


    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_schema()
