# Retail Sales Analytics - SQL + Star Schema + Interactive Dashboard

End-to-end sales performance analysis for a fictional South African home-ware
retailer (**Mzansi Home & Living**, simulated data): a raw ERP-style extract is
modelled into a validated **star schema** in SQLite, six business questions are
answered in **SQL**, and the results are published as an **interactive Plotly
dashboard** and a consulting-style solution summary.

![Monthly revenue](output/charts/monthly_revenue.png)

## Why this project exists

Retail businesses rarely lack data - they lack **answers they can act on**. The
brief: *"revenue growth has stalled; find out where margin is being lost."*
This project walks the full path a data analyst / SAP analytics consultant
would walk: understand the question → shape the data → answer with evidence →
recommend.

## What's inside

| Piece | Description |
| --- | --- |
| `src/01_generate_data.py` | Generates a simulated ERP-style sales extract (43,465 billing lines, 2024-2025, fixed seed for reproducibility) |
| `src/02_build_star_schema.py` | Builds DIM_Date / DIM_Store / DIM_Product / DIM_Customer + FACT_Sales, loads SQLite, runs validation (FK checks + revenue reconciliation to the cent) |
| `src/03_analyse_sql.py` | Six business questions answered in SQL; results saved as CSV |
| `src/04_dashboard.py` | Builds the interactive dashboard and static previews |
| `output/sales_dashboard.html` | **Open in your browser** - KPI header + 9 linked views |
| `docs/01_business_requirements.md` | Consulting-style requirements document (stakeholders, questions, scope, success criteria) |
| `docs/02_data_model.md` | Star schema design decisions + full data dictionary |
| `docs/03_solution_summary.md` | Findings and recommendations, quantified in Rand |

![Category performance](output/charts/category_performance.png)

## Headline findings

- **Growth is flat: +1.7% YoY** (R 114.5m → R 116.4m gross). The business is
  structurally dependent on Black Friday (November ≈ 50% above an average
  month); base months show no organic growth.
- **Promotions erode margin**: promo lines (10.2% of revenue) earn **18.0%**
  margin vs **30.3%** on non-promo lines - and growth is flat, so the
  incremental value is questionable.
- **Returns are concentrated in furniture**: Lounge + Bedroom + Outdoor =
  86% of the R 8.5m returned value; Outdoor Living has the worst return rate
  (5.6% of units).
- **Margin engine is underweight**: Decor & Lighting earns 44.0% margin but is
  only 5.7% of revenue.
- **Customer concentration**: 70 Champion customers = 38% of registered
  revenue; 60% of sales are anonymous walk-ins that no CRM action can reach.

Full evidence chain in `docs/03_solution_summary.md`.

![Customer segments](output/charts/customer_segments.png)

## How to run

```bash
pip install -r requirements.txt
python src/01_generate_data.py      # ~1 min, fixed seed -> data/raw/
python src/02_build_star_schema.py  # builds + validates SQLite warehouse
python src/03_analyse_sql.py        # answers Q1-Q6, writes analysis CSVs
python src/04_dashboard.py          # writes output/sales_dashboard.html + charts
```

Then open `output/sales_dashboard.html` in a browser (internet needed for the
Plotly.js CDN). Every number in the docs and dashboard is regenerated from
scratch by these four commands.

## Skills demonstrated

- **Data modelling**: star schema, conformed dimensions, additive measures,
  credit-note style returns, fact/dimension grain decisions
- **SQL**: CTEs, conditional aggregation, RFM segmentation, data validation
  and reconciliation queries (SQLite; the SQL is standard and portable)
- **Analysis**: seasonality, margin-mix and promo-effectiveness analysis,
  return-rate economics, RFM customer segmentation
- **Communication**: requirements doc → data dictionary → quantified
  findings → recommendations, i.e. the deliverable chain of a consulting
  engagement
- **Visualisation**: interactive Plotly dashboard with KPI header, plus
  publication-style static charts

## Honest scope notes

- The dataset is **simulated** (fixed seed, clearly labelled in the repo). The
  schema mirrors a real ERP sales extract (billing documents, credit-note
  returns, promo flags, anonymous walk-ins) so the pipeline ports to real data
  with a path change.
- Promo "effectiveness" is inferred from margin differentials; measuring true
  incrementality needs a controlled test - which is exactly what the solution
  summary recommends.

## How to talk about this project in interviews

- **"Walk me through it"**: raw flat extract → star schema for stable, extensible
  reporting → SQL for evidence → dashboard for communication. Emphasise that
  the schema exists because one-off queries don't scale to new questions.
- **Design decision you can defend**: returns as negative-quantity fact rows
  (`FactType`) - keeps revenue measures honest and mirrors how ERPs post
  credit notes; separate "returns" tables drift out of sync.
- **Data quality instinct**: you validate loads, not assume them - the build
  script prints FK checks and a raw-vs-warehouse reconciliation (diff R 0.00).
- **Business sense**: the best finding is not the most technical one - promo
  lines earning 40% less margin during flat growth is a board-level question,
  and the honest answer ("this needs an incrementality test") shows judgment.
