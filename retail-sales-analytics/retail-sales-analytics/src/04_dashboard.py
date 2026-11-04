"""
04_dashboard.py
---------------
Builds two deliverables from the analysis CSVs:

1. output/sales_dashboard.html - a self-contained interactive Plotly dashboard
   (KPI header, revenue trend, category and store performance, customer
   segments, promo and returns analysis). Open it in any browser; it needs an
   internet connection because Plotly.js is loaded from a CDN.
2. output/charts/*.png - static preview images used in the README.

Run after 03_analyse_sql.py.
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import pandas as pd
import plotly.graph_objects as go
import plotly.subplots as sp

REPO = Path(__file__).resolve().parents[1]
A = REPO / "data" / "processed" / "analysis"
OUT = REPO / "output"
(OUT / "charts").mkdir(parents=True, exist_ok=True)

NAVY = "#1F3B57"
BLUE = "#2F6FBA"
TEAL = "#3A9188"
ORANGE = "#E08214"
GREY = "#8A8F98"
RED = "#C0392B"


def millions(x, _):
    return f"R{x/1e6:,.0f}m"


def load() -> dict[str, pd.DataFrame]:
    seg = pd.read_csv(A / "q4_customer_segments.csv")
    # the CSV is one row per customer; aggregate to segment level for plotting
    seg_summary = (
        seg.groupby("Segment", as_index=False)
        .agg(Customers=("CustomerKey", "count"), MonetaryZAR=("MonetaryZAR", "sum"))
    )
    return {
        "trend": pd.read_csv(A / "q1_monthly_trend.csv"),
        "cat": pd.read_csv(A / "q2_category_performance.csv"),
        "store": pd.read_csv(A / "q3_store_performance.csv"),
        "seg": seg_summary,
        "promo": pd.read_csv(A / "q5_promo_effectiveness.csv"),
        "ret": pd.read_csv(A / "q6_returns.csv"),
    }


def headline(d: dict[str, pd.DataFrame]) -> dict[str, float]:
    """KPI numbers reused by the dashboard header and the solution summary."""
    trend, cat, store, seg, promo, ret = (
        d["trend"], d["cat"], d["store"], d["seg"], d["promo"], d["ret"],
    )
    gross = trend.RevenueZAR.sum()
    returned = ret.ReturnedValueZAR.sum()
    weighted_margin = 100 * (cat.RevenueZAR * cat.MarginPct / 100).sum() / cat.RevenueZAR.sum()
    rev24 = trend.loc[trend.Year == 2024, "RevenueZAR"].sum()
    rev25 = trend.loc[trend.Year == 2025, "RevenueZAR"].sum()
    online = store.loc[store.ChannelModel == "Online", "RevenueZAR"].iloc[0]
    promo_rev = promo.loc[promo.PromoFlag == 1, "RevenueZAR"].iloc[0]
    promo_margin = promo.loc[promo.PromoFlag == 1, "MarginPct"].iloc[0]
    non_margin = promo.loc[promo.PromoFlag == 0, "MarginPct"].iloc[0]
    champ = seg.loc[seg.Segment == "Champion"]
    return {
        "gross_sales": gross,
        "net_revenue": gross - returned,
        "returned": returned,
        "yoy_pct": 100 * (rev25 / rev24 - 1),
        "margin_pct": weighted_margin,
        "online_share_pct": 100 * online / store.RevenueZAR.sum(),
        "promo_revenue_share_pct": 100 * promo_rev / gross,
        "promo_margin_pct": promo_margin,
        "non_promo_margin_pct": non_margin,
        "champion_customers": int(champ.Customers.iloc[0]),
        "champion_revenue": float(champ.MonetaryZAR.iloc[0]),
        "champion_share_pct": 100 * champ.MonetaryZAR.iloc[0] / seg.MonetaryZAR.sum(),
    }


# --------------------------------------------------------------------------
# Interactive Plotly dashboard
# --------------------------------------------------------------------------

def build_interactive(d: dict[str, pd.DataFrame], k: dict[str, float]) -> None:
    trend, cat, store, seg, promo, ret = (
        d["trend"], d["cat"], d["store"], d["seg"], d["promo"], d["ret"],
    )

    fig = sp.make_subplots(
        rows=3, cols=3,
        subplot_titles=(
            "Monthly revenue (Rm)", "Revenue by store (Rm)", "Revenue by category (Rm)",
            "Margin % vs return rate by category", "Customer segments (registered only)",
            "Promo vs non-promo (margin %)",
            "Returned value by category (Rm)", "Revenue 2024 vs 2025 (Rm)",
            "Champion share of registered revenue",
        ),
        specs=[[{}, {}, {}],
               [{}, {}, {}],
               [{}, {}, {"type": "domain"}]],
        vertical_spacing=0.16, horizontal_spacing=0.10,
    )

    # 1. monthly revenue trend -------------------------------------------
    fig.add_trace(
        go.Scatter(x=trend.YearMonth, y=trend.RevenueZAR / 1e6, mode="lines+markers",
                   line=dict(color=NAVY, width=2.5), name="Revenue",
                   hovertemplate="%{x}<br>R%{y:,.1f}m<extra></extra>", showlegend=False),
        row=1, col=1,
    )
    bf = trend.loc[trend.YearMonth.isin(["2024-11", "2025-11"])]
    fig.add_trace(
        go.Scatter(x=bf.YearMonth, y=bf.RevenueZAR / 1e6, mode="markers",
                   marker=dict(color=ORANGE, size=11, symbol="diamond"),
                   name="Black Friday", hovertemplate="Black Friday: %{x}<br>R%{y:,.1f}m<extra></extra>",
                   showlegend=False),
        row=1, col=1,
    )

    # 2. revenue by store --------------------------------------------------
    s = store.sort_values("RevenueZAR")
    fig.add_trace(
        go.Bar(y=s.StoreName, x=s.RevenueZAR / 1e6, orientation="h", marker_color=TEAL,
               hovertemplate="%{y}<br>R%{x:,.1f}m<extra></extra>", showlegend=False),
        row=1, col=2,
    )
    fig.update_yaxes(tickfont=dict(size=9), row=1, col=2)

    # 3. revenue by category ----------------------------------------------
    c = cat.sort_values("RevenueZAR", ascending=False)
    fig.add_trace(
        go.Bar(x=c.Category, y=c.RevenueZAR / 1e6, marker_color=BLUE,
               hovertemplate="%{x}<br>R%{y:,.1f}m<extra></extra>", showlegend=False),
        row=1, col=3,
    )
    fig.update_xaxes(tickangle=35, tickfont=dict(size=9), row=1, col=3)

    # 4. margin % vs return rate (scatter, one point per category) ---------
    fig.add_trace(
        go.Scatter(x=c.ReturnRatePct, y=c.MarginPct, mode="markers+text",
                   text=c.Category, textposition="top center", textfont=dict(size=9),
                   marker=dict(size=13, color=ORANGE),
                   hovertemplate="%{text}<br>margin %{y}%<br>returns %{x}%<extra></extra>",
                   showlegend=False),
        row=2, col=1,
    )
    fig.update_xaxes(title_text="Return rate %", title_font=dict(size=10), range=[0.9, 6.4], row=2, col=1)
    fig.update_yaxes(title_text="Gross margin %", title_font=dict(size=10), range=[22, 47], row=2, col=1)

    # 5. customer segments --------------------------------------------------
    sg = seg.sort_values("MonetaryZAR", ascending=False)
    fig.add_trace(
        go.Bar(x=sg.Segment, y=sg.Customers, marker_color=BLUE, name="Customers",
               customdata=sg.MonetaryZAR,
               hovertemplate="%{x}<br>%{y} customers<br>R%{customdata:,.0f} spend<extra></extra>",
               showlegend=False),
        row=2, col=2,
    )
    fig.update_xaxes(tickangle=25, tickfont=dict(size=9), row=2, col=2)

    # 6. promo vs non-promo -------------------------------------------------
    labels = ["Non-promo", "Promo"]
    margins = [promo.loc[promo.PromoFlag == 0, "MarginPct"].iloc[0],
               promo.loc[promo.PromoFlag == 1, "MarginPct"].iloc[0]]
    fig.add_trace(
        go.Bar(x=labels, y=margins, marker_color=[TEAL, RED],
               hovertemplate="%{x}: %{y}% margin<extra></extra>", showlegend=False),
        row=2, col=3,
    )

    # 7. returned value by category -----------------------------------------
    r = ret.sort_values("ReturnedValueZAR", ascending=False)
    fig.add_trace(
        go.Bar(x=r.Category, y=r.ReturnedValueZAR / 1e6, marker_color=GREY,
               hovertemplate="%{x}<br>R%{y:,.2f}m returned<extra></extra>", showlegend=False),
        row=3, col=1,
    )
    fig.update_xaxes(tickangle=35, tickfont=dict(size=9), row=3, col=1)

    # 8. 2024 vs 2025 --------------------------------------------------------
    yr = trend.groupby("Year")["RevenueZAR"].sum()
    fig.add_trace(
        go.Bar(x=[str(y) for y in yr.index], y=yr.values / 1e6, marker_color=[BLUE, NAVY],
               hovertemplate="%{x}: R%{y:,.1f}m<extra></extra>", showlegend=False),
        row=3, col=2,
    )

    # 9. champion share (donut) ----------------------------------------------
    champ = float(sg.loc[sg.Segment == "Champion", "MonetaryZAR"].iloc[0])
    rest = float(sg.MonetaryZAR.sum()) - champ
    fig.add_trace(
        go.Pie(values=[champ, rest], labels=["Champions", "Other segments"], hole=0.62,
               marker=dict(colors=[ORANGE, "#D8DDE3"]), showlegend=False,
               hovertemplate="%{label}: R%{value:,.0f}<extra></extra>",
               textinfo="none"),
        row=3, col=3,
    )
    fig.add_annotation(
        xref="paper", yref="paper", x=0.867, y=0.113, showarrow=False,
        text=f"<b>{k['champion_share_pct']:.0f}%</b><br><span style='font-size:10px'>from {k['champion_customers']} customers</span>",
        font=dict(size=13, color=NAVY),
    )

    # KPI header -----------------------------------------------------------
    kpis = [
        (f"R{k['net_revenue']/1e6:,.0f}m", "Net revenue 2024-25"),
        (f"{k['yoy_pct']:+.1f}%", "Revenue growth YoY"),
        (f"{k['margin_pct']:.1f}%", "Gross margin"),
        (f"{k['online_share_pct']:.1f}%", "Online revenue share"),
        (f"R{k['returned']/1e6:,.1f}m", "Returned value"),
    ]
    for i, (value, label) in enumerate(kpis):
        fig.add_annotation(
            xref="paper", yref="paper", x=i / 5 + 0.1, y=1.10, showarrow=False,
            text=f"<span style='font-size:22px; color:{NAVY}'><b>{value}</b></span><br>"
                 f"<span style='font-size:11px; color:{GREY}'>{label}</span>",
        )

    fig.update_layout(
        title=dict(text="<b>Mzansi Home & Living - Sales Performance 2024-2025</b><br>"
                        "<sup>Simulated ERP-style data | star schema in SQLite | SQL analysis | Plotly</sup>",
                   font=dict(size=20, color=NAVY), x=0.02, y=0.985),
        template="plotly_white",
        height=1180, width=1280,
        margin=dict(t=240, b=40, l=60, r=40),
        font=dict(family="Arial, sans-serif", size=11),
    )
    fig.write_html(
        OUT / "sales_dashboard.html",
        include_plotlyjs="cdn",
        config={"displaylogo": False},
    )
    print(f"Wrote {OUT / 'sales_dashboard.html'}")


# --------------------------------------------------------------------------
# Static matplotlib previews for the README
# --------------------------------------------------------------------------

def _style(ax):
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.spines["left"].set_color("#CCCCCC")
    ax.spines["bottom"].set_color("#CCCCCC")
    ax.tick_params(colors="#555555", labelsize=9)


def build_static(d: dict[str, pd.DataFrame], k: dict[str, float]) -> None:
    trend, cat, seg = d["trend"], d["cat"], d["seg"]

    # 1 - monthly revenue trend
    fig, ax = plt.subplots(figsize=(8.2, 3.6), dpi=150, constrained_layout=True)
    x = pd.to_datetime(trend.YearMonth + "-01")
    ax.plot(x, trend.RevenueZAR / 1e6, color=NAVY, lw=2, marker="o", ms=3)
    bf = trend[trend.YearMonth.isin(["2024-11", "2025-11"])]
    xb = pd.to_datetime(bf.YearMonth + "-01")
    ax.scatter(xb, bf.RevenueZAR / 1e6, color=ORANGE, s=55, zorder=3, marker="D")
    for xi, yi in zip(xb, bf.RevenueZAR / 1e6):
        ax.annotate("Black Friday", (xi, yi), xytext=(0, 8), textcoords="offset points",
                    ha="center", fontsize=8, color=ORANGE, fontweight="bold")
    ax.yaxis.set_major_formatter(mtick.FuncFormatter(millions))
    ax.set_ylabel("Revenue", fontsize=9)
    ax.set_title("Monthly revenue, 2024-2025 - November peaks at R14.9m (Black Friday)",
                 fontsize=11, color=NAVY, loc="left", pad=10)
    _style(ax)
    fig.savefig(OUT / "charts" / "monthly_revenue.png")
    plt.close(fig)

    # 2 - category performance
    fig, ax = plt.subplots(figsize=(8.2, 3.6), dpi=150, constrained_layout=True)
    c = cat.sort_values("RevenueZAR", ascending=True)
    bars = ax.barh(c.Category, c.RevenueZAR / 1e6, color=BLUE, height=0.62)
    ax.yaxis.set_major_formatter(mtick.FuncFormatter(lambda v, _: f"{v:,.0f}"))
    ax.xaxis.set_major_formatter(mtick.FuncFormatter(millions))
    for b, (_, row) in zip(bars, c.iterrows()):
        ax.text(b.get_width() + 1.2, b.get_y() + b.get_height() / 2,
                f"{row.MarginPct:.0f}% margin", va="center", fontsize=8.5, color="#555555")
    ax.set_xlim(0, c.RevenueZAR.max() / 1e6 * 1.22)
    ax.set_title("Revenue and gross margin by category - Lounge Furniture leads, "
                 "Outdoor Living is margin-weak", fontsize=11, color=NAVY, loc="left", pad=10)
    _style(ax)
    fig.savefig(OUT / "charts" / "category_performance.png")
    plt.close(fig)

    # 3 - customer segments
    fig, ax = plt.subplots(figsize=(8.2, 3.6), dpi=150, constrained_layout=True)
    sg = seg.sort_values("MonetaryZAR", ascending=False)
    rev_share = 100 * sg.MonetaryZAR / sg.MonetaryZAR.sum()
    bars = ax.bar(sg.Segment, rev_share, color=[ORANGE, BLUE, BLUE, BLUE, GREY], width=0.6)
    for b, share, n in zip(bars, rev_share, sg.Customers):
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.8,
                f"{share:.0f}%\n({n:,} customers)", ha="center", fontsize=8.5, color="#444444")
    ax.set_ylim(0, rev_share.max() * 1.3)
    ax.yaxis.set_major_formatter(mtick.PercentFormatter())
    ax.set_ylabel("Share of registered-customer revenue", fontsize=9)
    ax.set_title("Customer segmentation - 70 Champion customers generate "
                 f"{k['champion_share_pct']:.0f}% of registered revenue",
                 fontsize=11, color=NAVY, loc="left", pad=10)
    _style(ax)
    fig.savefig(OUT / "charts" / "customer_segments.png")
    plt.close(fig)

    print(f"Wrote static previews to {OUT / 'charts'}")


def main() -> None:
    d = load()
    k = headline(d)
    print("== Headline numbers ==")
    for name, val in k.items():
        print(f"  {name:<26} {val:,.2f}" if isinstance(val, float) else f"  {name:<26} {val:,}")
    build_interactive(d, k)
    build_static(d, k)


if __name__ == "__main__":
    main()
