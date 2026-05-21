import pandas as pd

downloads = "/Users/kristaspada/Downloads"

events = pd.read_csv(f"{downloads}/events.csv")
items = pd.read_csv(f"{downloads}/items.csv")
users = pd.read_csv(f"{downloads}/users.csv")

# Keep only completed purchases
purchase_events = events[events["type"] == "purchase"].copy()

# Join events to item/product details
purchase_events = purchase_events.merge(
    items,
    left_on="item_id",
    right_on="id",
    how="inner",
    suffixes=("_event", "_item")
)

# Join buyer/customer details
purchase_events = purchase_events.merge(
    users,
    left_on="user_id",
    right_on="id",
    how="left",
    suffixes=("", "_user")
)

purchase_events["purchase_date"] = pd.to_datetime(purchase_events["date_event"]).dt.date
purchase_events["purchase_month"] = pd.to_datetime(purchase_events["date_event"]).dt.to_period("M").astype(str)
purchase_events["price_in_usd"] = purchase_events["price_in_usd"].astype(float)
purchase_events["ltv"] = purchase_events["ltv"].astype(float)

# Find top country per product
product_country_units = (
    purchase_events
    .groupby(["item_id", "country"])
    .size()
    .reset_index(name="country_units")
    .sort_values(["item_id", "country_units", "country"], ascending=[True, False, True])
)

top_country = product_country_units.drop_duplicates("item_id")

# Roll up product sales
product_rollup = (
    purchase_events
    .groupby(["item_id", "name", "variant", "category"])
    .agg(
        units_sold=("item_id", "size"),
        revenue_usd=("price_in_usd", "sum"),
        unique_buyers=("user_id", "nunique"),
        purchase_sessions=("ga_session_id", "nunique"),
        avg_unit_price_usd=("price_in_usd", "mean"),
        avg_buyer_ltv_usd=("ltv", "mean"),
        first_purchase_date=("purchase_date", "min"),
        last_purchase_date=("purchase_date", "max")
    )
    .reset_index()
)

product_rollup = product_rollup.merge(
    top_country[["item_id", "country", "country_units"]],
    on="item_id",
    how="left"
)

product_rollup = product_rollup.rename(columns={
    "name": "product_name",
    "country": "top_country",
    "country_units": "top_country_units"
})

product_rollup["revenue_usd"] = product_rollup["revenue_usd"].round(2)
product_rollup["avg_unit_price_usd"] = product_rollup["avg_unit_price_usd"].round(2)
product_rollup["avg_buyer_ltv_usd"] = product_rollup["avg_buyer_ltv_usd"].round(2)

top_products = (
    product_rollup
    .sort_values(
        ["units_sold", "revenue_usd", "product_name"],
        ascending=[False, False, True]
    )
    .head(25)
    .reset_index(drop=True)
)

top_products.insert(0, "product_rank", top_products.index + 1)

output_path = "/Users/kristaspada/Desktop/Analysis_Export/top_sellers_products_python_results.csv"
top_products.to_csv(output_path, index=False)

print(top_products)
print(f"Saved results to: {output_path}")