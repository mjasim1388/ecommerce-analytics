from db import engine
from sqlalchemy import text

TABLES = ["customers", "orders", "order_items", "products", "payments"]

with engine.connect() as conn:
    print(f"{'Table':<15}{'Rows':>12}")
    print("-" * 27)
    for t in TABLES:
        count = conn.execute(text(f"SELECT COUNT(*) FROM {t};")).fetchone()[0]
        print(f"{t:<15}{count:>12,}")