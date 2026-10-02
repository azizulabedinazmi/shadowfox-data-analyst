"""
Clean the Superstore dataset for the Beginner-level task.

Input : data/raw/superstore_raw.csv
Output: data/clean/superstore_clean.csv      (order lines, 1 row per line item)
        data/clean/returns.csv               (1 row per returned order)
        data/clean/regional_managers.csv     (1 row per region)
        docs/cleaning_log.csv                (every step: issue, action, rows affected)

Run from the 01-beginner folder:  python scripts/clean_superstore.py
"""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "superstore_raw.csv"
CLEAN = ROOT / "data" / "clean"
DOCS = ROOT / "docs"
CLEAN.mkdir(parents=True, exist_ok=True)
DOCS.mkdir(parents=True, exist_ok=True)

log = []


def record(step, issue, action, affected, rows_after):
    log.append(
        {
            "Step": len(log) + 1,
            "Issue found": issue,
            "Action taken": action,
            "Rows affected": affected,
            "Order rows after step": rows_after,
        }
    )


# 1. Load everything as text so nothing is silently converted -----------------
raw = pd.read_csv(RAW, dtype=str, keep_default_na=False, na_values=[""])
raw = raw.apply(lambda s: s.str.strip())
n_raw = len(raw)

# 2. The CSV is three Excel tabs stacked on top of each other ------------------
is_order = raw["Row ID"].str.fullmatch(r"\d+", na=False)
orders = raw[is_order].copy()

# People tab: header row 'Person' / 'Region', then one row per region
p_start = raw.index[raw["Row ID"] == "Person"][0]
r_start = raw.index[raw["Row ID"] == "Returned"][0]
people = raw.loc[p_start + 1 : r_start - 1, ["Row ID", "Order ID"]]
people.columns = ["Regional Manager", "Region"]

# Returns tab: header row 'Returned' / 'Order ID', then 'Yes' + Order ID
returns = raw.loc[r_start + 1 :, ["Row ID", "Order ID"]]
returns.columns = ["Returned", "Order ID"]

record(
    "Split combined file",
    f"Raw CSV has {n_raw:,} rows: the Orders, People and Returns tabs were exported "
    "into one file, so {0:,} rows below the real data are not orders.".format(n_raw - len(orders)),
    f"Separated into three tables: Orders ({len(orders):,} rows), "
    f"People ({len(people)} rows), Returns ({len(returns)} rows).",
    n_raw - len(orders),
    len(orders),
)

# 3. Returns table lists one entry per line item; we only need one per order ----
n_ret_before = len(returns)
returns = returns.drop_duplicates(subset="Order ID")[["Order ID"]].reset_index(drop=True)
returns["Returned"] = "Yes"
missing = (~returns["Order ID"].isin(orders["Order ID"])).sum()
record(
    "De-duplicate Returns",
    f"Returns tab has {n_ret_before} entries but only {len(returns)} distinct Order IDs "
    f"(repeated per line item). {missing} returned Order IDs are missing from Orders.",
    "Kept one row per returned order.",
    n_ret_before - len(returns),
    len(orders),
)

# 4. Data types ----------------------------------------------------------------
orders["Row ID"] = orders["Row ID"].astype(int)
for col in ["Order Date", "Ship Date"]:
    parsed = pd.to_datetime(orders[col], format="%m/%d/%Y", errors="coerce")
    bad = parsed.isna().sum()
    orders[col] = parsed
    record(
        f"Convert {col}",
        f"{col} stored as text in M/D/YYYY format ({bad} unparseable values).",
        "Converted to a true date.",
        len(orders) - bad,
        len(orders),
    )
for col in ["Sales", "Quantity", "Discount", "Profit"]:
    orders[col] = pd.to_numeric(orders[col], errors="raise")
orders["Quantity"] = orders["Quantity"].astype(int)
record(
    "Convert numeric columns",
    "Sales, Quantity, Discount and Profit read in as text.",
    "Converted to numbers (Quantity as whole number).",
    len(orders),
    len(orders),
)

# 5. Missing values -------------------------------------------------------------
nulls = orders.isna().sum()
nulls = nulls[nulls > 0]
assert list(nulls.index) == ["Postal Code"], f"Unexpected nulls: {nulls.to_dict()}"
mask = orders["Postal Code"].isna()
assert (orders.loc[mask, ["City", "State"]].drop_duplicates().values.tolist()
        == [["Burlington", "Vermont"]])
orders.loc[mask, "Postal Code"] = "05401"
record(
    "Missing Postal Code",
    f"{int(mask.sum())} rows have no Postal Code. All are Burlington, Vermont.",
    "Filled with 05401 (Burlington, VT main ZIP code). This is an outside fact, not "
    "something derived from the data. Postal Code is not used in any KPI.",
    int(mask.sum()),
    len(orders),
)

# 6. Postal code format ---------------------------------------------------------
orders["Postal Code"] = (
    orders["Postal Code"].str.replace(r"\.0$", "", regex=True).str.zfill(5)
)
record(
    "Postal Code format",
    "Postal Code was read as a number, which drops leading zeros "
    "(e.g. 5401 instead of 05401).",
    "Stored as 5-character text.",
    len(orders),
    len(orders),
)

# 7. Duplicates -----------------------------------------------------------------
dedupe_cols = [c for c in orders.columns if c != "Row ID"]
dup_mask = orders.duplicated(subset=dedupe_cols, keep="first")
removed_ids = orders.loc[dup_mask, "Row ID"].tolist()
orders = orders[~dup_mask]
record(
    "Duplicate order lines",
    "Rows identical in every column except Row ID: same order, product, "
    f"quantity and price (Row ID {removed_ids}).",
    "Removed the repeat and kept the first. A repeated line with identical values "
    "inside one order is most likely a data-entry duplicate. Impact on Sales is "
    "under 0.02%.",
    int(dup_mask.sum()),
    len(orders),
)

# 8. Validation checks (no change to data, results are logged) -----------------
checks = {
    "Ship Date is never before Order Date": (orders["Ship Date"] >= orders["Order Date"]).all(),
    "Sales > 0 on every row": (orders["Sales"] > 0).all(),
    "Quantity > 0 on every row": (orders["Quantity"] > 0).all(),
    "Discount between 0 and 1": orders["Discount"].between(0, 1).all(),
    "Each State maps to one Region": (orders.groupby("State")["Region"].nunique() == 1).all(),
    "Each Customer ID maps to one name": (orders.groupby("Customer ID")["Customer Name"].nunique() == 1).all(),
    "Every Region has a manager": set(orders["Region"]) == set(people["Region"]),
}
for name, ok in checks.items():
    record(f"Check: {name}", "Integrity check run before any analysis.", "Passed." if ok else "FAILED, investigate.", 0, len(orders))

# 9. Known issue we do NOT fix --------------------------------------------------
multi = orders.groupby("Product ID")["Product Name"].nunique()
n_multi = int((multi > 1).sum())
record(
    "Product ID reused for different products",
    f"{n_multi} Product IDs are attached to two different Product Names "
    "(e.g. FUR-BO-10002213 is both a Sauder and a DMI bookcase).",
    "Left as is. Product-level analysis uses Product Name, not Product ID.",
    n_multi,
    len(orders),
)

# 10. Outliers we keep ----------------------------------------------------------
big_loss = orders.nsmallest(1, "Profit").iloc[0]
record(
    "Extreme values",
    f"Largest loss on one line is {big_loss['Profit']:,.2f} "
    f"({big_loss['Sub-Category']}, {big_loss['Discount']:.0%} discount). "
    "Discounts reach 80%.",
    "Kept. These are consistent with the discount level and Sales, so they are real "
    "business events rather than errors. They are worth discussing in the insights.",
    0,
    len(orders),
)

# 11. Output --------------------------------------------------------------------
orders = orders.sort_values("Row ID").reset_index(drop=True)
orders.to_csv(CLEAN / "superstore_clean.csv", index=False, date_format="%Y-%m-%d")
returns.to_csv(CLEAN / "returns.csv", index=False)
people.to_csv(CLEAN / "regional_managers.csv", index=False)
pd.DataFrame(log).to_csv(DOCS / "cleaning_log.csv", index=False)

print(f"Orders: {len(orders):,} rows | Returns: {len(returns)} | Managers: {len(people)}")
print(f"Sales {orders['Sales'].sum():,.2f} | Profit {orders['Profit'].sum():,.2f}")
print(pd.DataFrame(log)[["Step", "Issue found", "Rows affected"]].to_string(index=False, max_colwidth=60))
