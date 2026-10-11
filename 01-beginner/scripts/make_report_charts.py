r"""Create report figures that mirror the Excel dashboard.

Run from the 01-beginner folder:
    python scripts\make_report_charts.py
"""
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "figures"
OUT.mkdir(parents=True, exist_ok=True)

orders = pd.read_csv(
    ROOT / "data" / "clean" / "superstore_clean.csv",
    parse_dates=["Order Date", "Ship Date"],
)
returns = pd.read_csv(ROOT / "data" / "clean" / "returns.csv")
orders["Year"] = orders["Order Date"].dt.year
orders["Month"] = orders["Order Date"].dt.month
orders["Year-Month"] = orders["Order Date"].dt.to_period("M").astype(str)
orders["Margin"] = orders["Profit"] / orders["Sales"]

TEAL = "#0F766E"
NAVY = "#1F3864"
BLUE = "#2E75B6"
ORANGE = "#ED7D31"
RED = "#C00000"
GREEN = "#70AD47"
GREY = "#A6A6A6"
plt.rcParams.update({"font.family": "DejaVu Sans", "axes.titleweight": "bold"})


def save(name):
    plt.tight_layout()
    plt.savefig(OUT / name, dpi=180, bbox_inches="tight", facecolor="#FBFAF6")
    plt.close()


# 1. Dashboard-style overview: KPI cards plus the main sales/profit curve.
monthly = orders.groupby("Year-Month", as_index=False).agg(
    Sales=("Sales", "sum"), Profit=("Profit", "sum")
)
sales = orders["Sales"].sum()
profit = orders["Profit"].sum()
order_count = orders["Order ID"].nunique()
return_rate = returns["Order ID"].nunique() / order_count
growth = (
    orders.loc[orders["Year"] == 2018, "Sales"].sum()
    / orders.loc[orders["Year"] == 2017, "Sales"].sum()
    - 1
)
fig = plt.figure(figsize=(12, 7), facecolor="#FBFAF6")
grid = fig.add_gridspec(3, 4, height_ratios=[0.8, 0.8, 2.8])
cards = [
    ("TOTAL SALES", f"${sales:,.0f}"),
    ("TOTAL PROFIT", f"${profit:,.0f}"),
    ("PROFIT MARGIN", f"{profit / sales:.1%}"),
    ("TOTAL ORDERS", f"{order_count:,}"),
    ("AVG ORDER VALUE", f"${sales / order_count:,.2f}"),
    ("RETURN RATE", f"{return_rate:.1%}"),
    ("SALES GROWTH", f"{growth:+.1%}"),
]
for i, (label, value) in enumerate(cards):
    ax = fig.add_subplot(grid[i // 4, i % 4])
    ax.set_facecolor("#DEEAF6")
    ax.text(0.05, 0.78, label, color=BLUE, fontsize=8, weight="bold")
    ax.text(0.05, 0.25, value, color=NAVY, fontsize=17, weight="bold")
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_color("#D9D6CC")
for i in range(len(cards), 8):
    ax = fig.add_subplot(grid[i // 4, i % 4])
    ax.axis("off")
ax = fig.add_subplot(grid[2, :])
ax.plot(monthly["Year-Month"], monthly["Sales"], color=BLUE, lw=2.2, label="Sales")
ax.plot(monthly["Year-Month"], monthly["Profit"], color=ORANGE, lw=2.2, label="Profit")
ax.set_title("Monthly sales and profit")
ax.set_ylabel("USD")
ax.tick_params(axis="x", rotation=55, labelsize=7)
ax.grid(axis="y", alpha=0.2)
ax.legend(frameon=False, ncol=2)
save("dashboard_overview.png")


# 2. Monthly trend curve with a three-month sales average.
trend = monthly.copy()
trend["3-month average"] = trend["Sales"].rolling(3).mean()
fig, ax = plt.subplots(figsize=(10, 4.5))
ax.plot(trend["Year-Month"], trend["Sales"], color=BLUE, lw=1.8, label="Sales")
ax.plot(trend["Year-Month"], trend["3-month average"], color=TEAL, lw=2.2,
        label="3-month average")
ax.set_title("Monthly sales trend, 2015-2018")
ax.set_ylabel("Sales (USD)")
ax.tick_params(axis="x", rotation=55, labelsize=7)
ax.grid(axis="y", alpha=0.2)
ax.legend(frameon=False)
save("monthly_trend.png")


# 3. Category and region comparisons.
fig, axes = plt.subplots(1, 2, figsize=(10, 4.5))
for ax, group, title in [
    (axes[0], "Category", "Sales and profit by category"),
    (axes[1], "Region", "Sales and profit by region"),
]:
    summary = orders.groupby(group)[["Sales", "Profit"]].sum().sort_values("Sales")
    summary.plot.barh(ax=ax, color=[BLUE, ORANGE])
    ax.set_title(title)
    ax.set_xlabel("USD")
    ax.grid(axis="x", alpha=0.2)
    ax.legend(frameon=False)
save("category_region.png")


# 4. Sub-category performance.
sub = orders.groupby("Sub-Category").agg(
    Sales=("Sales", "sum"), Profit=("Profit", "sum")
)
sub["Margin"] = sub["Profit"] / sub["Sales"]
sub = sub.sort_values("Profit")
fig, axes = plt.subplots(1, 2, figsize=(11, 6))
axes[0].barh(sub.index, sub["Profit"], color=[RED if x < 0 else BLUE for x in sub["Profit"]])
axes[0].axvline(0, color="#444444", lw=0.8)
axes[0].set_title("Profit by sub-category")
axes[0].set_xlabel("USD")
axes[0].grid(axis="x", alpha=0.2)
axes[1].barh(sub.index, sub["Margin"], color=[RED if x < 0 else GREEN for x in sub["Margin"]])
axes[1].axvline(0, color="#444444", lw=0.8)
axes[1].set_title("Profit margin by sub-category")
axes[1].set_xlabel("Margin")
axes[1].xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:.0%}"))
axes[1].grid(axis="x", alpha=0.2)
save("subcategory_performance.png")


# 5. Top and bottom products by profit.
product = orders.groupby("Product Name").agg(
    Sales=("Sales", "sum"), Profit=("Profit", "sum")
)
top = product.nlargest(10, "Profit").sort_values("Profit")
bottom = product.nsmallest(10, "Profit").sort_values("Profit")
fig, axes = plt.subplots(1, 2, figsize=(12, 6))
axes[0].barh(top.index, top["Profit"], color=BLUE)
axes[0].set_title("Top 10 products by profit")
axes[0].set_xlabel("USD")
axes[1].barh(bottom.index, bottom["Profit"], color=RED)
axes[1].set_title("Bottom 10 products by profit")
axes[1].set_xlabel("USD")
for ax in axes:
    ax.grid(axis="x", alpha=0.2)
    ax.tick_params(axis="y", labelsize=7)
save("product_rankings.png")


# 6. Discount bands and exact-rate relationship.
bins = [-0.001, 0, 0.2, 0.4, 1]
labels = ["0%", "1-20%", "21-40%", "41%+"]
orders["Discount Band"] = pd.cut(
    orders["Discount"], bins=bins, labels=labels, include_lowest=True
)
discount = orders.groupby("Discount Band", observed=False).agg(
    Sales=("Sales", "sum"), Profit=("Profit", "sum")
)
discount["Margin"] = discount["Profit"] / discount["Sales"]
rate = orders.groupby("Discount").agg(
    Sales=("Sales", "sum"), Profit=("Profit", "sum")
)
rate["Margin"] = rate["Profit"] / rate["Sales"]
fig, axes = plt.subplots(1, 2, figsize=(10, 4.5))
axes[0].bar(discount.index, discount["Margin"], color=[GREEN, BLUE, ORANGE, RED])
axes[0].axhline(0, color="#444444", lw=0.8)
axes[0].set_title("Profit margin by discount band")
axes[0].set_ylabel("Margin")
axes[0].yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:.0%}"))
axes[0].grid(axis="y", alpha=0.2)
axes[1].plot(rate.index * 100, rate["Margin"], marker="o", color=TEAL, lw=2)
axes[1].axhline(0, color="#444444", lw=0.8)
axes[1].set_title("Margin by exact discount rate")
axes[1].set_xlabel("Discount (%)")
axes[1].set_ylabel("Margin")
axes[1].yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:.0%}"))
axes[1].grid(alpha=0.2)
save("discount_analysis.png")


# 7. Seasonality: same calendar month across years, matching Monthly Trend.
season = orders.pivot_table(index="Month", columns="Year", values="Sales", aggfunc="sum")
month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
fig, ax = plt.subplots(figsize=(10, 4.8))
for year, color in zip(sorted(season.columns), [GREY, "#9DC3E6", BLUE, NAVY]):
    ax.plot(month_names, season[year], marker="o", lw=2, color=color, label=str(year))
ax.set_title("Sales by calendar month: one curve per year")
ax.set_ylabel("Sales (USD)")
ax.grid(axis="y", alpha=0.2)
ax.legend(frameon=False, ncol=4)
save("seasonality.png")

print(f"Created {len(list(OUT.glob('*.png')))} figures in {OUT}")
