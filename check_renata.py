from src.agents.telesales_agent import TelesalesAgent
import pandas as pd

agent = TelesalesAgent()
vendedor = 'V.vp - Renata Rodrigues'
print(f"=== Buscando Vendas de '{vendedor}' ===")

print("\n--- Top 10 Clientes (Ultimos 365 dias) ---")
df_top = agent.db.get_dataframe(f"""
    SELECT TOP 10 Codigo_Cliente, Nome_Cliente, SUM(Valor_Liquido) as Total, MAX(Data_Emissao) as Ultima
    FROM FAL_IA_Dados_Vendas_Televendas
    WHERE Vendedor_Atual = '{vendedor}'
      AND Data_Emissao >= DATEADD(day, -365, GETDATE())
    GROUP BY Codigo_Cliente, Nome_Cliente
    ORDER BY Total DESC
""")
print(df_top.to_string(index=False))

print("\n--- Verificando C003550 especificamente ---")
df_c = agent.db.get_dataframe(f"""
    SELECT Codigo_Cliente, Data_Emissao, Valor_Liquido, Categoria_Produto
    FROM FAL_IA_Dados_Vendas_Televendas
    WHERE Codigo_Cliente LIKE '%C003550%'
      AND Vendedor_Atual = '{vendedor}'
    ORDER BY Data_Emissao DESC
""")
if not df_c.empty:
    print(df_c.head(10).to_string(index=False))
else:
    print("Zero vendas encontradas para C003550 com este vendedor.")

print("\n--- Testando get_sales_trend para C003550 ---")
trend = agent.get_sales_trend('C003550', months=12)
print("Resultado:", trend)
