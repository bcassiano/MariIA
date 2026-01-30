import sys
import os
import pandas as pd

# Adiciona o diretório raiz ao path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.database.connector import DatabaseConnector

def debug_negative_average():
    db = DatabaseConnector()
    card_code = "C003617"
    
    query = f"""
    SELECT 
        Numero_Documento,
        Data_Emissao,
        SKU,
        Nome_Produto,
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
        print(df.head(20).to_markdown(index=False))
        print(f"\nSoma total quantidade: {df['Quantidade'].sum()}")

if __name__ == "__main__":
    debug_negative_average()
