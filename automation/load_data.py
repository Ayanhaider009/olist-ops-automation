"""
Load the Olist CSVs into Supabase.

Usage:
    pip install pandas supabase python-dotenv
    python load_data.py

Reads SUPABASE_URL, SUPABASE_SERVICE_KEY and DATA_DIR from a .env file.
Safe to re-run: rows are upserted, so nothing gets duplicated.
"""

import json
import os
import time

import pandas as pd
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

DATA_DIR = os.getenv("DATA_DIR", "data/archive")
BATCH_SIZE = 1000

sb = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_KEY"])


def read_csv(name: str) -> pd.DataFrame:
    """Read a CSV with every column as text, so IDs and zip codes keep their leading zeros."""
    return pd.read_csv(os.path.join(DATA_DIR, name), dtype=str)


def to_numeric(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    for col in cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def upload(table: str, df: pd.DataFrame, conflict: str) -> None:
    """Upsert a dataframe into Supabase in batches. Empty cells become NULL."""
    rows = json.loads(df.to_json(orient="records"))
    total = len(rows)
    start = time.time()

    for i in range(0, total, BATCH_SIZE):
        batch = rows[i : i + BATCH_SIZE]
        for attempt in range(3):
            try:
                sb.table(table).upsert(batch, on_conflict=conflict).execute()
                break
            except Exception as err:
                if attempt == 2:
                    raise
                print(f"  retrying batch {i} of {table} after error: {err}")
                time.sleep(2)
        print(f"  {table}: {min(i + BATCH_SIZE, total):,}/{total:,}", end="\r")

    print(f"  {table}: {total:,} rows loaded in {time.time() - start:.0f}s      ")


def main() -> None:
    # Order matters: parent tables first, because of the foreign keys.

    customers = read_csv("olist_customers_dataset.csv")
    upload("customers", customers, "customer_id")

    sellers = read_csv("olist_sellers_dataset.csv")
    upload("sellers", sellers, "seller_id")

    products = read_csv("olist_products_dataset.csv")
    translation = read_csv("product_category_name_translation.csv")
    products = products.merge(translation, on="product_category_name", how="left")
    products = products[
        ["product_id", "product_category_name", "product_category_name_english", "product_weight_g"]
    ]
    products = to_numeric(products, ["product_weight_g"])
    upload("products", products, "product_id")

    orders = read_csv("olist_orders_dataset.csv")
    upload("orders", orders, "order_id")

    items = read_csv("olist_order_items_dataset.csv")
    items = to_numeric(items, ["order_item_id", "price", "freight_value"])
    upload("order_items", items, "order_id,order_item_id")

    reviews = read_csv("olist_order_reviews_dataset.csv")
    reviews = reviews.drop_duplicates(subset=["review_id", "order_id"])
    reviews = to_numeric(reviews, ["review_score"])
    upload("reviews", reviews, "review_id,order_id")

    print("\nDone. Check the Table Editor in Supabase.")


if __name__ == "__main__":
    main()
