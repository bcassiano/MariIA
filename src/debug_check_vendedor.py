import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from src.database.connector import DatabaseConnector

def check_vendedor():
    db = DatabaseConnector()
    try:
        df = db.get_dataframe("SELECT TOP 5 Vendedor, Vendedor_Atual FROM FAL_IA_Dados_Vendas_Televendas")
        print(df.to_markdown())
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_vendedor()
