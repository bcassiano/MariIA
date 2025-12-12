from agents.telesales_agent import TelesalesAgent
import pandas as pd

agent = TelesalesAgent()

def test_filter(min_d, max_d):
    print(f"\n--- TESTANDO FILTRO: {min_d} a {max_d} dias ---")
    try:
        df = agent.get_inactive_customers(min_days=min_d, max_days=max_d)
        print(f"Total encontrado: {len(df)}")
        if not df.empty:
            print(df[['Codigo_Cliente', 'Ultima_Compra']].head().to_markdown(index=False))
        else:
            print("Nenhum registro.")
            
        # Debug extra: Ver range de datas
        print("--- RANGE DE DATAS NO BANCO ---")
        query = "SELECT MIN(Data_Emissao) as Mais_Antiga, MAX(Data_Emissao) as Mais_Recente FROM FAL_IA_Dados_Vendas_Televendas"
        df_range = agent.db.get_dataframe(query)
        print(df_range)
        
        print("--- CLIENTES INATIVOS RECENTES (> 10 DIAS) ---")
        query = """
        SELECT TOP 10 Codigo_Cliente, MAX(Data_Emissao) as Ultima
        FROM FAL_IA_Dados_Vendas_Televendas
        GROUP BY Codigo_Cliente
        HAVING MAX(Data_Emissao) < DATEADD(day, -10, GETDATE())
        ORDER BY Ultima DESC
        """
        print(agent.db.get_dataframe(query))
            
    except Exception as e:
        print(f"Erro: {e}")

test_filter(15, 25)
test_filter(26, 30)
