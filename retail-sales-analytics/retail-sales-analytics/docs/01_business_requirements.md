# Business Requirements Document
## Sales Performance Analysis - Mzansi Home & Living (Pty) Ltd

> **Note on data:** Mzansi Home & Living is a fictional company. The dataset in
> `data/raw/` is simulated with a fixed seed and structured the way a sales
> line-item extract from a typical ERP system is structured. The methods in
> this repository are the deliverable - they transfer unchanged to a real
> extract. See `README.md` for details.

---

## 1. Background

Mzansi Home & Living (Pty) Ltd is a mid-size South African home-ware retailer
operating seven physical stores across Gauteng, the Western Cape and
KwaZulu-Natal, plus a national online channel. Management has noticed that
revenue growth has stalled even though trading conditions are described as
"good", and the CFO has asked whether margin is being lost somewhere inside
the business.

The company has two years of billing-document data (FY2024-FY2025). Until now
it has only been reported as static monthly totals; nobody has analysed it at
line level.

## 2. Stakeholders

| Stakeholder | Role in this analysis |
| --- | --- |
| CFO (sponsor) | Needs an explanation of the growth stall and a margin-risk view |
| Head of Retail | Will act on store- and category-level recommendations |
| Head of Marketing | Owns the promotional calendar; needs promo effectiveness evidence |
| Sales Operations | Supplies the extracts; will consume the validated data model |

## 3. Objectives and business questions

**Objective:** explain the revenue growth stall and identify where margin is
being lost, at a level of detail that supports concrete actions for 2026
planning.

| # | Business question | Decision it supports |
| --- | --- | --- |
| Q1 | How does revenue and margin trend by month, and how does 2025 compare with 2024? | 2026 revenue plan; seasonality of staffing and stock |
| Q2 | Which product categories drive revenue, and at what margin and return cost? | Assortment and pricing priorities |
| Q3 | How do the seven stores and the online channel compare? | Space allocation, channel investment |
| Q4 | Which customer segments exist among registered customers, and where is the revenue concentrated? | Loyalty and CRM priorities |
| Q5 | Are promotional lines protecting or eroding margin? | 2026 promotional calendar |
| Q6 | Which categories generate the most returned value? | Quality and delivery-process fixes |

## 4. Scope

**In scope**
- Two financial years of sales billing lines (2024-01-01 to 2025-12-31), including credit-note style return lines
- Analysis at line, document, day, store, product, category and customer level
- A validated star-schema data model in SQLite as the reporting basis

**Out of scope**
- Purchasing/supplier data, stock levels, staffing and payroll
- Marketing campaign data (promo lines are flagged in the extract, but campaign-level attribution is not possible from billing data alone)
- Profit & loss below gross margin (overheads are not in the extract)

## 5. Success criteria

1. Every business question Q1-Q6 is answered from the data model with SQL that a reviewer can rerun end to end.
2. The warehouse reconciles to the raw extract to the cent (revenue reconciliation check in `02_build_star_schema.py`).
3. Findings are quantified in Rand and percentages - no unsupported claims.
4. Each finding is paired with at least one actionable recommendation for the 2026 planning cycle.

## 6. Deliverables

| Deliverable | Location |
| --- | --- |
| Simulated ERP-style raw extract | `data/raw/sales_lines_2024_2025.csv` |
| Star schema + validation | `src/02_build_star_schema.py`, `data/processed/retail_dw.sqlite` |
| SQL answers to Q1-Q6 | `src/03_analyse_sql.py`, `data/processed/analysis/*.csv` |
| Interactive dashboard | `output/sales_dashboard.html` |
| Findings and recommendations | `docs/03_solution_summary.md` |
