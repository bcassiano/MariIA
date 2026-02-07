
import sys
import os
import pandas as pd

# Adiciona o diretório raiz ao path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from src.database.connector import DatabaseConnector

def debug_doc():
    try:
        db = DatabaseConnector()
        doc_num = 248875
        print(f"--- Debugging Document {doc_num} ---")
        
        query = f"""
        SELECT Numero_Documento, Data_Emissao, Valor_Liquido, Vendedor_Atual, Codigo_Cliente
        FROM FAL_IA_Dados_Vendas_Televendas 
        WHERE Numero_Documento = {doc_num}
        """
        
        df = db.get_dataframe(query)
        print(df.to_markdown())
        
        if not df.empty:
            val = df.iloc[0]['Valor_Liquido']
            print(f"Value: {val} Type: {type(val)}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_doc()
