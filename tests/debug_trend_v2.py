
import sys
import os
import pandas as pd

# Adiciona o diretório raiz ao path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from src.database.connector import DatabaseConnector

def debug_trend():
    try:
        db = DatabaseConnector()
        card_code = 'C004843'
        months = 6
        
        output = []
        output.append(f"--- Debugging Trend for {card_code} ---")
        
        # 0. Check Date
        date_query = "SELECT GETDATE() as ServerDate"
        server_date = db.get_dataframe(date_query).iloc[0]['ServerDate']
        output.append(f"Server Date: {server_date}")

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
        
        output.append("\n--- Trend Query Results ---")
        df = db.get_dataframe(query)
        if df.empty:
            output.append("DataFrame is EMPTY!")
        else:
            output.append(df.to_markdown())
            
        output.append("\n--- Raw Data Inspection (Last 10 Sales) ---")
        raw_query = f"""
        SELECT TOP 10 
            Data_Emissao, 
            Valor_Liquido, 
            Categoria_Produto, 
            SKU, 
            Nome_Produto 
        FROM FAL_IA_Dados_Vendas_Televendas 
        WHERE Codigo_Cliente = '{card_code}'
        ORDER BY Data_Emissao DESC
        """
        raw_df = db.get_dataframe(raw_query)
        output.append(raw_df.to_markdown())
        
        # Write to file
        with open("debug_output.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(output))
            
        print("Debug output written to debug_output.txt")

    except Exception as e:
        print(f"Error: {e}")
        with open("debug_output.txt", "w", encoding="utf-8") as f:
            f.write(f"Error: {e}")

if __name__ == "__main__":
    debug_trend()
