from src.agents.telesales_agent import TelesalesAgent
import pandas as pd

agent = TelesalesAgent()

print("Buscando 'Renata' ou 'Elen' (90 dias):")
df = agent.db.get_dataframe("""
    SELECT DISTINCT Vendedor_Atual 
    FROM FAL_IA_Dados_Vendas_Televendas 
    WHERE Data_Emissao >= DATEADD(day, -90, GETDATE()) 
      AND (Vendedor_Atual LIKE '%Renata%' OR Vendedor_Atual LIKE '%Elen%')
""")

if not df.empty:
    print("ENCONTRADO:")
    print(df.to_string(index=False))
else:
    print("Nenhum vendedor encontrado com Renata ou Elen nos ultimos 90 dias.")
    
print("\nTop 5 Vendedores com mais vendas (90 dias):")
df_top = agent.db.get_dataframe("""
    SELECT TOP 5 Vendedor_Atual, Count(*) as Total
    FROM FAL_IA_Dados_Vendas_Televendas
    WHERE Data_Emissao >= DATEADD(day, -90, GETDATE())
    GROUP BY Vendedor_Atual
    ORDER BY Total DESC
""")
print(df_top.to_string(index=False))
