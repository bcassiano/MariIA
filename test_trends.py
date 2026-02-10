from src.agents.telesales_agent import TelesalesAgent
import pandas as pd

agent = TelesalesAgent()
print("=== Buscando C003550 na View ===")

df_check = agent.db.get_dataframe("""
    SELECT DISTINCT Codigo_Cliente, Nome_Cliente, Vendedor_Atual 
    FROM FAL_IA_Dados_Vendas_Televendas 
    WHERE Codigo_Cliente LIKE '%C003550%'
""")
if not df_check.empty:
    print("Cliente encontrado:")
    print(df_check.to_string(index=False))
else:
    print("Cliente C003550 NÃO ENCONTRADO na view.")
    
print("\n=== Verificando Vendas (Últimos 12 meses) ===")
df_vendas = agent.db.get_dataframe("""
    SELECT TOP 10 Data_Emissao, Valor_Liquido, Categoria_Produto
    FROM FAL_IA_Dados_Vendas_Televendas
    WHERE Codigo_Cliente LIKE '%C003550%'
    ORDER BY Data_Emissao DESC
""")
if not df_vendas.empty:
    print(df_vendas.to_string(index=False))
else:
    print("Nenhuma venda encontrada para esse cliente na view.")

print("\n=== Testando get_sales_trend ===")
trend = agent.get_sales_trend('C003550', months=12)
print("Resultado da função:", trend)
