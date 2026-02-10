from src.agents.telesales_agent import TelesalesAgent

agent = TelesalesAgent()

# Verifica dados gerais da view
print("=== Verificando view FAL_IA_Dados_Vendas_Televendas ===\n")

# Total de registros
df_total = agent.db.get_dataframe("SELECT COUNT(*) as Total FROM FAL_IA_Dados_Vendas_Televendas")
print(f"Total de registros na view: {df_total.iloc[0]['Total']}")

# Data mais recente
df_recent = agent.db.get_dataframe("""
    SELECT TOP 1 Data_Emissao, Vendedor_Atual, Nome_Cliente 
    FROM FAL_IA_Dados_Vendas_Televendas 
    ORDER BY Data_Emissao DESC
""")
print(f"\nVenda mais recente:")
print(df_recent)

# Vendedores disponíveis
df_vendedores = agent.db.get_dataframe("""
    SELECT DISTINCT Vendedor_Atual, COUNT(*) as Total
    FROM FAL_IA_Dados_Vendas_Televendas
    WHERE Vendedor_Atual IS NOT NULL
    GROUP BY Vendedor_Atual
    ORDER BY Total DESC
""")
print(f"\nVendedores na view (top 10):")
print(df_vendedores.head(10))
