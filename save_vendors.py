from src.agents.telesales_agent import TelesalesAgent
import pandas as pd

agent = TelesalesAgent()
print("Executando busca...")

df = agent.db.get_dataframe("SELECT DISTINCT Vendedor_Atual FROM FAL_IA_Dados_Vendas_Televendas WHERE Data_Emissao >= DATEADD(day, -90, GETDATE()) AND (Vendedor_Atual LIKE '%Renata%' OR Vendedor_Atual LIKE '%Elen%')")

if not df.empty:
    df.to_csv('vendedores.csv', index=False)
    print(f"Encontrados {len(df)} vendedores. Salvo em vendedores.csv")
else:
    print("Zero encontrados")
