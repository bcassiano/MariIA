
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from src.database.connector import DatabaseConnector

db = DatabaseConnector()
query = "SELECT MAX(Data_Emissao) as LastDate FROM FAL_IA_Dados_Vendas_Televendas"
df = db.get_dataframe(query)
print(df)
