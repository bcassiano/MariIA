
import sys
import os
import pandas as pd
from sqlalchemy import text
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from src.database.connector import DatabaseConnector

db = DatabaseConnector()

def check_sku_types():
    print("Checking SKU raw values...")
    # Tenta pegar um SKU que sabemos que deveria ter zeros
    query = "SELECT TOP 5 SKU, CAST(SKU as VARCHAR(50)) as SKU_Str, Nome_Produto FROM FAL_IA_Dados_Vendas_Televendas WHERE Nome_Produto LIKE '%SABOROSO%'"
    df = db.get_dataframe(query)
    print(df.to_markdown())

if __name__ == "__main__":
    check_sku_types()
