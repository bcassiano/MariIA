from src.database.connector import DatabaseConnector
import pandas as pd

def check_db():
    print("Checking Database Connection...")
    try:
        db = DatabaseConnector()
        # Simple query to check connection
        df = db.get_dataframe("SELECT 1 as Connected")
        if not df.empty and df.iloc[0]['Connected'] == 1:
            print("Database Connection: OK")
            return True
        else:
            print("Database Connection: Failed (Unexpected Result)")
            return False
    except Exception as e:
        print(f"Database Connection: Failed ({str(e)})")
        return False

if __name__ == "__main__":
    check_db()
