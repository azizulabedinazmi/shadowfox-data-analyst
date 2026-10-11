"""
Clean the Online Retail dataset (UCI / mirrored on GitHub).

Input : data/raw/online_retail_raw.csv
Output: data/clean/sales_all.csv        valid product sales, any customer (revenue / product / country views)
        data/clean/sales_customers.csv  same, only rows with a CustomerID (customer / retention views)
        data/clean/cancellations.csv    cancelled lines (kept for the returns view)
        docs/cleaning_log.csv           every step with rows removed

Run from the 02-intermediate folder:  python scripts/clean_online_retail.py
"""
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "online_retail_raw.csv"
CLEAN = ROOT / "data" / "clean"
DOCS = ROOT / "docs"
CLEAN.mkdir(parents=True, exist_ok=True)
DOCS.mkdir(parents=True, exist_ok=True)

log = []


def record(issue, action, removed, rows_after):
    log.append({"Step": len(log) + 1, "Issue found": issue, "Action taken": action,
                "Rows affected": removed, "Rows remaining": rows_after})


df = pd.read_csv(RAW, dtype=str, encoding="latin-1")
df = df.apply(lambda s: s.str.strip())
n0 = len(df)
record("Raw file loaded", "Read all columns as text so nothing is converted silently.", 0, n0)

# types
df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"], format="%m/%d/%Y %H:%M", errors="raise")
df["Quantity"] = pd.to_numeric(df["Quantity"])
df["UnitPrice"] = pd.to_numeric(df["UnitPrice"])
record("Dates and numbers stored as text",
       "Converted InvoiceDate to datetime (M/D/YYYY H:MM), Quantity and UnitPrice to numbers.", 0, len(df))

# exact duplicates
d = df.duplicated().sum()
df = df.drop_duplicates()
record("Exact duplicate lines (identical in every column)",
       "Removed repeats and kept the first. Same invoice, product, quantity, price and time "
       "is most likely a double entry.", int(d), len(df))

# cancellations
is_cancel = df["InvoiceNo"].str.startswith("C")
canc = df[is_cancel].copy()
df = df[~is_cancel]
record("Cancellation invoices (InvoiceNo starts with 'C')",
       "Moved to cancellations.csv. Revenue analysis uses completed sales; cancellations are "
       "reported separately as a return rate.", int(is_cancel.sum()), len(df))

# non-product stock codes
nonprod = ["POST", "DOT", "M", "BANK CHARGES", "AMAZONFEE", "CRUK", "S", "D", "B", "C2", "AMAZONFEE", "ADJUST", "ADJUST2"]
mask = df["StockCode"].isin(nonprod) | df["StockCode"].str.upper().str.startswith("GIFT_")
n_np = int(mask.sum())
df = df[~mask]
record("Non-product lines (postage, manual, bank charges, Amazon fees, gift vouchers)",
       "Removed. These are not products and would distort product and revenue analysis.", n_np, len(df))

# invalid qty / price
bad = (df["Quantity"] <= 0) | (df["UnitPrice"] <= 0)
nb = int(bad.sum())
df = df[~bad]
record("Quantity <= 0 or UnitPrice <= 0 on non-cancelled invoices (stock write-offs, adjustments, free items)",
       "Removed. They carry no sales revenue.", nb, len(df))

# description
df["Description"] = df["Description"].str.upper()
miss_desc = int(df["Description"].isna().sum())
df["Description"] = df["Description"].fillna("UNKNOWN")
record("Missing Description", "Filled with 'UNKNOWN'. Product analysis uses StockCode as the key.", miss_desc, len(df))

# one name per stock code (most common)
mode = df.groupby("StockCode")["Description"].agg(lambda s: s.mode().iloc[0])
changed = int((df["StockCode"].map(mode) != df["Description"]).sum())
df["Description"] = df["StockCode"].map(mode)
record("StockCode has several spelling variants of its description",
       "Used the most common description for each StockCode.", changed, len(df))

# duplicates created by standardising descriptions
d2 = int(df.duplicated().sum())
df = df.drop_duplicates()
record("Duplicates revealed after standardising descriptions",
       "Removed (same invoice, product, quantity, price, time).", d2, len(df))

# derived
df["Revenue"] = (df["Quantity"] * df["UnitPrice"]).round(2)
df["InvoiceMonth"] = df["InvoiceDate"].dt.to_period("M").astype(str)
df["CustomerID"] = df["CustomerID"].str.replace(r"\.0$", "", regex=True)
record("Derived columns", "Added Revenue = Quantity x UnitPrice and InvoiceMonth.", 0, len(df))

# missing customer
no_cust = int(df["CustomerID"].isna().sum())
record("Missing CustomerID (guest or untracked orders)",
       "Kept in sales_all.csv for revenue, product and country analysis. Excluded from "
       "sales_customers.csv because customer behaviour cannot be tracked without an ID.", no_cust, len(df))

# non-product lines in the cancellations file
canc = canc[~(canc["StockCode"].isin(nonprod) | canc["StockCode"].str.upper().str.startswith("GIFT_"))].copy()
canc["Quantity"] = canc["Quantity"].astype(float)

# order-and-immediately-cancel pairs: a very large sale reversed in full by the same customer
big = canc[canc["Quantity"].abs() >= 10000]
pairs_sales, pairs_canc = [], []
for r_ in big.itertuples():
    m_ = df[(df["CustomerID"] == r_.CustomerID) & (df["StockCode"] == r_.StockCode) & (df["Quantity"] == -r_.Quantity)]
    if len(m_):
        pairs_sales.append(m_.index[0])
        pairs_canc.append(r_.Index)
pair_desc = ", ".join(f"{df.loc[i, 'Description']} x{int(df.loc[i, 'Quantity']):,}" for i in pairs_sales)
pair_rev = float(df.loc[pairs_sales, "Revenue"].sum()) if pairs_sales else 0.0
df = df.drop(index=pairs_sales)
canc = canc.drop(index=pairs_canc)
record("Orders of 10,000+ units that the same customer cancelled in full (" + pair_desc + ")",
       f"Removed both the sale and its cancellation. They are one reversed transaction worth {pair_rev:,.0f} "
       "in revenue that was never kept. Leaving them in would make a cancelled order the #2 product.",
       len(pairs_sales), len(df))

# order-line sanity
extreme = df.nlargest(3, "Revenue")[["InvoiceNo", "Description", "Quantity", "Revenue"]]
record("Extreme orders",
       "Kept. Largest lines: " + "; ".join(f"{r.Description} x{r.Quantity} = {r.Revenue:,.0f}" for r in extreme.itertuples()),
       0, len(df))

# cancellations cleaned
canc["CustomerID"] = canc["CustomerID"].str.replace(r"\.0$", "", regex=True)
canc["Revenue"] = (canc["Quantity"] * canc["UnitPrice"]).round(2)

cust = df[df["CustomerID"].notna()]
record("Customer-level dataset", "Rows with a CustomerID.", 0, len(cust))

# checks
assert (df["Quantity"] > 0).all() and (df["UnitPrice"] > 0).all()
assert df.duplicated().sum() == 0
record("Integrity checks", "Positive quantity and price, no duplicates: passed.", 0, len(df))

df.to_csv(CLEAN / "sales_all.csv", index=False)
cust.to_csv(CLEAN / "sales_customers.csv", index=False)
canc.to_csv(CLEAN / "cancellations.csv", index=False)
pd.DataFrame(log).to_csv(DOCS / "cleaning_log.csv", index=False)

print(f"raw {n0:,} -> sales_all {len(df):,} -> with customer {len(cust):,} | cancellations {len(canc):,}")
print(f"customers {cust['CustomerID'].nunique():,} | invoices {df['InvoiceNo'].nunique():,} | revenue {df['Revenue'].sum():,.0f}")
print(df["InvoiceDate"].min(), df["InvoiceDate"].max())
print(pd.DataFrame(log)[["Step", "Issue found", "Rows affected"]].to_string(index=False, max_colwidth=70))
