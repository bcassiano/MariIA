import sys
import os
import pandas as pd
from sqlalchemy import text

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from src.database.connector import DatabaseConnector

def inspect_units():
    db = DatabaseConnector()
    query = "SELECT DISTINCT Unidade_Medida FROM FAL_IA_Dados_Vendas_Televendas"
    try:
        df = db.get_dataframe(query)
        print(df.to_string())
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    inspect_units()
