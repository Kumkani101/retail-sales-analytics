# Solution Summary - Findings and Recommendations
## Sales Performance Analysis - Mzansi Home & Living (FY2024-FY2025)

All figures below are computed by `src/03_analyse_sql.py` from the validated
star schema and reproducible end to end. Dataset is simulated (see README);
the analytical method is the deliverable.

## Headline results

| KPI | Value |
| --- | --- |
| Gross sales (2 years) | R 230.9m |
| Returned value | R 8.5m (3.7% of gross) |
| **Net revenue** | **R 222.4m** |
| Revenue growth 2025 vs 2024 | **+1.7%** |
| Blended gross margin | 29.0% |
| Online share of revenue | 18.8% |

## Finding 1 - Growth has stalled: +1.7% YoY hides a two-speed business

Revenue moved from R 114.5m (2024) to R 116.4m (2025). The trading pattern is
extremely seasonal: the two November months peak at R 15.0m (2024) and
R 14.9m (2025) - roughly 50% above an average month - followed by December
(R 13.4m in 2025). Between the peaks, months run at R 8.6m-R 10.0m with no
upward drift. **The business is structurally dependent on Black Friday; there
is no visible organic growth in the base months.** The one structural bright
spot is online: the Online Warehouse is the single largest "store" at
R 43.4m, 18.8% of revenue.

**Recommendation:** build the 2026 revenue plan on base-month demand (not on
the November peak), and treat online as the primary growth engine with a
specific growth target rather than a passive fulfilment channel.

## Finding 2 - Promotions are eroding margin, not obviously buying growth

Promo lines carry a 15% discount and represent 10.2% of gross revenue, but
their margin is **18.0% vs 30.3% on non-promo lines** - a 12.3 percentage
point gap, i.e. promo lines earn roughly 40% less margin per Rand. With
overall growth flat, the revenue that promos add looks increasingly like
discounted demand that would have arrived anyway, at full price, in
November/December peaks.

**Recommendation:** before signing the 2026 promotional calendar, run a
controlled promo-effectiveness test (holdout stores or categories) to measure
incrementality. If promo lines do not lift total category demand, re-allocate
that discount budget to the highest-margin categories (Finding 4).

## Finding 3 - Returns are concentrated in big-ticket furniture

Returned value totals R 8.5m. By value: **Lounge Furniture R 3.8m (44.6% of
all returned value)**, Bedroom Furniture R 1.9m (22.8%), Outdoor Living
R 1.6m (18.8%) - 86% of returned value sits in three categories. By rate,
Outdoor Living is worst at **5.62% of units returned** (vs 1.68% for Decor &
Lighting). Bulky items are expensive to collect, restock and refurbish, so
the true cost is higher than the R 8.5m headline.

**Recommendation:** run a root-cause split on furniture returns (product
fault vs "not as expected" vs delivery damage) and fix accordingly - better
product content and dimension information online, pre-delivery quality
inspection, or protective delivery handling. A one-point reduction in the
Outdoor return rate is worth roughly R 0.5m a year at current volumes.

## Finding 4 - The margin engine (Decor & Lighting) is the smallest category

Decor & Lighting has by far the highest margin at **44.0%** but contributes
only R 13.1m (5.7% of revenue). Lounge Furniture, the largest category at
R 96.5m, earns 26.6%. Kitchen & Dining (33.8% margin, R 22.9m) is the
balanced middle. The revenue mix is therefore weighted toward the
lowest-margin categories.

**Recommendation:** grow high-margin attach rates - bundle Decor & Lighting
into furniture purchases (online checkout recommendations, in-store merchandising
near furniture displays) and shift promotional spend from furniture toward
these categories.

## Finding 5 - Revenue is concentrated in a small champion group - and 60% of customers are anonymous

Of R 93.1m spent by the 899 registered customers (40% of gross sales):

| Segment | Customers | Spend | Share of registered revenue |
| --- | ---: | ---: | ---: |
| Champion (30+ purchase documents, ≥ R 250k) | 70 | R 35.3m | 38.0% |
| Loyal (20+ documents) | 175 | R 25.9m | 27.9% |
| Repeat low-value | 516 | R 28.7m | 30.8% |
| High-value occasional | 5 | R 0.8m | 0.9% |
| One-time | 133 | R 2.3m | 2.4% |

70 customers (7.8% of registered) generate 38% of registered revenue - a
genuine key-account risk if any of them defect. Meanwhile **59.7% of gross
sales are anonymous walk-in purchases** that no CRM action can reach.

**Recommendation:** (1) assign named key-account ownership to the 70
champions with proactive service; (2) push customer registration at the till
(e-mail receipts, Wi-Fi sign-in) to convert walk-ins into known customers;
(3) target the 516 repeat low-value customers with category-crossing offers -
they already trust the brand but buy only one category.

## Risks and limitations (stated honestly)

- Data is simulated; magnitudes are illustrative, method is not.
- Promo effectiveness is inferred from margin differentials, not measured
  incrementality - that requires the controlled test recommended above.
- No cost data beyond cost of goods: overheads, delivery and returns handling
  costs are unknown, so return-cost estimates are conservative.
- Customer segmentation is RFM-lite (frequency + monetary). Adding recency
  bands and purchase recency windows would refine it.
