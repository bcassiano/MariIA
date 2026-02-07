import sys
import os
import pandas as pd
from dotenv import load_dotenv

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))
from src.database.connector import DatabaseConnector

def check_slp_123():
    try:
        db = DatabaseConnector()
        print("\n--- Identify SlpCode 123 ---")
        query_code = "SELECT SlpCode, SlpName FROM OSLP WHERE SlpCode = 123"
        df_code = db.get_dataframe(query_code)
        
        if df_code.empty:
            print("No vendor found for SlpCode 123.")
        else:
            print("Found Vendor:")
            print(df_code.to_markdown(index=False))

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_slp_123()
