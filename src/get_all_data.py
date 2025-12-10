import sqlite3
import pandas as pd

from config import DB_PATH
   

def fetch_all(table_name):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
    conn.close()
    return df


if __name__ == "__main__":
    print("=== All Tickers ===")
    tickers = fetch_all("tickers")
    print(tickers)

    print("\n=== Industry Aggregates ===")
    industries = fetch_all("industry_aggregates")
    print(industries)
