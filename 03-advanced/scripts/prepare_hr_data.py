"""
Prepare the IBM HR Analytics Employee Attrition dataset for Power BI.

Input : data/raw/ibm_hr_attrition_raw.csv
Output: data/clean/hr_employees.csv   one row per employee, load this into Power BI
        docs/cleaning_log.csv         every change, with counts
        docs/data_dictionary.csv      every column in the output

Run from the 03-advanced folder:  python scripts/prepare_hr_data.py
"""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "ibm_hr_attrition_raw.csv"
CLEAN = ROOT / "data" / "clean"
DOCS = ROOT / "docs"
CLEAN.mkdir(parents=True, exist_ok=True)
DOCS.mkdir(parents=True, exist_ok=True)

log = []


def record(step, issue, action, affected):
    log.append({"Step": len(log) + 1, "Area": step, "Issue found": issue,
                "Action taken": action, "Rows or columns affected": affected})


# utf-8-sig removes the byte-order mark that otherwise corrupts the first column name ("ï»¿Age")
df = pd.read_csv(RAW, encoding="utf-8-sig")
n_rows, n_cols = df.shape
record("Load", "File starts with a byte-order mark, which breaks the first column name in some tools.",
       "Read as UTF-8 with BOM removed.", "1 column name")

# ------------------------------------------------------------------ checks
assert df.isna().sum().sum() == 0, "unexpected nulls"
assert not df.duplicated().any() and df["EmployeeNumber"].is_unique
record("Quality check", "Looked for nulls, duplicate rows and duplicate EmployeeNumber.",
       f"None found in {n_rows:,} rows. The dataset is already clean, so the work is mostly transformation.", 0)

obj = df.select_dtypes(exclude="number").columns
assert all((df[c] == df[c].str.strip()).all() for c in obj)
record("Quality check", "Checked text columns for stray spaces and mixed spellings.",
       "None found.", 0)

# ------------------------------------------------------- constant columns
const = [c for c in df.columns if df[c].nunique() == 1]
assert set(const) == {"EmployeeCount", "Over18", "StandardHours"}, const
df = df.drop(columns=const)
record("Columns", "Three columns hold a single value for every employee (EmployeeCount=1, Over18=Y, StandardHours=80).",
       "Dropped. They cannot explain differences between employees.", ", ".join(const))

# ------------------------------------------------ logic checks (no changes)
checks = {
    "YearsAtCompany <= TotalWorkingYears": (df["YearsAtCompany"] <= df["TotalWorkingYears"]).all(),
    "YearsInCurrentRole <= YearsAtCompany": (df["YearsInCurrentRole"] <= df["YearsAtCompany"]).all(),
    "YearsWithCurrManager <= YearsAtCompany": (df["YearsWithCurrManager"] <= df["YearsAtCompany"]).all(),
    "YearsSinceLastPromotion <= YearsAtCompany": (df["YearsSinceLastPromotion"] <= df["YearsAtCompany"]).all(),
    "Age - TotalWorkingYears >= 14": ((df["Age"] - df["TotalWorkingYears"]) >= 14).all(),
}
for name, ok in checks.items():
    record("Logic check", f"Rule: {name}.", "Passed." if ok else "FAILED, investigate.", 0)
    assert ok, name

# ---------------------------------------------------------- pay columns
pay_corr = {c: df["MonthlyIncome"].corr(df[c]) for c in ["DailyRate", "HourlyRate", "MonthlyRate"]}
record("Known issue",
       "DailyRate, HourlyRate and MonthlyRate are unrelated to MonthlyIncome (correlations "
       + ", ".join(f"{k} {v:.2f}" for k, v in pay_corr.items())
       + "), while MonthlyIncome tracks JobLevel closely.",
       "Kept in the file but not used anywhere in the dashboard. MonthlyIncome is used as the pay measure.",
       "3 columns")

# ------------------------------------------------------- flags and labels
df["Left"] = (df["Attrition"] == "Yes").astype(int)
df["OvertimeFlag"] = (df["OverTime"] == "Yes").astype(int)
record("Transformation", "Attrition is Yes/No text, which is awkward to sum or average.",
       "Added Left (1 = left, 0 = stayed) and OvertimeFlag (1/0). Original text columns kept for slicers.",
       "2 columns added")

scales = {
    "Education": {1: "Below College", 2: "College", 3: "Bachelor", 4: "Master", 5: "Doctor"},
    "EnvironmentSatisfaction": {1: "Low", 2: "Medium", 3: "High", 4: "Very High"},
    "JobInvolvement": {1: "Low", 2: "Medium", 3: "High", 4: "Very High"},
    "JobSatisfaction": {1: "Low", 2: "Medium", 3: "High", 4: "Very High"},
    "RelationshipSatisfaction": {1: "Low", 2: "Medium", 3: "High", 4: "Very High"},
    "WorkLifeBalance": {1: "Bad", 2: "Good", 3: "Better", 4: "Best"},
    "PerformanceRating": {1: "Low", 2: "Good", 3: "Excellent", 4: "Outstanding"},
}
for col, mp in scales.items():
    df[f"{col}Label"] = df[col].map(mp)
    assert df[f"{col}Label"].notna().all(), col
record("Transformation", "Survey and rating columns are stored as numbers 1 to 4 (or 1 to 5), which read as meaningless on a chart.",
       "Added a text label column for each (e.g. JobSatisfactionLabel). The number stays for sorting. Label meanings follow the "
       "dataset's published data dictionary: confirm against your copy of the task materials.", "7 columns added")


def band(series, edges, labels):
    return pd.cut(series, bins=edges, labels=labels, right=True, include_lowest=True)


bands = {
    "AgeBand": ("Age", [0, 25, 35, 45, 100], ["18-25", "26-35", "36-45", "46+"]),
    "TenureBand": ("YearsAtCompany", [-1, 1, 2, 5, 10, 100], ["0-1 yrs", "2 yrs", "3-5 yrs", "6-10 yrs", "11+ yrs"]),
    "IncomeBand": ("MonthlyIncome", [0, 3000, 5000, 8000, 12000, 1e9],
                   ["Up to 3K", "3K-5K", "5K-8K", "8K-12K", "Over 12K"]),
    "DistanceBand": ("DistanceFromHome", [0, 5, 10, 20, 100], ["1-5", "6-10", "11-20", "21+"]),
    "ManagerTenureBand": ("YearsWithCurrManager", [-1, 0, 2, 5, 100], ["New (<1 yr)", "1-2 yrs", "3-5 yrs", "6+ yrs"]),
}
for name, (src, edges, labels) in bands.items():
    df[name] = band(df[src], edges, labels).astype(str)
    df[f"{name}Sort"] = band(df[src], edges, labels).cat.codes + 1
    assert df[name].ne("nan").all(), name
record("Transformation", "Continuous columns (age, tenure, income, distance, years with manager) are too granular for group comparison.",
       "Added 5 band columns, each with a *Sort column so Power BI can order bands correctly (use Sort by column). "
       "Band edges were chosen to give groups of reasonable size. Income is in the dataset's currency, which is not stated.",
       "10 columns added")

df["AnnualIncome"] = df["MonthlyIncome"] * 12
record("Transformation", "Cost questions need a yearly figure.", "AnnualIncome = MonthlyIncome x 12.", "1 column added")

# ------------------------------------------------------------ risk flags
df["FlagOvertime"] = (df["OverTime"] == "Yes").astype(int)
df["FlagFrequentTravel"] = (df["BusinessTravel"] == "Travel_Frequently").astype(int)
df["FlagNoStockOptions"] = (df["StockOptionLevel"] == 0).astype(int)
df["FlagShortTenure"] = (df["YearsAtCompany"] <= 2).astype(int)
df["FlagEntryLevel"] = (df["JobLevel"] == 1).astype(int)
df["FlagLowSatisfaction"] = ((df["JobSatisfaction"] == 1) | (df["EnvironmentSatisfaction"] == 1)
                             | (df["WorkLifeBalance"] == 1)).astype(int)
flag_cols = [c for c in df.columns if c.startswith("Flag")]
df["RiskFlagCount"] = df[flag_cols].sum(axis=1)
record("Transformation",
       "The dashboard needs a way to prioritise current employees for a retention conversation.",
       "Added six yes/no risk flags (overtime, frequent travel, no stock options, tenure of 2 years or less, entry level "
       "(JobLevel 1), any of job satisfaction / environment satisfaction / work-life balance rated 1) and RiskFlagCount (0 to 6). "
       "This is a transparent rule, not a fitted model. The flags were chosen after looking at this same data (the entry-level "
       "flag was added after a first version flagged many senior staff who almost never leave), so its apparent accuracy is "
       "optimistic and should be tested on new data before relying on it.", "7 columns added")

# --------------------------------------------------------------- order
first = ["EmployeeNumber", "Attrition", "Left"]
df = df[first + [c for c in df.columns if c not in first]]
df = df.sort_values("EmployeeNumber").reset_index(drop=True)

assert len(df) == n_rows and df["EmployeeNumber"].is_unique
df.to_csv(CLEAN / "hr_employees.csv", index=False)
pd.DataFrame(log).to_csv(DOCS / "cleaning_log.csv", index=False)

# ------------------------------------------------------ data dictionary
desc = {
    "EmployeeNumber": "Employee ID (unique)", "Attrition": "Yes if the employee left, otherwise No",
    "Left": "1 if left, 0 if stayed (use for rates)", "Age": "Age in years",
    "BusinessTravel": "Non-Travel, Travel_Rarely or Travel_Frequently", "DailyRate": "Daily rate (not used, see cleaning log)",
    "Department": "Sales, Research & Development or Human Resources", "DistanceFromHome": "Distance from home (units not stated)",
    "Education": "Education level 1 to 5", "EducationField": "Field of study", "EmployeeNumber ": "",
    "EnvironmentSatisfaction": "Rating 1 (Low) to 4 (Very High)", "Gender": "Female or Male",
    "HourlyRate": "Hourly rate (not used)", "JobInvolvement": "Rating 1 to 4", "JobLevel": "Seniority 1 (junior) to 5",
    "JobRole": "Job title", "JobSatisfaction": "Rating 1 to 4", "MaritalStatus": "Single, Married or Divorced",
    "MonthlyIncome": "Monthly pay (currency not stated)", "MonthlyRate": "Monthly rate (not used)",
    "NumCompaniesWorked": "Number of previous employers", "OverTime": "Yes if works overtime",
    "PercentSalaryHike": "Last salary increase, percent", "PerformanceRating": "Rating 3 or 4 only in this dataset",
    "RelationshipSatisfaction": "Rating 1 to 4", "StockOptionLevel": "0 to 3", "TotalWorkingYears": "Career length in years",
    "TrainingTimesLastYear": "Training sessions last year", "WorkLifeBalance": "Rating 1 to 4",
    "YearsAtCompany": "Tenure in years", "YearsInCurrentRole": "Years in current role",
    "YearsSinceLastPromotion": "Years since last promotion", "YearsWithCurrManager": "Years with current manager",
    "OvertimeFlag": "1 if OverTime = Yes", "AnnualIncome": "MonthlyIncome x 12",
    "RiskFlagCount": "Number of risk flags (0 to 6), see cleaning log",
}
rows = []
for c in df.columns:
    kind = ("Added" if c not in pd.read_csv(RAW, encoding="utf-8-sig", nrows=1).columns else "Original")
    d = desc.get(c) or (f"Text label for {c[:-5]}" if c.endswith("Label") else
                        f"Sort order for {c[:-4]}" if c.endswith("Sort") else
                        f"Band of {bands[c][0]}" if c in bands else
                        f"Risk flag (1/0): {c[4:]}" if c.startswith("Flag") else "")
    rows.append({"Column": c, "Type": str(df[c].dtype), "Origin": kind, "Description": d})
pd.DataFrame(rows).to_csv(DOCS / "data_dictionary.csv", index=False)

print(f"{n_rows:,} employees | {len(df.columns)} columns (was {n_cols})")
print(f"Attrition {df['Left'].mean():.1%} ({df['Left'].sum()} of {len(df)})")
print(df.groupby("RiskFlagCount")["Left"].agg(["size", "mean"]).round(3).T.to_string())
