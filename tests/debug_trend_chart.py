
import sys
import os
import pandas as pd

# Adiciona o diretório raiz ao path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from src.database.connector import DatabaseConnector

def debug_trend():
    db = DatabaseConnector()
    card_code = 'C004843'
    months = 6
    
    print(f"--- Debugging Trend for {card_code} ---")
    
    # 1. Run the exact query from telesales_agent.py
    query = f"""
            SELECT 
                FORMAT(Data_Emissao, 'MM/yy') as Mes,
                CASE 
                    WHEN Categoria_Produto LIKE '%ARROZ%' THEN 'Arroz'
                    WHEN Categoria_Produto LIKE '%FEIJAO%' THEN 'Feijão'
                    WHEN Categoria_Produto LIKE '%MASSA%' THEN 'Massas'
                    ELSE 'Outros'
                END as Categoria,
                SUM(Valor_Liquido) as Total,
                MIN(Data_Emissao) as SortDate,
                MAX(Categoria_Produto) as Raw_Categoria_Sample
            FROM FAL_IA_Dados_Vendas_Televendas 
            WHERE Codigo_Cliente = :card_code 
              AND Data_Emissao >= DATEADD(month, -{months}, GETDATE())
            GROUP BY FORMAT(Data_Emissao, 'MM/yy'),
                     CASE 
                        WHEN Categoria_Produto LIKE '%ARROZ%' THEN 'Arroz'
                        WHEN Categoria_Produto LIKE '%FEIJAO%' THEN 'Feijão'
                        WHEN Categoria_Produto LIKE '%MASSA%' THEN 'Massas'
                        ELSE 'Outros'
                     END
            ORDER BY SortDate ASC
            """
            
    try:
        df = db.get_dataframe(query, params={"card_code": card_code})
        print("--- Result DataFrame ---")
        if df.empty:
            print("DataFrame is EMPTY!")
        else:
            print(df.to_markdown())
            
        print("\n--- Raw Data Inspection (Last 10 Sales) ---")
        # Check raw data to see why it might be failing
        raw_query = f"""
        SELECT TOP 10 Data_Emissao, Valor_Liquido, Categoria_Produto, SKU, Nome_Produto 
        FROM FAL_IA_Dados_Vendas_Televendas 
        WHERE Codigo_Cliente = :card_code 
        ORDER BY Data_Emissao DESC
        """
        raw_df = db.get_dataframe(raw_query, params={"card_code": card_code})
        print(raw_df.to_markdown())

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_trend()
