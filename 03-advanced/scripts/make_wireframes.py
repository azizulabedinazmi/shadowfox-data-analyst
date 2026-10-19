"""
Draw the three planned dashboard pages as images, using the real numbers.
These are wireframes (a target to build in Power BI), not the dashboard itself.

Run from the 03-advanced folder:  python scripts/make_wireframes.py
Output: dashboard/wireframe_1_summary.png, _2_drivers.png, _3_watchlist.png
"""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.ticker import FuncFormatter

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "dashboard"
OUT.mkdir(exist_ok=True)
d = pd.read_csv(ROOT / "data/clean/hr_employees.csv")

NAVY, BLUE, RED, GREEN, GREY, LIGHT = "#1F3864", "#2E75B6", "#C00000", "#548235", "#A6A6A6", "#DEEAF6"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.spines.top": False,
                     "axes.spines.right": False, "axes.titleweight": "bold", "axes.titlesize": 10,
                     "axes.titlecolor": NAVY})
pct = FuncFormatter(lambda x, _: f"{x:.0%}")
BASE = d["Left"].mean()


def colour(r):
    return RED if r >= BASE + 0.05 else GREEN if r <= BASE - 0.05 else BLUE


def page(title, subtitle, slicers):
    fig = plt.figure(figsize=(13.33, 7.5))
    fig.patch.set_facecolor("white")
    fig.add_artist(Rectangle((0, 0.93), 1, 0.07, transform=fig.transFigure, color=NAVY))
    fig.text(0.015, 0.955, title, color="white", fontsize=17, fontweight="bold", va="center")
    fig.text(0.985, 0.955, "WIREFRAME: build in Power BI", color="#BDD7EE", fontsize=9, ha="right", va="center")
    fig.text(0.015, 0.905, subtitle, color="#595959", fontsize=9, style="italic")
    # slicer strip
    fig.add_artist(Rectangle((0.01, 0.03), 0.11, 0.86, transform=fig.transFigure, color="#F2F2F2"))
    fig.text(0.065, 0.865, "SLICERS", ha="center", fontsize=8, fontweight="bold", color=NAVY)
    for i, s in enumerate(slicers):
        y = 0.82 - i * 0.075
        fig.add_artist(Rectangle((0.018, y - 0.045), 0.095, 0.055, transform=fig.transFigure,
                                 facecolor="white", edgecolor=GREY))
        fig.text(0.065, y - 0.018, s, ha="center", va="center", fontsize=8, color=NAVY)
    return fig


def card(fig, x, w, label, value, sub=None, col=NAVY):
    fig.add_artist(Rectangle((x, 0.78), w, 0.11, transform=fig.transFigure, facecolor=LIGHT, edgecolor="none"))
    fig.text(x + w / 2, 0.865, label, ha="center", fontsize=8, color="#595959", fontweight="bold")
    fig.text(x + w / 2, 0.815, value, ha="center", va="center", fontsize=20, color=col, fontweight="bold")
    if sub:
        fig.text(x + w / 2, 0.787, sub, ha="center", fontsize=7, color="#595959")


def rate_bars(ax, series_rate, series_n, title, horizontal=True, minn=0):
    r = series_rate
    cols = [colour(v) for v in r.values]
    if horizontal:
        ax.barh(r.index, r.values, color=cols)
        ax.invert_yaxis()
        ax.axvline(BASE, color=NAVY, ls="--", lw=1)
        ax.xaxis.set_major_formatter(pct)
        for i, (v, n) in enumerate(zip(r.values, series_n.values)):
            ax.text(v + 0.005, i, f"{v:.0%}  (n={n})", va="center", fontsize=7.5)
        ax.set_xlim(0, max(r.values) * 1.35)
    else:
        ax.bar(r.index, r.values, color=cols)
        ax.axhline(BASE, color=NAVY, ls="--", lw=1)
        ax.yaxis.set_major_formatter(pct)
        for i, (v, n) in enumerate(zip(r.values, series_n.values)):
            ax.text(i, v + 0.008, f"{v:.0%}", ha="center", fontsize=8)
            if len(r) <= 4:
                ax.text(i, 0.005, f"n={n}", ha="center", fontsize=6.5, color="white")
        ax.set_ylim(0, min(1.0, max(r.values) * 1.15))
    ax.set_title(title, loc="left")


def grp(col, order=None):
    g = d.groupby(col)["Left"].agg(["mean", "size"])
    if order is not None:
        g = g.loc[order]
    return g["mean"], g["size"]


# =============================================================== page 1
fig = page("HR Attrition: Executive Summary", "Dashed line = company attrition rate. Red = 5+ points above, green = 5+ points below.",
           ["Department", "Job Role", "Gender", "Marital Status", "Age Band", "Business Travel"])
lv, st = d[d.Left == 1], d[d.Left == 0]
ot, no = d[d.OverTime == "Yes"].Left.mean(), d[d.OverTime == "No"].Left.mean()
w = 0.108
xs = np.linspace(0.14, 0.985 - w, 7)
for x, (lab, val, sub) in zip(xs, [
        ("HEADCOUNT", f"{len(d):,}", None), ("LEAVERS", f"{int(d.Left.sum())}", None),
        ("ATTRITION RATE", f"{BASE:.1%}", "company"), ("OVERTIME MULTIPLE", f"{ot/no:.1f}x", f"{ot:.0%} vs {no:.0%}"),
        ("AVG TENURE, LEAVERS", f"{lv.YearsAtCompany.mean():.1f} yrs", f"stayers {st.YearsAtCompany.mean():.1f}"),
        ("EARLY LEAVERS", f"{(lv.YearsAtCompany <= 2).mean():.0%}", f"<=2 yrs; {(d.YearsAtCompany<=2).mean():.0%} of staff"),
        ("LEAVERS' PAY / YR", f"{lv.AnnualIncome.sum()/1e6:.1f}M", "currency not stated")]):
    card(fig, x, w, lab, val, sub, RED if lab in ("ATTRITION RATE",) else NAVY)

ax = fig.add_axes([0.30, 0.10, 0.23, 0.60])
r, n = grp("JobRole")
o = r.sort_values(ascending=False).index
rate_bars(ax, r.loc[o], n.loc[o], "Attrition rate by job role")
ax = fig.add_axes([0.62, 0.40, 0.36, 0.30])
order = d.sort_values("TenureBandSort")["TenureBand"].unique()
r, n = grp("TenureBand", order)
rate_bars(ax, r, n, "Attrition rate by tenure (years at company)", horizontal=False)
ax = fig.add_axes([0.70, 0.08, 0.13, 0.24])
r, n = grp("Department")
rate_bars(ax, r.sort_values(ascending=False), n.loc[r.sort_values(ascending=False).index], "By department")
ax.tick_params(axis="y", labelsize=7)
ax = fig.add_axes([0.89, 0.08, 0.09, 0.24])
r, n = grp("OverTime")
rate_bars(ax, r, n, "By overtime", horizontal=False)
fig.savefig(OUT / "wireframe_1_summary.png", dpi=110)
plt.close(fig)

# =============================================================== page 2
fig = page("HR Attrition: What Drives It", "Drill from company to department to role using the decomposition tree. Matrix shows role x overtime.",
           ["Department", "Job Role", "Overtime", "Marital Status", "Income Band", "Job Level"])
specs = [("OverTime", "Overtime", None), ("StockOptionLevel", "Stock option level", None),
         ("BusinessTravel", "Business travel", None)]
pos = [[0.20, 0.57, 0.15, 0.30], [0.40, 0.57, 0.17, 0.30], [0.62, 0.57, 0.17, 0.30]]
for (col, title, order), p in zip(specs, pos):
    ax = fig.add_axes(p)
    r, n = grp(col)
    r.index = r.index.astype(str).str.replace("Travel_", "", regex=False)
    n.index = r.index
    rate_bars(ax, r, n, title, horizontal=False)
    ax.tick_params(axis="x", labelsize=7)
ax = fig.add_axes([0.85, 0.57, 0.13, 0.30])
r, n = grp("IncomeBand", d.sort_values("IncomeBandSort")["IncomeBand"].unique())
rate_bars(ax, r, n, "Monthly income", horizontal=False)
ax.tick_params(axis="x", labelsize=6, rotation=40)

# matrix: role x overtime
ax = fig.add_axes([0.29, 0.08, 0.27, 0.37])
m = d.pivot_table(index="JobRole", columns="OverTime", values="Left", aggfunc="mean")
cnt = d.pivot_table(index="JobRole", columns="OverTime", values="Left", aggfunc="size")
m = m.loc[m.mean(axis=1).sort_values(ascending=False).index]
ax.imshow(m.values, cmap="Reds", vmin=0, vmax=0.7, aspect="auto")
ax.set_xticks([0, 1])
ax.set_xticklabels(["No overtime", "Overtime"])
ax.set_yticks(range(len(m)))
ax.set_yticklabels(m.index, fontsize=8)
for i in range(m.shape[0]):
    for j in range(2):
        v, c_ = m.values[i, j], cnt.loc[m.index[i]].iloc[j]
        ax.text(j, i, f"{v:.0%}\n(n={c_})", ha="center", va="center", fontsize=7.5, color="white" if v > 0.35 else "black")
ax.set_title("Matrix: attrition rate, role x overtime", loc="left")
for s in ax.spines.values():
    s.set_visible(False)

ax = fig.add_axes([0.70, 0.08, 0.10, 0.37])
sat = []
for col, nm in [("JobSatisfaction", "Job satisfaction"), ("EnvironmentSatisfaction", "Environment satisfaction"), ("WorkLifeBalance", "Work-life balance")]:
    sat.append((nm, d[d[col] == 1].Left.mean(), d[d[col] > 1].Left.mean()))
y = np.arange(len(sat))
ax.barh(y - 0.2, [s[1] for s in sat], 0.38, color=RED, label="Rated 1 (lowest)")
ax.barh(y + 0.2, [s[2] for s in sat], 0.38, color=BLUE, label="Rated 2 to 4")
ax.set_yticks(y)
ax.set_yticklabels([s[0] for s in sat], fontsize=7.5)
ax.invert_yaxis()
ax.xaxis.set_major_formatter(pct)
ax.axvline(BASE, color=NAVY, ls="--", lw=1)
ax.legend(fontsize=7, frameon=False, loc="upper left", bbox_to_anchor=(-0.05, -0.09), ncol=2)
ax.set_title("Lowest satisfaction rating", loc="left")

fig.add_artist(Rectangle((0.83, 0.08), 0.15, 0.37, transform=fig.transFigure, facecolor="#F2F2F2", edgecolor=GREY, ls="--"))
fig.text(0.905, 0.40, "Decomposition tree", ha="center", fontsize=9, fontweight="bold", color=NAVY)
fig.text(0.905, 0.25, "Attrition rate\nexplain by: Department,\nJob Role, Overtime,\nTenure Band", ha="center", va="center", fontsize=8, color="#595959")
fig.text(0.905, 0.12, "(native Power BI visual)", ha="center", fontsize=7, color=GREY)
fig.savefig(OUT / "wireframe_2_drivers.png", dpi=110)
plt.close(fig)

# =============================================================== page 3
fig = page("HR Attrition: Retention Watchlist", "Current employees with several known risk factors (default: 4 or more of 6). Rule-based and tested only on this same data.",
           ["Department", "Job Role", "Risk threshold", "Replacement cost %"])
T = 4
cur = d[(d.Left == 0) & (d.RiskFlagCount >= T)]
w3 = 0.19
x3 = np.linspace(0.14, 0.985 - w3, 4)
for x, (lab, val, sub) in zip(x3, [
        ("AT-RISK EMPLOYEES (4+ FLAGS)", f"{len(cur)}", f"{len(cur)/len(d[d.Left==0]):.0%} of current staff"),
        ("PAY OF AT-RISK STAFF / YR", f"{cur.AnnualIncome.sum()/1e6:.1f}M", "currency not stated"),
        ("COST IF ALL LEFT @ 50%", f"{cur.AnnualIncome.sum()*0.5/1e6:.1f}M", "50% = assumption, adjustable"),
        ("ATTRITION, 4+ FLAGS vs 0-1", f"{d[d.RiskFlagCount>=T].Left.mean():.0%} vs {d[d.RiskFlagCount<=1].Left.mean():.0%}", "in-sample, optimistic")]):
    card(fig, x, w3, lab, val, sub)

ax = fig.add_axes([0.20, 0.42, 0.27, 0.28])
g = d.groupby("RiskFlagCount")["Left"].agg(["mean", "size"])
rate_bars(ax, g["mean"].rename(index=str), g["size"].rename(index=str), "Attrition rate by number of risk flags", horizontal=False)
ax.set_xlabel("Risk flags (6 flags = 1 person)", fontsize=7)

ax = fig.add_axes([0.30, 0.07, 0.17, 0.24])
fl = {"Overtime": "FlagOvertime", "Frequent travel": "FlagFrequentTravel", "No stock options": "FlagNoStockOptions",
      "Tenure <= 2 yrs": "FlagShortTenure", "Entry level": "FlagEntryLevel", "Low satisfaction": "FlagLowSatisfaction"}
vals = [(k, cur[v].mean()) for k, v in fl.items()]
ax.barh([k for k, _ in vals], [v for _, v in vals], color=BLUE)
ax.invert_yaxis()
ax.xaxis.set_major_formatter(pct)
ax.set_title("Which flags the at-risk group carry", loc="left")
for i, (_, v) in enumerate(vals):
    ax.text(v + 0.01, i, f"{v:.0%}", va="center", fontsize=8)
ax.set_xlim(0, 1.1)

# table
ax = fig.add_axes([0.51, 0.07, 0.47, 0.63])
ax.axis("off")
ax.set_title("Employees to talk to first (current staff, most flags first)", loc="left")
role_rate = d.groupby("JobRole")["Left"].mean()
cur = cur.assign(RoleRate=cur["JobRole"].map(role_rate).map(lambda v: f"{v:.0%}"))
top = cur.sort_values(["RiskFlagCount", "JobLevel", "YearsAtCompany"], ascending=[False, True, True]).head(12)
cols = ["EmployeeNumber", "JobRole", "Department", "YearsAtCompany", "MonthlyIncome", "RiskFlagCount", "RoleRate"]
heads = ["Emp #", "Job role", "Department", "Tenure", "Monthly pay", "Flags", "Role attrition"]
tb = ax.table(cellText=[[str(r[c]) if c != "MonthlyIncome" else f"{r[c]:,}" for c in cols] for _, r in top.iterrows()],
              colLabels=heads, loc="upper center", cellLoc="left", colWidths=[0.09, 0.22, 0.24, 0.09, 0.13, 0.07, 0.14])
tb.auto_set_font_size(False)
tb.set_fontsize(7.5)
tb.scale(1, 1.55)
for (r_, c_), cell in tb.get_celld().items():
    cell.set_edgecolor("#D9D9D9")
    if r_ == 0:
        cell.set_facecolor(NAVY)
        cell.set_text_props(color="white", fontweight="bold")
fig.text(0.51, 0.045, "Drill-through: right-click a job role on page 1 > Drill through > this page.", fontsize=7.5, color="#595959", style="italic")
fig.savefig(OUT / "wireframe_3_watchlist.png", dpi=110)
plt.close(fig)
print("wireframes saved")
