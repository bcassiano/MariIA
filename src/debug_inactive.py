from agents.telesales_agent import TelesalesAgent
import pandas as pd

agent = TelesalesAgent()
try:
    df = agent.get_inactive_customers(days=30)
    print(f"--- CLIENTES INATIVOS (Total: {len(df)}) ---")
    if not df.empty:
        print(df.head().to_markdown(index=False))
        print("\n--- COLUNAS ---")
        print(df.columns.tolist())
        print("\n--- AMOSTRA DE DATAS ---")
        print(df['Ultima_Compra'].head())
    else:
        print("Nenhum cliente inativo encontrado.")
except Exception as e:
    print(f"Erro: {e}")
