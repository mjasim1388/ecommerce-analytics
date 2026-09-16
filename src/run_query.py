import sys
from pathlib import Path
import pandas as pd
from db import engine

def run_query_file(path):
    sql_path = Path(path).resolve()
    if not sql_path.exists():
        print(f"File not found: {sql_path}")
        return
    sql = sql_path.read_text(encoding="utf-8")
    df = pd.read_sql(sql, engine)
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 200)
    pd.set_option("display.float_format", lambda x: f"{x:,.2f}")
    print(f"\n=== {sql_path.name} ===\n")
    print(df.to_string(index=False))
    print(f"\nRows returned: {len(df)}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python run_query.py <path_to_sql_file>")
    else:
        run_query_file(sys.argv[1])