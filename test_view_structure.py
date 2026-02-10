from src.agents.telesales_agent import TelesalesAgent
import pandas as pd

try:
    agent = TelesalesAgent()
    print("Conectado ao banco.")

    # 1. Listar Views
    print("\n=== Views Disponíveis (FAL_IA%) ===")
    df_views = agent.db.get_dataframe("SELECT name FROM sys.views WHERE name LIKE 'FAL_IA%'")
    if not df_views.empty:
        print(df_views)
    else:
        print("Nenhuma view encontrada com FAL_IA%")

    # 2. Verificar estrutura da view principal
    print("\n=== Estrutura FAL_IA_Dados_Vendas_Televendas (TOP 1) ===")
    try:
        df_struct = agent.db.get_dataframe("SELECT TOP 1 * FROM FAL_IA_Dados_Vendas_Televendas")
        if not df_struct.empty:
            print("Colunas encontradas:", list(df_struct.columns))
            print("Amostra:\n", df_struct.to_string())
        else:
            print("View existe mas está vazia (0 linhas totais).")
    except Exception as e:
        print(f"Erro ao ler view: {e}")

    # 3. Verificar dados recentes (30, 90, 180 dias)
    print("\n=== Contagem por período ===")
    periods = [30, 90, 180, 365]
    for days in periods:
        try:
            # 🛡️ SECURITY: Use safe parameterization for Data_Emissao lookup
            query = "SELECT COUNT(*) as Total FROM FAL_IA_Dados_Vendas_Televendas WHERE Data_Emissao >= DATEADD(day, :days, GETDATE())"
            df_count = agent.db.get_dataframe(query, params={"days": -days})
            count = df_count.iloc[0]['Total'] if not df_count.empty else 0
            print(f"Últimos {days} dias: {count} registros")
        except Exception as e:
            print(f"Erro ao contar {days} dias: {e}")

except Exception as e:
    print(f"Erro fatal no script: {e}")
