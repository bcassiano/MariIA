
import pandas as pd
from src.core.database import DatabaseConnector

db = DatabaseConnector()
query = "SELECT TOP 1 * FROM VW_MariIA_ClientDetails"
try:
    df = db.get_dataframe(query)
    print("Columns in VW_MariIA_ClientDetails:")
    print(df.columns.tolist())
    if not df.empty:
        print("\nSample Data:")
        print(df.iloc[0].to_dict())
    else:
        print("\nView is empty!")
except Exception as e:
    print(f"Error: {e}")
