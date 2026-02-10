from src.agents.telesales_agent import TelesalesAgent

agent = TelesalesAgent()

print("=== Testando dados sem filtro de vendedor ===")
df = agent.get_sales_insights(0, 90, None)
print(f"Total de clientes (90 dias): {len(df)}")

if len(df) > 0:
    print("\nPrimeiros 5 clientes:")
    print(df[['Nome_Cliente', 'Cidade', 'Total_Venda']].head())
else:
    print("\nNENHUM DADO ENCONTRADO!")
    print("\nVerificando se há vendas na tabela...")
    df_check = agent.db.get_dataframe("""
        SELECT TOP 5 
            Data_Emissao,
            Vendedor_Atual,
            COUNT(*) as Total
        FROM FAL_IA_Dados_Vendas_Televendas
        WHERE Data_Emissao >= DATEADD(day, -90, GETDATE())
        GROUP BY Data_Emissao, Vendedor_Atual
        ORDER BY Data_Emissao DESC
    """)
    print(df_check)
