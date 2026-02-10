from src.agents.telesales_agent import TelesalesAgent
import pandas as pd

agent = TelesalesAgent()
vendedor = 'V.vp - Renata Rodrigues'
print(f"=== Clientes com Vendas de '{vendedor}' (90 dias) ===")

df = agent.db.get_dataframe(f"""
    SELECT TOP 5 Codigo_Cliente, Nome_Cliente, SUM(Valor_Liquido) as Total
    FROM FAL_IA_Dados_Vendas_Televendas
    WHERE Vendedor_Atual = '{vendedor}'
      AND Data_Emissao >= DATEADD(day, -90, GETDATE())
    GROUP BY Codigo_Cliente, Nome_Cliente
    ORDER BY Total DESC
""")

if not df.empty:
    print(df.to_string(index=False))
else:
    print("Nenhum cliente encontrado nos últimos 90 dias para este vendedor.")
