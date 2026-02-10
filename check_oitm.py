from src.agents.telesales_agent import TelesalesAgent
import pandas as pd

def check_oitm():
    agent = TelesalesAgent()
    # Check SWeight1
    query = """
    SELECT ItemCode, ItemName, SalUnitMsr, NumInSale, SWeight1, IWeight1 
    FROM OITM 
    WHERE ItemCode IN ('SB00317', '0005')
    """
    try:
        df = agent.db.get_dataframe(query)
        print(df.to_dict(orient='records'))
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_oitm()
