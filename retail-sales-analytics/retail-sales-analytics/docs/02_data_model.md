# Data Model and Data Dictionary
## Sales Performance Analysis - Mzansi Home & Living

The raw extract is a flat billing-line export. It is reshaped into a small
**star schema** so that every business question is a simple, fast, readable
SQL query, and so the model extends naturally to more years, more stores or a
real SAP source in future.

## 1. Star schema overview

```
                DIM_Date                DIM_Store
                    \                       /
                     \                     /
        DIM_Customer ----- FACT_Sales ----- DIM_Product
```

| Table | Grain | Rows |
| --- | --- | --- |
| `FACT_Sales` | one billing document line (sales **and** credit-note style return lines) | 43,465 |
| `DIM_Date` | one calendar day (2024-01-01 to 2025-12-31) | 731 |
| `DIM_Store` | one store or the online warehouse | 8 |
| `DIM_Product` | one product (material master) | 120 |
| `DIM_Customer` | one registered customer, plus one anonymous walk-in bucket | 901 |

Conformed dimensions are shared across the fact: the same `DIM_Date` serves
any future fact (stock movements, targets), which is exactly why a star
schema is preferred over one-off report queries.

## 2. Design decisions worth explaining in an interview

1. **Returns are stored as negative-quantity fact rows** with `FactType = 'Return'`,
   mirroring how an ERP posts a credit note against a billing document. Revenue
   measures therefore filter `FactType = 'Sale'` or net the returns explicitly -
   no double-counting, no separate "returns" table to keep in sync.
2. **Measures are additive** on the fact (`SalesAmountZAR`, `CostAmountZAR`,
   `GrossMarginZAR`), so month, store, category and customer cuts all roll up
   correctly. Ratios (margin %, return rate) are always computed from additive
   numerators and denominators - never averaged as columns.
3. **Anonymous walk-in purchases** are retained in the fact under one customer
   key (`C00000`) so revenue stays complete, but customer segmentation
   (Q4) explicitly excludes them - segmenting customers we cannot identify
   would be meaningless.
4. **The load is validated, not assumed**: row counts per table, four
   referential-integrity checks (all fact keys resolve to dimension rows), and
   a revenue reconciliation between raw extract and warehouse (diff R 0.00).

## 3. Data dictionary

### FACT_Sales

| Column | Type | Description |
| --- | --- | --- |
| `DocumentNo` | INTEGER | Billing document number; one document = one purchase occasion (customer/store/day) |
| `LineItem` | INTEGER | Line number within the document |
| `DateKey` | INTEGER | FK to `DIM_Date` (YYYYMMDD) |
| `StoreKey` | TEXT | FK to `DIM_Store` (S001-S008) |
| `Channel` | TEXT | `In-store` or `Online` |
| `CustomerKey` | TEXT | FK to `DIM_Customer`; `C00000` = anonymous walk-in |
| `ProductKey` | TEXT | FK to `DIM_Product` (M1000-M1119) |
| `Category` | TEXT | Denormalised product category for convenience |
| `FactType` | TEXT | `Sale` or `Return` (return rows have negative `Qty` and amounts) |
| `Qty` | INTEGER | Units sold (negative on return lines) |
| `UnitPriceZAR` | REAL | List unit price in Rand |
| `DiscountPct` | REAL | Discount applied to the line (15% on promo lines, else 0) |
| `SalesAmountZAR` | REAL | Net line revenue after discount (negative on returns) |
| `CostAmountZAR` | REAL | Cost of goods for the line (negative on returns) |
| `GrossMarginZAR` | REAL | `SalesAmountZAR - CostAmountZAR` |
| `PromoFlag` | INTEGER | 1 if the line was sold on promotion |

### DIM_Date

| Column | Type | Description |
| --- | --- | --- |
| `DateKey` | INTEGER | YYYYMMDD (primary key) |
| `Date` | TEXT | ISO date |
| `Year`, `Quarter`, `Month`, `MonthName`, `YearMonth` | INT/TEXT | Standard calendar attributes |
| `DayName` | TEXT | Weekday name |
| `IsWeekend` | INTEGER | 1 for Saturday/Sunday |

### DIM_Store

| Column | Type | Description |
| --- | --- | --- |
| `StoreKey` | TEXT | S001-S008 (primary key) |
| `StoreName` | TEXT | Trading name |
| `City`, `Province` | TEXT | Location attributes |
| `ChannelModel` | TEXT | `In-store` or `Online` |

### DIM_Product

| Column | Type | Description |
| --- | --- | --- |
| `ProductKey` | TEXT | M1000-M1119 (primary key) |
| `Category` | TEXT | One of six merchandising categories |
| `UnitPriceZAR` | REAL | Current list price |

### DIM_Customer

| Column | Type | Description |
| --- | --- | --- |
| `CustomerKey` | TEXT | C00000 (walk-in bucket) or C00001-C00900 |
| `Province` | TEXT | Home province (registered customers) |

## 4. Reproducibility

- Raw data: `python src/01_generate_data.py` (fixed seed 42)
- Warehouse: `python src/02_build_star_schema.py` (writes `data/processed/retail_dw.sqlite` and per-table CSVs)
- The dataset is **simulated**; the schema, keys and quirks (credit-note
  returns, anonymous walk-ins, promo flags) are modelled on a real-world ERP
  extract so the pipeline ports to real data with a file-path change.
