"""
02_build_star_schema.py
-----------------------
Transforms the raw ERP-style extract into a small star schema and loads it
into a SQLite warehouse.

Star schema
    DIM_Date       - one row per calendar day in the extract
    DIM_Store      - store attributes (name, city, province, channel model)
    DIM_Product    - product master (category, unit price, base margin)
    DIM_Customer   - customer master (name, province)
    FACT_Sales     - one row per billing document line (sales AND credit-note
                     style return lines, identified by FactType)

Validation is printed at the end: row counts, referential integrity, and a
revenue reconciliation between the raw extract and the warehouse.

Outputs
    data/processed/retail_dw.sqlite
    data/processed/DIM_Date.csv / DIM_Store.csv / DIM_Product.csv / DIM_Customer.csv / FACT_Sales.csv
"""

from pathlib import Path

import numpy as np
import pandas as pd
import sqlite3

REPO = Path(__file__).resolve().parents[1]
RAW = REPO / "data" / "raw" / "sales_lines_2024_2025.csv"
OUT_DIR = REPO / "data" / "processed"
OUT_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = OUT_DIR / "retail_dw.sqlite"


def build_dimensions(df: pd.DataFrame, stores: pd.DataFrame) -> dict[str, pd.DataFrame]:
    # ---- DIM_Date --------------------------------------------------------
    dates = pd.DataFrame({"Date": pd.to_datetime(sorted(df["PostingDate"].unique()))})
    dates["DateKey"] = dates["Date"].dt.strftime("%Y%m%d").astype(int)
    dates["Year"] = dates["Date"].dt.year
    dates["Quarter"] = dates["Date"].dt.quarter
    dates["Month"] = dates["Date"].dt.month
    dates["MonthName"] = dates["Date"].dt.strftime("%b")
    dates["YearMonth"] = dates["Date"].dt.strftime("%Y-%m")
    dates["DayName"] = dates["Date"].dt.day_name()
    dates["IsWeekend"] = dates["Date"].dt.dayofweek.isin([5, 6]).astype(int)

    # ---- DIM_Store / DIM_Product / DIM_Customer --------------------------
    store_dim = stores.rename(columns={"StoreID": "StoreKey"}).copy()

    product_dim = (
        df[["MaterialNo", "Category", "UnitPriceZAR"]]
        .drop_duplicates("MaterialNo")
        .rename(columns={"MaterialNo": "ProductKey"})
        .reset_index(drop=True)
    )

    customer_dim = (
        df[["CustomerNo"]]
        .drop_duplicates()
        .rename(columns={"CustomerNo": "CustomerKey"})
        .reset_index(drop=True)
    )

    # ---- FACT_Sales ------------------------------------------------------
    date_key = dates.set_index("Date")["DateKey"]
    fact = df.copy()
    fact["DateKey"] = pd.to_datetime(fact["PostingDate"]).map(date_key)
    fact["FactType"] = np.where(fact["Qty"] < 0, "Return", "Sale")
    fact["SalesAmountZAR"] = fact["LineNetZAR"]
    fact["CostAmountZAR"] = fact["LineCostZAR"]
    fact["GrossMarginZAR"] = fact["SalesAmountZAR"] - fact["CostAmountZAR"]

    fact = fact[
        [
            "DocumentNo", "LineItem", "DateKey", "StoreID", "Channel",
            "CustomerNo", "MaterialNo", "Category", "FactType", "Qty",
            "UnitPriceZAR", "DiscountPct", "SalesAmountZAR", "CostAmountZAR",
            "GrossMarginZAR", "PromoFlag",
        ]
    ].rename(columns={"StoreID": "StoreKey", "CustomerNo": "CustomerKey", "MaterialNo": "ProductKey"})

    return {
        "DIM_Date": dates,
        "DIM_Store": store_dim,
        "DIM_Product": product_dim,
        "DIM_Customer": customer_dim,
        "FACT_Sales": fact,
    }


def load_sqlite(tables: dict[str, pd.DataFrame]) -> None:
    if DB_PATH.exists():
        DB_PATH.unlink()
    with sqlite3.connect(DB_PATH) as con:
        for name, frame in tables.items():
            frame.to_sql(name, con, index=False)


def validate(raw: pd.DataFrame, tables: dict[str, pd.DataFrame]) -> None:
    fact = tables["FACT_Sales"]
    print("== Star schema validation ==")
    for name, frame in tables.items():
        print(f"  {name:<13} {len(frame):>7,} rows")

    # referential integrity: every fact key must resolve to a dimension row
    checks = [
        ("DateKey", tables["DIM_Date"]["DateKey"]),
        ("StoreKey", tables["DIM_Store"]["StoreKey"]),
        ("ProductKey", tables["DIM_Product"]["ProductKey"]),
        ("CustomerKey", tables["DIM_Customer"]["CustomerKey"]),
    ]
    for key, dim_values in checks:
        missing = (~fact[key].isin(set(dim_values))).sum()
        status = "OK" if missing == 0 else f"FAIL ({missing} orphan rows)"
        print(f"  FK {key:<11} {status}")

    # revenue reconciliation: raw extract vs warehouse fact
    raw_rev = raw["LineNetZAR"].sum()
    fact_rev = fact["SalesAmountZAR"].sum()
    diff = abs(raw_rev - fact_rev)
    print(f"  Revenue reconciliation : raw R {raw_rev:,.2f} vs warehouse R {fact_rev:,.2f} "
          f"(diff R {diff:.2f}) -> {'OK' if diff < 1 else 'FAIL'}")


def main() -> None:
    # Store master - same reference data as the generator script
    stores = pd.DataFrame(
        {
            "StoreID": [f"S{str(i).zfill(3)}" for i in range(1, 9)],
            "StoreName": [
                "Sandton City", "Menlyn Park", "Gateway Durban",
                "V&A Waterfront", "Eastgate", "Canal Walk",
                "Pavillion Westville", "Online Warehouse",
            ],
            "City": [
                "Johannesburg", "Pretoria", "Durban",
                "Cape Town", "Johannesburg", "Cape Town",
                "Durban", "National",
            ],
            "Province": [
                "Gauteng", "Gauteng", "KwaZulu-Natal",
                "Western Cape", "Gauteng", "Western Cape",
                "KwaZulu-Natal", "National",
            ],
            "ChannelModel": ["In-store"] * 7 + ["Online"],
        }
    )

    raw = pd.read_csv(RAW)
    tables = build_dimensions(raw, stores)

    # persist each table as CSV (inspectable without any database tool)
    for name, frame in tables.items():
        frame.to_csv(OUT_DIR / f"{name}.csv", index=False)

    load_sqlite(tables)
    validate(raw, tables)
    print(f"\nSQLite warehouse written to {DB_PATH.relative_to(REPO)}")


if __name__ == "__main__":
    main()
