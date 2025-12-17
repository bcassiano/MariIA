import sys
import os
import pandas as pd

# Adiciona o diretório raiz ao path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.database.connector import DatabaseConnector

def debug_customer():
    db = DatabaseConnector()
    card_code = "C013314"
    
    query = f"""
    SELECT TOP 10
        Numero_Documento,
        Data_Emissao,
        SKU,
        Nome_Produto,
        Valor_Liquido,
        Valor_Total_Linha,
        Quantidade
    FROM FAL_IA_Dados_Vendas_Televendas
    WHERE Codigo_Cliente = '{card_code}'
    ORDER BY Data_Emissao DESC
    """
    
    print(f"Executando query para {card_code}...")
    df = db.get_dataframe(query)
    
    if df.empty:
        print("Nenhum dado encontrado.")
    else:
        print(df.to_markdown(index=False))

if __name__ == "__main__":
    debug_customer()
