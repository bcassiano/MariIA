
import pandas as pd
import os
import sys

# Adiciona o diretório raiz ao path
sys.path.append(os.path.abspath(os.path.join(os.getcwd())))

from src.database.connector import DatabaseConnector

db = DatabaseConnector()
try:
    print("\nColumns in FAL_IA_Dados_Vendas_Televendas:")
    df_sample = db.get_dataframe("SELECT TOP 1 * FROM FAL_IA_Dados_Vendas_Televendas")
    print(df_sample.columns.tolist())

except Exception as e:
    print(f"Error: {e}")
