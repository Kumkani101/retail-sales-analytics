"""
03_analyse_sql.py
-----------------
Answers the six business questions defined in docs/01_business_requirements.md
using SQL against the SQLite star schema (data/processed/retail_dw.sqlite).

Each answer is printed to the console and written to
data/processed/analysis/<question>.csv so the dashboard and the solution
summary (docs/03_solution_summary.md) can reuse them.

Run after 02_build_star_schema.py.
"""

from pathlib import Path

import pandas as pd
import sqlite3

REPO = Path(__file__).resolve().parents[1]
DB_PATH = REPO / "data" / "processed" / "retail_dw.sqlite"
OUT_DIR = REPO / "data" / "processed" / "analysis"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Q1 - revenue and margin trend by month, with year-on-year comparison
SQL_Q1 = """
SELECT d.YearMonth, d.Year, d.Month,
       ROUND(SUM(f.SalesAmountZAR), 0)                AS RevenueZAR,
       ROUND(SUM(f.GrossMarginZAR), 0)                AS GrossMarginZAR,
       ROUND(100.0 * SUM(f.GrossMarginZAR) / SUM(f.SalesAmountZAR), 1) AS MarginPct
FROM FACT_Sales f
JOIN DIM_Date d ON d.DateKey = f.DateKey
WHERE f.FactType = 'Sale'
GROUP BY d.YearMonth, d.Year, d.Month
ORDER BY d.YearMonth
"""

# Q2 - category performance: revenue, margin %, return rate
SQL_Q2 = """
SELECT p.Category,
       ROUND(SUM(f.SalesAmountZAR), 0)                AS RevenueZAR,
       ROUND(100.0 * SUM(f.GrossMarginZAR) / SUM(f.SalesAmountZAR), 1) AS MarginPct,
       ROUND(100.0 * SUM(CASE WHEN f.FactType = 'Return' THEN -f.Qty ELSE 0 END)
             / SUM(CASE WHEN f.FactType = 'Sale' THEN f.Qty ELSE 0 END), 2) AS ReturnRatePct
FROM FACT_Sales f
JOIN DIM_Product p ON p.ProductKey = f.ProductKey
GROUP BY p.Category
ORDER BY RevenueZAR DESC
"""

# Q3 - store performance: revenue, margin %, online share
SQL_Q3 = """
SELECT s.StoreName, s.City, s.Province, s.ChannelModel,
       ROUND(SUM(f.SalesAmountZAR), 0)                AS RevenueZAR,
       ROUND(100.0 * SUM(f.GrossMarginZAR) / SUM(f.SalesAmountZAR), 1) AS MarginPct
FROM FACT_Sales f
JOIN DIM_Store s ON s.StoreKey = f.StoreKey
WHERE f.FactType = 'Sale'
GROUP BY s.StoreKey
ORDER BY RevenueZAR DESC
"""

# Q4 - RFM-lite customer segmentation (registered customers only; anonymous
#       walk-in purchases C00000 carry no customer identity to segment on)
SQL_Q4 = """
WITH customer_rfm AS (
    SELECT f.CustomerKey,
           MAX(d.Date)                                    AS LastPurchaseDate,
           COUNT(DISTINCT f.DocumentNo)                   AS Frequency,
           SUM(f.SalesAmountZAR)                          AS MonetaryZAR
    FROM FACT_Sales f
    JOIN DIM_Date d ON d.DateKey = f.DateKey
    WHERE f.FactType = 'Sale'
      AND f.CustomerKey <> 'C00000'
    GROUP BY f.CustomerKey
)
SELECT CustomerKey,
       LastPurchaseDate,
       Frequency,
       ROUND(MonetaryZAR, 0)                              AS MonetaryZAR,
       CASE
           WHEN Frequency >= 30 AND MonetaryZAR >= 250000 THEN 'Champion'
           WHEN Frequency >= 20                           THEN 'Loyal'
           WHEN MonetaryZAR >= 150000                     THEN 'High-value occasional'
           WHEN Frequency >= 5                            THEN 'Repeat low-value'
           ELSE 'One-time'
       END                                                AS Segment
FROM customer_rfm
"""

# Q5 - promo effectiveness: margin on promo vs non-promo lines
SQL_Q5 = """
SELECT f.PromoFlag,
       ROUND(SUM(f.SalesAmountZAR), 0)                    AS RevenueZAR,
       ROUND(100.0 * SUM(f.GrossMarginZAR) / SUM(f.SalesAmountZAR), 1) AS MarginPct
FROM FACT_Sales f
WHERE f.FactType = 'Sale'
GROUP BY f.PromoFlag
"""

# Q6 - return lines by category and by store channel
SQL_Q6 = """
SELECT p.Category,
       SUM(CASE WHEN f.FactType = 'Return' THEN -f.Qty ELSE 0 END)                    AS ReturnedUnits,
       ROUND(SUM(CASE WHEN f.FactType = 'Return' THEN -f.SalesAmountZAR ELSE 0 END), 0) AS ReturnedValueZAR
FROM FACT_Sales f
JOIN DIM_Product p ON p.ProductKey = f.ProductKey
GROUP BY p.Category
ORDER BY ReturnedValueZAR DESC
"""


def run(con: sqlite3.Connection, sql: str, name: str) -> pd.DataFrame:
    df = pd.read_sql_query(sql, con)
    df.to_csv(OUT_DIR / f"{name}.csv", index=False)
    return df


def main() -> None:
    with sqlite3.connect(DB_PATH) as con:
        q1 = run(con, SQL_Q1, "q1_monthly_trend")
        q2 = run(con, SQL_Q2, "q2_category_performance")
        q3 = run(con, SQL_Q3, "q3_store_performance")
        q4 = run(con, SQL_Q4, "q4_customer_segments")
        q5 = run(con, SQL_Q5, "q5_promo_effectiveness")
        q6 = run(con, SQL_Q6, "q6_returns")

    # ---- headline numbers for the solution summary ------------------------
    rev = q1.groupby("Year")["RevenueZAR"].sum()
    best = q1.loc[q1["RevenueZAR"].idxmax()]

    print("== Q1 monthly trend ==")
    print(f"  Revenue 2024: R {rev[2024]:,.0f} | 2025: R {rev[2025]:,.0f} | YoY: {100 * (rev[2025] / rev[2024] - 1):+.1f}%")
    print(f"  Best month : {best.YearMonth} (R {best.RevenueZAR:,.0f})")

    print("== Q2 categories (top 3 by revenue) ==")
    for _, r in q2.head(3).iterrows():
        print(f"  {r.Category:<20} R {r.RevenueZAR:>13,.0f}  margin {r.MarginPct}%  returns {r.ReturnRatePct}%")

    print("== Q3 stores (top 3) ==")
    for _, r in q3.head(3).iterrows():
        print(f"  {r.StoreName:<20} R {r.RevenueZAR:>13,.0f}  margin {r.MarginPct}%")
    online = q3.loc[q3.ChannelModel == "Online"].iloc[0]
    print(f"  Online warehouse     R {online.RevenueZAR:,.0f}  ({100 * online.RevenueZAR / q3.RevenueZAR.sum():.1f}% of revenue)")

    print("== Q4 customer segments ==")
    seg = q4["Segment"].value_counts()
    seg_rev = q4.groupby("Segment")["MonetaryZAR"].sum().sort_values(ascending=False)
    for name, n in seg.items():
        print(f"  {name:<18} {n:>5,} customers  R {seg_rev[name]:,.0f}")

    print("== Q5 promo effectiveness ==")
    for _, r in q5.iterrows():
        label = "Promo lines   " if r.PromoFlag == 1 else "Non-promo     "
        print(f"  {label} R {r.RevenueZAR:>13,.0f}  margin {r.MarginPct}%")

    print("== Q6 returns by value (top 3) ==")
    total_ret = q6.ReturnedValueZAR.sum()
    for _, r in q6.head(3).iterrows():
        print(f"  {r.Category:<20} R {r.ReturnedValueZAR:>11,.0f}  ({100 * r.ReturnedValueZAR / total_ret:.1f}% of returns)")


if __name__ == "__main__":
    main()
