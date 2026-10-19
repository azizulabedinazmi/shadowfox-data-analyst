"""
Compute the value every DAX measure should show, using pandas, so the Power BI
dashboard can be checked number by number.

Writes docs/expected_values.csv and analysis/metrics.json.
Run from the 03-advanced folder:  python scripts/expected_values.py
"""
import json
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
d = pd.read_csv(ROOT / "data/clean/hr_employees.csv")
(ROOT / "analysis").mkdir(exist_ok=True)
rows, M = [], {}


def add(measure, flt, value, fmt):
    rows.append({"Measure": measure, "Filter applied": flt, "Expected value": value, "Format": fmt})


def rate(x):
    return x["Left"].mean()


HC, LV = len(d), int(d["Left"].sum())
base = d["Left"].mean()
ot, no = d[d.OverTime == "Yes"], d[d.OverTime == "No"]
lv, st = d[d.Left == 1], d[d.Left == 0]
M.update(headcount=HC, leavers=LV, current=HC - LV, attrition_rate=base,
         ot_rate=rate(ot), no_ot_rate=rate(no), ot_multiple=rate(ot) / rate(no),
         avg_tenure_leavers=lv.YearsAtCompany.mean(), avg_tenure_stayers=st.YearsAtCompany.mean(),
         avg_income_leavers=lv.MonthlyIncome.mean(), avg_income_stayers=st.MonthlyIncome.mean(),
         annual_salary_leavers=float(lv.AnnualIncome.sum()),
         early_leaver_share=float((lv.YearsAtCompany <= 2).mean()),
         early_staff_share=float((d.YearsAtCompany <= 2).mean()))
M["cost_at_50pct"] = M["annual_salary_leavers"] * 0.5

add("Headcount", "none", HC, "#,##0")
add("Leavers", "none", LV, "#,##0")
add("Current Employees", "none", HC - LV, "#,##0")
add("Attrition Rate", "none", base, "0.0%")
add("Overtime Attrition Rate", "none", rate(ot), "0.0%")
add("No Overtime Attrition Rate", "none", rate(no), "0.0%")
add("Overtime Multiple", "none", M["ot_multiple"], '0.0"x"')
add("Avg Tenure Leavers (yrs)", "none", M["avg_tenure_leavers"], "0.0")
add("Avg Tenure Stayers (yrs)", "none", M["avg_tenure_stayers"], "0.0")
add("Avg Monthly Income Leavers", "none", M["avg_income_leavers"], "#,##0")
add("Avg Monthly Income Stayers", "none", M["avg_income_stayers"], "#,##0")
add("Annual Salary of Leavers", "none", M["annual_salary_leavers"], "#,##0")
add("Estimated Cost of Attrition", "Replacement Cost = 50%", M["cost_at_50pct"], "#,##0")
add("Early Leaver Share (tenure <= 2 yrs)", "none", M["early_leaver_share"], "0.0%")

for t in (3, 4, 5):
    cur = d[(d.Left == 0) & (d.RiskFlagCount >= t)]
    add("At-Risk Employees", f"Risk Threshold = {t}", len(cur), "#,##0")
    add("At-Risk Annual Salary", f"Risk Threshold = {t}", float(cur.AnnualIncome.sum()), "#,##0")
    if t == 4:
        M["at_risk_4"], M["at_risk_4_salary"] = len(cur), float(cur.AnnualIncome.sum())
M["leavers_flags4_share"] = float(((d.Left == 1) & (d.RiskFlagCount >= 4)).sum() / LV)
M["staff_flags4_share"] = float((d.RiskFlagCount >= 4).mean())
M["rate_flags4plus"] = float(d[d.RiskFlagCount >= 4].Left.mean())
M["rate_flags01"] = float(d[d.RiskFlagCount <= 1].Left.mean())
M["roles_flags4_current"] = d[(d.Left == 0) & (d.RiskFlagCount >= 4)].JobRole.value_counts().to_dict()
M["rate_by_flags"] = {int(k): [int(v["size"]), float(v["mean"])] for k, v in d.groupby("RiskFlagCount")["Left"].agg(["size", "mean"]).iterrows()}

for col in ["Department", "JobRole", "OverTime", "BusinessTravel", "MaritalStatus", "StockOptionLevel", "JobLevel"]:
    for k, g in d.groupby(col):
        add("Attrition Rate", f"{col} = {k}", rate(g), "0.0%")
        add("Headcount", f"{col} = {k}", len(g), "#,##0")
for col, sort in [("TenureBand", "TenureBandSort"), ("AgeBand", "AgeBandSort"), ("IncomeBand", "IncomeBandSort")]:
    for k, g in d.sort_values(sort).groupby(col, sort=False):
        add("Attrition Rate", f"{col} = {k}", rate(g), "0.0%")
        add("Headcount", f"{col} = {k}", len(g), "#,##0")
for (r, o), g in d.groupby(["JobRole", "OverTime"]):
    add("Attrition Rate", f"JobRole = {r} AND OverTime = {o}", rate(g), "0.0%")
    add("Headcount", f"JobRole = {r} AND OverTime = {o}", len(g), "#,##0")
for (o, l1), g in d.assign(L1=d.JobLevel == 1).groupby(["OverTime", "L1"]):
    M[f"ot_{o}_level1_{l1}"] = (len(g), rate(g))

# drivers that do NOT matter (for the insight page)
from math import isnan
try:
    from scipy.stats import chi2_contingency
    M["p_values"] = {c: float(chi2_contingency(pd.crosstab(d[c], d.Left))[1])
                     for c in ["Gender", "PerformanceRating", "PercentSalaryHike", "Education", "RelationshipSatisfaction",
                               "OverTime", "StockOptionLevel", "JobLevel", "BusinessTravel", "MaritalStatus"]}
except Exception:
    M["p_values"] = {}

out = pd.DataFrame(rows)
out["Expected value"] = out["Expected value"].map(lambda v: round(float(v), 6))
out.to_csv(ROOT / "docs/expected_values.csv", index=False)
json.dump(M, open(ROOT / "analysis/metrics.json", "w"), indent=1, default=float)
print(len(out), "expected values written")
print({k: (round(v, 4) if isinstance(v, float) else v) for k, v in M.items() if not isinstance(v, (dict, tuple))})
print(M["p_values"])
