from src.agents.telesales_agent import TelesalesAgent
import pandas as pd

def debug_view():
    agent = TelesalesAgent()
    query = "SELECT TOP 1 * FROM FAL_IA_Dados_Vendas_Televendas"
    try:
        df = agent.db.get_dataframe(query)
        print("\n".join(df.columns.tolist()))
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_view()
