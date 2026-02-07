
import sys
import os
import pandas as pd

# Adiciona o diretório raiz ao path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from src.database.connector import DatabaseConnector

def debug_trend_fix():
    try:
        db = DatabaseConnector()
        card_code = 'C004843'
        months = 6
        
        output = []
        output.append(f"--- Debugging Trend Fix (CAST FLOAT) for {card_code} ---")
        
        # 1. Run the query with CAST
        query = f"""
                SELECT 
                    FORMAT(Data_Emissao, 'MM/yy') as Mes,
                    CASE 
                        WHEN Categoria_Produto LIKE '%ARROZ%' THEN 'Arroz'
                        WHEN Categoria_Produto LIKE '%FEIJAO%' THEN 'Feijão'
                        WHEN Categoria_Produto LIKE '%MASSA%' THEN 'Massas'
                        ELSE 'Outros'
                    END as Categoria,
                    SUM(CAST(Valor_Liquido AS FLOAT)) as Total,
                    MIN(Data_Emissao) as SortDate
                FROM FAL_IA_Dados_Vendas_Televendas 
                WHERE Codigo_Cliente = '{card_code}'
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
        
        output.append("\n--- Trend Query Results (With CAST) ---")
        df = db.get_dataframe(query)
        if df.empty:
            output.append("DataFrame is EMPTY!")
        else:
            output.append(df.to_markdown())
            
        print("\n".join(output))

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_trend_fix()
