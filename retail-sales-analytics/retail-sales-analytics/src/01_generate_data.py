"""
01_generate_data.py
-------------------
Generates a simulated, ERP-style sales extract for a fictional South African
home-ware retailer: Mzansi Home & Living (Pty) Ltd.

IMPORTANT - DATA PROVENANCE
    Every row in this dataset is SIMULATED with a fixed random seed (42) so the
    results are fully reproducible. The structure, column names and quirks
    (credit-note style return lines, document numbers, posting dates) are
    modelled on what a sales line-item extract from a typical ERP system looks
    like. The analysis code in this repository transfers unchanged to a real
    extract - only the file path changes.

Outputs
    data/raw/sales_lines_2024_2025.csv
"""

from pathlib import Path

import numpy as np
import pandas as pd

RNG = np.random.default_rng(42)

START = pd.Timestamp("2024-01-01")
END = pd.Timestamp("2025-12-31")

# --------------------------------------------------------------------------
# Reference data: stores, products, customers
# --------------------------------------------------------------------------

STORES = pd.DataFrame(
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

# category: (avg unit price ZAR, base margin, popularity weight, return-prone factor)
CATEGORIES = {
    "Lounge Furniture":   (7950, 0.28, 0.14, 1.4),
    "Bedroom Furniture":  (5400, 0.30, 0.12, 1.5),
    "Kitchen & Dining":   (1250, 0.35, 0.20, 0.9),
    "Decor & Lighting":   (680,  0.45, 0.22, 0.7),
    "Bedding & Textiles": (540,  0.40, 0.18, 1.8),
    "Outdoor Living":     (2150, 0.25, 0.14, 2.2),
}

N_PRODUCTS = 120
N_CUSTOMERS = 900
WALKIN_NO = "C00000"       # anonymous walk-in purchases are not customer-identified
WALKIN_SHARE = 0.60        # share of lines bought by unregistered walk-ins


def build_products() -> pd.DataFrame:
    rows = []
    sku = 1000
    styles = ["Classic", "Nova", "Grande", "Slim", "Premier", "Urban"]
    for cat, (price, margin, _, _) in CATEGORIES.items():
        for _ in range(N_PRODUCTS // len(CATEGORIES) + 1):
            if len(rows) >= N_PRODUCTS:
                break
            rows.append(
                {
                    "MaterialNo": f"M{sku}",
                    "ProductName": f"{cat.split(' ')[0]} {RNG.choice(styles)} {RNG.integers(100, 999)}",
                    "Category": cat,
                    "UnitPriceZAR": float(np.round(price * RNG.uniform(0.6, 1.6), -1)),
                    "BaseMargin": margin,
                }
            )
            sku += 1
    return pd.DataFrame(rows)


def build_customers() -> pd.DataFrame:
    first = ["Thabo", "Lerato", "Sipho", "Naledi", "Bongani", "Aisha", "Pieter", "Annelie",
             "Sibusiso", "Zanele", "Johan", "Precious", "Musa", "Chantelle", "Kagiso", "Nomvula"]
    last = ["Nkosi", "Molefe", "Dlamini", "Van Wyk", "Khumalo", "Petersen", "Ndlovu",
            "Botha", "Mahlangu", "Jacobs", "Sithole", "Mahlangu", "Fourie", "Zwane"]
    provinces = ["Gauteng", "Western Cape", "KwaZulu-Natal", "Free State", "Mpumalanga", "Limpopo"]
    registered = pd.DataFrame(
        {
            "CustomerNo": [f"C{str(i).zfill(5)}" for i in range(1, N_CUSTOMERS + 1)],
            "CustomerName": [f"{RNG.choice(first)} {RNG.choice(last)}" for _ in range(N_CUSTOMERS)],
            "Province": RNG.choice(provinces, N_CUSTOMERS, p=[0.34, 0.22, 0.18, 0.08, 0.09, 0.09]),
        }
    )
    walkin = pd.DataFrame({"CustomerNo": [WALKIN_NO], "CustomerName": ["Walk-in customer (anonymous)"], "Province": ["National"]})
    return pd.concat([registered, walkin], ignore_index=True)


# --------------------------------------------------------------------------
# Seasonality and demand model
# --------------------------------------------------------------------------

MONTH_FACTOR = {1: 0.80, 2: 0.85, 3: 0.95, 4: 0.90, 5: 0.90, 6: 0.95,
                7: 0.90, 8: 0.95, 9: 1.00, 10: 1.10, 11: 1.60, 12: 1.40}
DOW_FACTOR = {0: 0.9, 1: 0.9, 2: 0.95, 3: 1.0, 4: 1.15, 5: 1.35, 6: 1.25}


def build_lines(products: pd.DataFrame, customers: pd.DataFrame) -> pd.DataFrame:
    # Each registered customer gets a purchase-intensity weight -> produces
    # realistic repeat buyers. Pareto shape 2.5 keeps the tail heavy but
    # plausible: a few loyal high-spenders, no absurd whales.
    w = RNG.pareto(2.5, N_CUSTOMERS) + 0.15
    cust_w = w / w.sum()

    dates = pd.date_range(START, END, freq="D")
    cat_names = list(CATEGORIES)
    cat_weights = np.array([CATEGORIES[c][2] for c in cat_names])
    cat_weights = cat_weights / cat_weights.sum()
    cat_return_factor = {c: CATEGORIES[c][3] for c in cat_names}
    cat_products = {c: products.index[products["Category"] == c].to_numpy() for c in cat_names}

    physical = STORES[STORES.StoreID != "S008"]
    doc_no = 10_000_000
    doc_lines: dict = {}          # (customer, store) -> [doc_no, next_line_no]
    rows: list[dict] = []

    for day in dates:
        day_factor = MONTH_FACTOR[day.month] * DOW_FACTOR[day.dayofweek]
        online_share = 0.16 + 0.002 * (day - START).days / 30  # online share grows over time

        for _, store in physical.iterrows():
            for _ in range(RNG.poisson(7.5 * day_factor)):
                # online orders route to the Online Warehouse store
                if RNG.random() < online_share:
                    store_id, channel = "S008", "Online"
                else:
                    store_id, channel = store.StoreID, "In-store"

                cat = RNG.choice(cat_names, p=cat_weights)
                prod = products.loc[RNG.choice(cat_products[cat])]
                if RNG.random() < WALKIN_SHARE:
                    cust = customers.iloc[-1]          # anonymous walk-in row
                else:
                    cust_idx = int(RNG.choice(len(customers) - 1, p=cust_w))
                    cust = customers.iloc[cust_idx]

                qty = int(RNG.choice([1, 2, 3, 4], p=[0.42, 0.30, 0.18, 0.10]))
                promo = RNG.random() < 0.12
                discount = 0.15 if promo else 0.0

                unit_price = float(prod.UnitPriceZAR)
                gross = unit_price * qty
                net = gross * (1 - discount)
                cost = gross * (1 - prod.BaseMargin) * RNG.uniform(0.97, 1.03)

                # one sales document per customer / store / day (an ERP would
                # create a new order document for each purchase occasion)
                key = (cust.CustomerNo, store_id, day)
                if key not in doc_lines:
                    doc_no += 1
                    doc_lines[key] = [doc_no, 1]
                doc_ref = doc_lines[key]
                line_no = doc_ref[1]
                doc_ref[1] += 1

                rows.append(
                    {
                        "DocumentNo": doc_ref[0],
                        "LineItem": line_no,
                        "PostingDate": day.date().isoformat(),
                        "StoreID": store_id,
                        "Channel": channel,
                        "CustomerNo": cust.CustomerNo,
                        "MaterialNo": prod.MaterialNo,
                        "Category": cat,
                        "Qty": qty,
                        "UnitPriceZAR": round(unit_price, 2),
                        "DiscountPct": round(discount * 100, 1),
                        "LineNetZAR": round(net, 2),
                        "LineCostZAR": round(cost, 2),
                        "PromoFlag": int(promo),
                    }
                )

    df = pd.DataFrame(rows)

    # Credit-note style return lines: pick a small share of lines and flip them,
    # the way an ERP posts a return as a negative-quantity billing document.
    ret_p = df["Category"].map(cat_return_factor).fillna(1.0).to_numpy()
    ret_p = ret_p / ret_p.sum()
    ret_idx = RNG.choice(df.index, size=int(len(df) * 0.035), p=ret_p, replace=False)

    returns = df.loc[ret_idx].copy()
    returns["DocumentNo"] = np.arange(20_000_000, 20_000_000 + len(returns))
    returns["LineItem"] = 1
    returns["Qty"] = -returns["Qty"]
    returns["LineNetZAR"] = -returns["LineNetZAR"]
    returns["LineCostZAR"] = -returns["LineCostZAR"]
    df = pd.concat([df, returns], ignore_index=True)

    df = df.sort_values(["PostingDate", "DocumentNo", "LineItem"]).reset_index(drop=True)
    return df


def main() -> None:
    raw_dir = Path(__file__).resolve().parents[1] / "data" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    products = build_products()
    customers = build_customers()
    df = build_lines(products, customers)

    out = raw_dir / "sales_lines_2024_2025.csv"
    df.to_csv(out, index=False)

    print(f"Wrote {len(df):,} sales/return lines to {out}")
    print(f"Date range        : {df.PostingDate.min()} to {df.PostingDate.max()}")
    print(f"Gross net revenue : R {df.LineNetZAR.sum():,.0f}")
    print(f"Return lines      : {(df.Qty < 0).sum():,} ({(df.Qty < 0).mean():.1%})")
    print(f"Online share      : {(df.Channel == 'Online').mean():.1%} of lines")


if __name__ == "__main__":
    main()
