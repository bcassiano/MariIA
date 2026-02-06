import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from src.database.connector import DatabaseConnector

def get_view_def():
    db = DatabaseConnector()
    try:
        # sp_helptext returns the definition in multiple rows
        df = db.get_dataframe("sp_helptext 'FAL_IA_Dados_Vendas_Televendas'")
        if not df.empty:
            # Join all text rows
            definition = "".join(df.iloc[:, 0].tolist())
            print(definition)
        else:
            print("View not found or no permission.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    get_view_def()
