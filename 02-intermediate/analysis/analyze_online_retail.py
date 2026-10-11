"""
Customer, revenue and product analysis for the Online Retail dataset.

Reads  data/clean/*.csv   (made by scripts/clean_online_retail.py)
Writes analysis/metrics.json
       analysis/analysis_tables.xlsx      every table behind every chart
       report/charts/*.png                charts used in the report

Run from the 02-intermediate folder:  python analysis/analyze_online_retail.py
"""
import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

ROOT = Path(__file__).resolve().parents[1]
CH = ROOT / "report" / "charts"
CH.mkdir(parents=True, exist_ok=True)

NAVY, BLUE, ORANGE, GREEN, GREY, RED = "#1F3864", "#2E75B6", "#ED7D31", "#548235", "#A6A6A6", "#C00000"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.titleweight": "bold", "axes.titlesize": 12,
                     "figure.dpi": 150, "savefig.bbox": "tight"})
gbp = FuncFormatter(lambda x, _: f"£{x/1e6:.1f}M" if abs(x) >= 1e6 else f"£{x/1e3:.0f}K")
pct = FuncFormatter(lambda x, _: f"{x:.0%}")

a = pd.read_csv(ROOT / "data/clean/sales_all.csv", parse_dates=["InvoiceDate"], dtype={"CustomerID": str})
c = a[a["CustomerID"].notna()].copy()
canc = pd.read_csv(ROOT / "data/clean/cancellations.csv", dtype={"CustomerID": str})
tables, M = {}, {}

# ----------------------------------------------------------------- headline
M["revenue"] = a["Revenue"].sum()
M["invoices"] = int(a["InvoiceNo"].nunique())
M["customers"] = int(c["CustomerID"].nunique())
M["products"] = int(a["StockCode"].nunique())
M["countries"] = int(a["Country"].nunique())
M["aov"] = a.groupby("InvoiceNo")["Revenue"].sum().mean()
M["aov_median"] = a.groupby("InvoiceNo")["Revenue"].sum().median()
M["identified_rev_share"] = c["Revenue"].sum() / M["revenue"]
M["cancel_value"] = -canc["Revenue"].sum()
M["cancel_rate"] = M["cancel_value"] / M["revenue"]
M["date_min"], M["date_max"] = str(a["InvoiceDate"].min().date()), str(a["InvoiceDate"].max().date())

# ------------------------------------------------------------ monthly trend
mon = a.groupby("InvoiceMonth").agg(Revenue=("Revenue", "sum"), Orders=("InvoiceNo", "nunique"),
                                    Customers=("CustomerID", "nunique")).reset_index()
mon["AOV"] = mon["Revenue"] / mon["Orders"]
tables["Monthly"] = mon
full = mon[mon["InvoiceMonth"] != "2011-12"]
M["q4_share"] = full[full["InvoiceMonth"].isin(["2011-09", "2011-10", "2011-11"])]["Revenue"].sum() / full["Revenue"].sum()
M["nov_rev"] = float(mon.loc[mon["InvoiceMonth"] == "2011-11", "Revenue"].iloc[0])
M["feb_rev"] = float(mon.loc[mon["InvoiceMonth"] == "2011-02", "Revenue"].iloc[0])
M["nov_vs_avg_jan_aug"] = M["nov_rev"] / mon[mon["InvoiceMonth"].between("2011-01", "2011-08")]["Revenue"].mean()

fig, ax = plt.subplots(figsize=(9, 4))
cols = [GREY if m == "2011-12" else BLUE for m in mon["InvoiceMonth"]]
ax.bar(mon["InvoiceMonth"], mon["Revenue"], color=cols)
ax.yaxis.set_major_formatter(gbp)
ax.set_title("Monthly revenue (Dec 2011 is a partial month, to 9 Dec)")
plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
ax2 = ax.twinx()
ax2.plot(mon["InvoiceMonth"], mon["Customers"], color=ORANGE, marker="o", lw=2)
ax2.set_ylabel("Active customers (line)", color=ORANGE)
ax2.spines["right"].set_visible(True)
fig.savefig(CH / "01_monthly_revenue.png")
plt.close(fig)

# -------------------------------------------------------------- day / hour
a["Weekday"] = a["InvoiceDate"].dt.day_name()
a["Hour"] = a["InvoiceDate"].dt.hour
order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Sunday"]
dow = a.groupby("Weekday")["Revenue"].sum().reindex(order)
hr = a.groupby("Hour")["Revenue"].sum()
tables["Weekday"] = dow.reset_index()
tables["Hour"] = hr.reset_index()
M["no_saturday"] = bool("Saturday" not in set(a["Weekday"]))
M["peak_hours_share"] = hr.loc[10:15].sum() / hr.sum()
M["sunday_share"] = dow["Sunday"] / dow.sum()
fig, axs = plt.subplots(1, 2, figsize=(10, 3.6))
axs[0].bar(dow.index, dow.values, color=BLUE)
axs[0].yaxis.set_major_formatter(gbp)
axs[0].set_title("Revenue by weekday")
plt.setp(axs[0].get_xticklabels(), rotation=30, ha="right")
axs[1].bar(hr.index, hr.values, color=BLUE)
axs[1].yaxis.set_major_formatter(gbp)
axs[1].set_title("Revenue by hour of day")
axs[1].set_xlabel("Hour")
fig.savefig(CH / "02_weekday_hour.png")
plt.close(fig)

# ------------------------------------------------------------------ country
ctry = a.groupby("Country").agg(Revenue=("Revenue", "sum"), Customers=("CustomerID", "nunique")).sort_values("Revenue", ascending=False)
ctry["Share"] = ctry["Revenue"] / ctry["Revenue"].sum()
tables["Country"] = ctry.reset_index()
M["uk_share"] = float(ctry.loc["United Kingdom", "Share"])
nonuk = ctry.drop("United Kingdom").head(8)
M["top_export"] = [(i, float(r)) for i, r in nonuk["Revenue"].items()][:5]
M["export_rev_share"] = 1 - M["uk_share"]
fig, ax = plt.subplots(figsize=(8, 3.8))
ax.barh(nonuk.index[::-1], nonuk["Revenue"][::-1], color=BLUE)
ax.xaxis.set_major_formatter(gbp)
ax.set_title("Top 8 export markets by revenue (UK excluded)")
fig.savefig(CH / "03_countries.png")
plt.close(fig)

# --------------------------------------------------------- customer behaviour
inv = c.groupby(["CustomerID", "InvoiceNo"]).agg(Date=("InvoiceDate", "min"), Revenue=("Revenue", "sum")).reset_index()
oc = inv.groupby("CustomerID").size()
cust = c.groupby("CustomerID").agg(Revenue=("Revenue", "sum"), Orders=("InvoiceNo", "nunique"),
                                   First=("InvoiceDate", "min"), Last=("InvoiceDate", "max"),
                                   Country=("Country", "first")).sort_values("Revenue", ascending=False)
n = len(cust)
M["repeat_share"] = float((oc > 1).mean())
M["orders_per_customer_mean"] = float(oc.mean())
M["orders_per_customer_median"] = float(oc.median())
M["repeat_rev_share"] = float(cust.loc[oc[oc > 1].index, "Revenue"].sum() / cust["Revenue"].sum())
for k, f in [("top1", .01), ("top10", .10), ("top20", .20)]:
    M[f"{k}_rev_share"] = float(cust["Revenue"].head(int(n * f)).sum() / cust["Revenue"].sum())
M["bottom50_rev_share"] = float(cust["Revenue"].tail(n // 2).sum() / cust["Revenue"].sum())

dist = oc.clip(upper=10).value_counts().sort_index()
tables["Orders per customer"] = dist.rename("Customers").reset_index().rename(columns={"index": "Orders (10 = 10+)", "CustomerID": "Orders (10 = 10+)"})

cum = cust["Revenue"].cumsum() / cust["Revenue"].sum()
x = np.arange(1, n + 1) / n
fig, ax = plt.subplots(figsize=(6.5, 4.2))
ax.plot(x, cum.values, color=NAVY, lw=2.5)
ax.plot([0, 1], [0, 1], color=GREY, ls="--")
for f in (0.1, 0.2):
    v = cum.iloc[int(n * f) - 1]
    ax.scatter([f], [v], color=ORANGE, zorder=5)
    ax.annotate(f"Top {f:.0%} of customers\n= {v:.0%} of revenue", (f, v), xytext=(f + .08, v - .14), fontsize=9,
                arrowprops=dict(arrowstyle="-", color=GREY))
ax.xaxis.set_major_formatter(pct)
ax.yaxis.set_major_formatter(pct)
ax.set_xlabel("Share of customers (biggest first)")
ax.set_ylabel("Cumulative share of revenue")
ax.set_title("Revenue concentration")
fig.savefig(CH / "04_concentration.png")
plt.close(fig)

fig, ax = plt.subplots(figsize=(6.5, 3.8))
ax.bar(dist.index.astype(str), dist.values, color=BLUE)
ax.set_xticks(range(len(dist)))
ax.set_xticklabels([str(i) if i < 10 else "10+" for i in dist.index])
ax.set_xlabel("Number of orders placed by a customer")
ax.set_ylabel("Customers")
ax.set_title("How many times do customers order?")
fig.savefig(CH / "05_orders_per_customer.png")
plt.close(fig)

# --------------------------------------------------------- cohort retention
inv["Month"] = inv["Date"].dt.to_period("M")
first = inv.groupby("CustomerID")["Month"].min()
inv["Cohort"] = inv["CustomerID"].map(first)
inv["Idx"] = (inv["Month"] - inv["Cohort"]).apply(lambda v: v.n)
co = inv.groupby(["Cohort", "Idx"])["CustomerID"].nunique().unstack()
ret = co.div(co[0], axis=0)
# December 2011 is a partial month (to 9 Dec): blank those cells so they do not look like churn
for coh in ret.index:
    for k in ret.columns:
        if str(coh + int(k)) == "2011-12" and k > 0:
            ret.loc[coh, k] = np.nan
ret.index = ret.index.astype(str)
ret_out = ret.copy()
ret_out.insert(0, "Cohort size", co[0].astype(int).values)
tables["Cohort retention"] = ret_out.reset_index()
# averages exclude the Dec 2010 cohort (existing customers at the start of the data) and incomplete months
valid = ret.drop(index="2010-12")
M["ret_m1"] = float(valid[1].mean())
M["ret_m3"] = float(valid[3].mean())
M["ret_m6"] = float(valid[6].mean())
M["dec10_cohort_m1"] = float(ret.loc["2010-12", 1])
fig, ax = plt.subplots(figsize=(9, 5))
data = ret.iloc[:, :10].values
im = ax.imshow(data, cmap="Blues", vmin=0, vmax=0.5, aspect="auto")
ax.set_xticks(range(data.shape[1]))
ax.set_xticklabels([f"M{i}" for i in range(data.shape[1])])
ax.set_yticks(range(len(ret)))
ax.set_yticklabels(ret.index)
for i in range(data.shape[0]):
    for j in range(data.shape[1]):
        if not np.isnan(data[i, j]):
            ax.text(j, i, f"{data[i, j]:.0%}", ha="center", va="center", fontsize=7.5,
                    color="white" if data[i, j] > 0.3 else "black")
ax.set_title("Cohort retention: share of each month's new customers who order again\n(blank = no data; Dec 2011 partial month excluded)")
ax.set_xlabel("Months since first order")
for s in ax.spines.values():
    s.set_visible(False)
fig.savefig(CH / "06_cohort_retention.png")
plt.close(fig)

# new vs returning revenue
inv["Type"] = np.where(inv["Month"] == inv["Cohort"], "New", "Returning")
nr = inv.groupby([inv["Month"].astype(str), "Type"])["Revenue"].sum().unstack().fillna(0)
tables["New vs returning"] = nr.reset_index()
ex = nr.drop(index=["2010-12", "2011-12"])
M["returning_rev_share_2011"] = float(ex["Returning"].sum() / ex.sum().sum())
fig, ax = plt.subplots(figsize=(9, 3.8))
nr.plot(kind="bar", stacked=True, color=[ORANGE, BLUE], ax=ax, width=0.8)
ax.yaxis.set_major_formatter(gbp)
ax.set_title("Revenue from new vs returning customers (identified customers only)")
ax.set_xlabel("")
plt.setp(ax.get_xticklabels(), rotation=45, ha="right")
ax.legend(frameon=False)
fig.savefig(CH / "07_new_vs_returning.png")
plt.close(fig)

# ---------------------------------------------------------------------- RFM
snap = a["InvoiceDate"].max() + pd.Timedelta(days=1)
r = cust.copy()
r["Recency"] = (snap - r["Last"]).dt.days
r["Frequency"] = r["Orders"]
r["Monetary"] = r["Revenue"]
r["R"] = pd.qcut(r["Recency"], 5, labels=[5, 4, 3, 2, 1]).astype(int)
r["F"] = pd.qcut(r["Frequency"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]).astype(int)
r["M"] = pd.qcut(r["Monetary"], 5, labels=[1, 2, 3, 4, 5]).astype(int)


def segment(x):
    if x.R >= 4 and x.F >= 4 and x.M >= 4:
        return "Champions"
    if x.R >= 3 and x.F >= 3:
        return "Loyal"
    if x.R >= 4 and x.F <= 2:
        return "New / Promising"
    if x.R <= 2 and x.F >= 3:
        return "At Risk"
    if x.R <= 2 and x.F <= 2:
        return "Lost / Hibernating"
    return "Needs Attention"


r["Segment"] = r.apply(segment, axis=1)
seg = r.groupby("Segment").agg(Customers=("Revenue", "size"), Revenue=("Revenue", "sum"),
                               AvgRecencyDays=("Recency", "mean"), AvgOrders=("Frequency", "mean"),
                               AvgRevenue=("Revenue", "mean"))
seg["CustomerShare"] = seg["Customers"] / seg["Customers"].sum()
seg["RevenueShare"] = seg["Revenue"] / seg["Revenue"].sum()
seg = seg.sort_values("Revenue", ascending=False)
tables["RFM segments"] = seg.reset_index()
tables["Customer RFM"] = r[["Country", "Recency", "Frequency", "Monetary", "R", "F", "M", "Segment"]].reset_index()
M["rfm"] = {k: {"customers": int(v.Customers), "rev_share": float(v.RevenueShare), "cust_share": float(v.CustomerShare),
                "avg_recency": float(v.AvgRecencyDays), "avg_orders": float(v.AvgOrders), "avg_rev": float(v.AvgRevenue),
                "revenue": float(v.Revenue)} for k, v in seg.iterrows()}
colmap = {"Champions": NAVY, "Loyal": BLUE, "At Risk": ORANGE, "Lost / Hibernating": GREY,
          "Needs Attention": "#BDD7EE", "New / Promising": GREEN}
fig, axs = plt.subplots(1, 2, figsize=(10, 3.8), sharey=True)
s2 = seg.sort_values("Revenue")
axs[0].barh(s2.index, s2["CustomerShare"], color=[colmap[i] for i in s2.index])
axs[0].xaxis.set_major_formatter(pct)
axs[0].set_title("Share of customers")
axs[1].barh(s2.index, s2["RevenueShare"], color=[colmap[i] for i in s2.index])
axs[1].xaxis.set_major_formatter(pct)
axs[1].set_title("Share of revenue")
fig.savefig(CH / "08_rfm_segments.png")
plt.close(fig)

# at-risk value: customers who were valuable but are quiet
risk = r[(r["Segment"] == "At Risk")]
M["at_risk_revenue_historic"] = float(risk["Revenue"].sum())
M["at_risk_customers"] = int(len(risk))
champ_lost = r[(r["M"] >= 4) & (r["Recency"] > 90)]
M["valuable_quiet_customers"] = int(len(champ_lost))
M["valuable_quiet_revenue"] = float(champ_lost["Revenue"].sum())

# ------------------------------------------------------------------ products
prod = a.groupby(["StockCode", "Description"]).agg(Revenue=("Revenue", "sum"), Units=("Quantity", "sum"),
                                                   Orders=("InvoiceNo", "nunique"),
                                                   Customers=("CustomerID", "nunique")).reset_index().sort_values("Revenue", ascending=False)
prod["Share"] = prod["Revenue"] / prod["Revenue"].sum()
tables["Products"] = prod
M["top10_products_share"] = float(prod["Revenue"].head(10).sum() / prod["Revenue"].sum())
M["top10pct_products_share"] = float(prod["Revenue"].head(int(len(prod) * .1)).sum() / prod["Revenue"].sum())
M["top_products"] = [(d, float(v)) for d, v in zip(prod["Description"].head(5), prod["Revenue"].head(5))]
fig, ax = plt.subplots(figsize=(9, 4.4))
t = prod.head(10).iloc[::-1]
ax.barh([d.title()[:38] for d in t["Description"]], t["Revenue"], color=BLUE)
ax.xaxis.set_major_formatter(gbp)
ax.set_title("Top 10 products by revenue")
fig.savefig(CH / "09_top_products.png")
plt.close(fig)

# seasonality of products: Christmas-related items
xm = a["Description"].str.contains("CHRISTMAS|XMAS|ADVENT|SANTA|SNOWMAN|REINDEER|STOCKING", regex=True)
xm_m = a[xm].groupby("InvoiceMonth")["Revenue"].sum()
M["xmas_share_of_revenue"] = float(a[xm]["Revenue"].sum() / M["revenue"])
M["xmas_sep_nov_share"] = float(xm_m.reindex(["2011-09", "2011-10", "2011-11"]).sum() / xm_m[xm_m.index < "2011-12"].sum())
tables["Christmas items by month"] = xm_m.reset_index()

# --------------------------------------------------------------- cancellations
canc["Month"] = pd.to_datetime(canc["InvoiceDate"]).dt.to_period("M").astype(str)
cm = (-canc.groupby("Month")["Revenue"].sum()).rename("Cancelled")
cmr = pd.concat([mon.set_index("InvoiceMonth")["Revenue"], cm], axis=1).fillna(0)
cmr["Rate"] = cmr["Cancelled"] / cmr["Revenue"]
tables["Cancellations by month"] = cmr.reset_index()
cp = canc.groupby("Description")["Revenue"].sum().sort_values().head(8)
M["cancel_top"] = [(d, float(-v)) for d, v in cp.items()][:5]
M["cancel_by_cust_top10_share"] = float(
    -canc[canc["CustomerID"].notna()].groupby("CustomerID")["Revenue"].sum().sort_values().head(10).sum() / M["cancel_value"])
M["cancel_rate_peak_month"] = [str(cmr["Rate"].idxmax()), float(cmr["Rate"].max())]

# AOV by segment (basket size) and by country type
aov_new = inv[inv["Type"] == "New"]["Revenue"].mean()
aov_ret = inv[inv["Type"] == "Returning"]["Revenue"].mean()
M["aov_new"], M["aov_returning"] = float(aov_new), float(aov_ret)

# ------------------------------------------------------------------- output
def clean(o):
    if isinstance(o, dict):
        return {k: clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [clean(v) for v in o]
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, (np.integer,)):
        return int(o)
    return o


(ROOT / "analysis" / "metrics.json").write_text(json.dumps(clean(M), indent=2))
with pd.ExcelWriter(ROOT / "analysis" / "analysis_tables.xlsx", engine="openpyxl") as xw:
    for name, t in tables.items():
        t.to_excel(xw, sheet_name=name[:31], index=False)
        ws = xw.sheets[name[:31]]
        for col in ws.columns:
            ws.column_dimensions[col[0].column_letter].width = min(40, max(10, max(len(str(x.value or "")) for x in col[:50]) + 2))
        ws.freeze_panes = "A2"
print(json.dumps(clean(M), indent=1)[:4500])
