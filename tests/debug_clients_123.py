import sys
import os
import pandas as pd
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from src.database.connector import DatabaseConnector

def check_clients_123():
    try:
        db = DatabaseConnector()
        print("\n--- Check Clients of SlpCode 123 (Elen Hasman) ---")
        query = """
        SELECT TOP 10 Codigo_Cliente, MAX(Nome_Cliente) as Cliente
        FROM FAL_IA_Dados_Vendas_Televendas
        WHERE Vendedor_Atual LIKE '%Elen Hasman%'
        GROUP BY Codigo_Cliente
        ORDER BY Cliente
        """
        df = db.get_dataframe(query)
        print(df.to_markdown(index=False))

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_clients_123()
