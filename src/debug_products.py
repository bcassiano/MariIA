from agents.telesales_agent import TelesalesAgent
import pandas as pd

agent = TelesalesAgent()
try:
    df = agent.get_top_products(days=90)
    print(f"--- TOP 50 PRODUTOS (Total: {len(df)}) ---")
    if not df.empty:
        print(df.to_markdown(index=False))
    else:
        print("Nenhum produto encontrado.")
except Exception as e:
    print(f"Erro: {e}")
