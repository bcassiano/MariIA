from src.agents.telesales_agent import TelesalesAgent
import pandas as pd

agent = TelesalesAgent()
print("Conectado ao banco.\n")

print("=== Vendedores com Vendas (Últimos 30 dias) ===")
try:
    df_vendedores = agent.db.get_dataframe("""
        SELECT TOP 10 Vendedor_Atual, COUNT(*) as Total_Vendas
        FROM FAL_IA_Dados_Vendas_Televendas
        WHERE Data_Emissao >= DATEADD(day, -30, GETDATE())
          AND Vendedor_Atual IS NOT NULL
        GROUP BY Vendedor_Atual
        ORDER BY COUNT(*) DESC
    """)
    if not df_vendedores.empty:
        print(df_vendedores.to_string(index=False))
    else:
        print("Nenhum vendedor encontrado com vendas nos últimos 30 dias.")
        
    print("\nVerificando especificamente 'Renata' e 'Elen':")
    df_specific = agent.db.get_dataframe("""
        SELECT Vendedor_Atual, COUNT(*) as Total_Vendas
        FROM FAL_IA_Dados_Vendas_Televendas
        WHERE Data_Emissao >= DATEADD(day, -30, GETDATE())
          AND Vendedor_Atual IN ('Renata', 'Elen')
        GROUP BY Vendedor_Atual
    """)
    print(df_specific.to_string(index=False) if not df_specific.empty else "Nenhuma venda para Renata ou Elen.")

except Exception as e:
    print(f"Erro ao consultar vendedores: {e}")
