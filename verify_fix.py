from src.agents.telesales_agent import TelesalesAgent
import pandas as pd

def verify_fix():
    agent = TelesalesAgent()
    # Get a client
    query = "SELECT TOP 1 Codigo_Cliente FROM FAL_IA_Dados_Vendas_Televendas WHERE Data_Emissao >= DATEADD(month, -3, GETDATE())"
    try:
        df = agent.db.get_dataframe(query)
        if df.empty:
            print("No clients found.")
            return
        
        card_code = df.iloc[0]['Codigo_Cliente']
        print(f"Testing for Client: {card_code}")

        # Call get_bales_breakdown
        df_breakdown = agent.get_bales_breakdown(card_code)
        print("\nBreakdown (Top 5):")
        print(df_breakdown.head(5).to_string())

        # Call get_volume_insights
        # print("\nVolume Insights (Top 5):")
        # print(agent.get_volume_insights(90))

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    verify_fix()
