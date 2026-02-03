
import sys
import os
import pandas as pd
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from src.database.connector import DatabaseConnector

# Setup
db = DatabaseConnector()

def check_skus():
    print("Checking get_top_products SKUs...")
    query = """
    SELECT TOP 20 SKU, MAX(Nome_Produto) as Produto 
    FROM FAL_IA_Dados_Vendas_Televendas 
    GROUP BY SKU
    """
    df = db.get_dataframe(query)
    print(df[['SKU', 'Produto']].head(10).to_markdown())
    print("\nTypes:")
    print(df.dtypes)

if __name__ == "__main__":
    check_skus()
