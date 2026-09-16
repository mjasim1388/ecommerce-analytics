import pandas as pd
from pathlib import Path
from sqlalchemy import text
from db import engine

RAW = Path(__file__).resolve().parent.parent / "data" / "raw"


def load_table(csv_file, table_name, columns=None, chunksize=5000):
    path = RAW / csv_file
    print(f"Loading {csv_file} -> {table_name} ...")

    df = pd.read_csv(path)

    if columns:
        df = df[columns]

    # Convert timestamp columns if present
    for col in df.columns:
        if "timestamp" in col or "date" in col:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    df.to_sql(
        table_name,
        engine,
        if_exists="append",
        index=False,
        chunksize=chunksize,
        method="multi",
    )
    print(f"  -> {len(df):,} rows loaded")


if __name__ == "__main__":
    # Clear existing data
    with engine.connect() as conn:
        for t in ["order_items", "payments", "orders", "products", "customers"]:
            conn.execute(text(f"TRUNCATE TABLE {t};"))
        conn.commit()
    print("Existing data cleared.\n")

    load_table(
        "olist_customers_dataset.csv",
        "customers",
        ["customer_id", "customer_unique_id", "customer_city", "customer_state"],
    )

    load_table(
        "olist_orders_dataset.csv",
        "orders",
        [
            "order_id",
            "customer_id",
            "order_status",
            "order_purchase_timestamp",
            "order_delivered_customer_date",
            "order_estimated_delivery_date",
        ],
    )

    load_table(
        "olist_order_items_dataset.csv",
        "order_items",
        ["order_id", "order_item_id", "product_id", "seller_id", "price", "freight_value"],
    )

    load_table(
        "olist_products_dataset.csv",
        "products",
        ["product_id", "product_category_name"],
    )

    load_table(
        "olist_order_payments_dataset.csv",
        "payments",
        ["order_id", "payment_sequential", "payment_type", "payment_value"],
    )

    print("\nAll tables loaded successfully.")