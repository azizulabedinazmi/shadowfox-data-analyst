# Level 1 (Beginner): Superstore Sales Analysis

## Objective

Clean a small retail sales dataset, define the key business metrics, and build a
spreadsheet dashboard that shows how sales and profit move over time, by
category, by region and by product.

## Status

- [x] Raw data profiled and cleaned (`scripts/clean_superstore.py`)
- [x] Cleaning log written (`docs/cleaning_log.csv`, "Cleaning Log" sheet)
- [x] KPIs defined with live formulas ("KPI Definitions" sheet)
- [x] Monthly trend table and seasonality grid ("Monthly Trend" sheet)
- [x] Dashboard v1: KPI cards, monthly trend, category and region charts ("Dashboard" sheet)
- [x] Sub-category profit and margin, top and bottom 10 products ("Product Analysis" sheet)
- [x] Discount analysis ("Discount Analysis" sheet)
- [ ] Year / Region / Segment filters (slicers), see "Adding slicers" below
- [ ] Insights and recommendations (sections below)

## Dataset

| | |
|---|---|
| Name | Sample Superstore |
| What it is | Order lines from a US office-supplies retailer, plus a returns list and regional managers |
| Source | https://github.com/leonism/sample-superstore (`data/superstore.csv`) |
| Period | 3 Jan 2015 to 30 Dec 2018 |
| Size after cleaning | 9,993 order lines, 5,009 orders, 793 customers, 1,862 product IDs |
| Grain | One row = one product line within one order |

The raw file is a single CSV, but it contains three tables stacked together
(Orders, People, Returns). The cleaning script splits them.

## Files

```
01-beginner/
├── README.md
├── superstore_beginner.xlsx     Workbook: Dashboard, Monthly Trend, Product Analysis, Discount Analysis, KPI Definitions, Data, Product Summary, Returns, Regional Managers, Cleaning Log
├── data/
│   ├── raw/superstore_raw.csv   Untouched download
│   └── clean/                   superstore_clean.csv, returns.csv, regional_managers.csv
├── docs/cleaning_log.csv        One row per cleaning step
└── scripts/
    ├── clean_superstore.py      raw -> clean CSVs + cleaning log
    ├── build_workbook.py        clean CSVs -> Excel workbook with formulas
    ├── add_analysis.py          adds Product Analysis, Product Summary, Discount Analysis
    └── add_dashboard.py         adds Monthly Trend and Dashboard (all charts)
```

## Step-by-step: run the Python scripts

Run the commands below from a terminal. The commands are written for Windows
PowerShell, but the Python commands also work in Command Prompt, macOS and
Linux.

### 1. Open the project folder

From the repository root:

```powershell
cd "d:\ShadowFox Intership\shadowfox-data-analyst"
cd "01-beginner"
```

Confirm that the input file exists before continuing:

```powershell
Test-Path "data\raw\superstore_raw.csv"
```

The command should return `True`. Do not rename or move the raw CSV unless you
also update the path in `scripts/clean_superstore.py`.

### 2. Install the Python packages

Run this once from the repository root (not from `01-beginner`):

```powershell
cd "d:\ShadowFox Intership\shadowfox-data-analyst"
py -m pip install -r requirements.txt
cd "01-beginner"
```

The scripts require Python 3, `pandas`, and `openpyxl`. If `py` is not
available on your computer, use `python` instead:

```powershell
python -m pip install -r ..\requirements.txt
```

### 3. Clean and split the raw data

```powershell
python scripts\clean_superstore.py
```

This script reads:

- `data\raw\superstore_raw.csv`

It creates or replaces:

- `data\clean\superstore_clean.csv` - cleaned order lines
- `data\clean\returns.csv` - one row per returned order
- `data\clean\regional_managers.csv` - one manager per region
- `docs\cleaning_log.csv` - every cleaning action and validation check

Check the printed row counts and sales/profit totals. The script should finish
without an assertion error.

### 4. Build the base Excel workbook

```powershell
python scripts\build_workbook.py
```

This script reads the three cleaned CSV files and the cleaning log, then
creates or replaces:

- `superstore_beginner.xlsx`

At this stage the workbook contains the `Data`, `Returns`, `Regional Managers`,
`Cleaning Log`, and `KPI Definitions` sheets. Do not run the later scripts
before this step, because they open this workbook.

### 5. Add product and discount analysis

```powershell
python scripts\add_analysis.py
```

This script opens `superstore_beginner.xlsx` and adds or replaces:

- `Product Summary`
- `Product Analysis`
- `Discount Analysis`
- `Data!AD: Discount Band`

It must run after `build_workbook.py`.

### 6. Add the monthly trend and dashboard

```powershell
python scripts\add_dashboard.py
```

This script opens the workbook produced by the previous step and adds or
replaces:

- `Monthly Trend`
- `Dashboard`

It must run last. Although it can open a workbook made by
`build_workbook.py`, its validation checks expect the `Product Analysis` and
`Discount Analysis` sheets from step 5.

### 7. Open and recalculate the workbook

Open `superstore_beginner.xlsx` in Excel or LibreOffice. If the cells show
formulas instead of values, force a full recalculation:

- **Excel:** `Formulas` > `Calculation Options` > `Automatic`, then press
 `Ctrl+Alt+F9`.
- **LibreOffice Calc:** open the file and use `Data` > `Calculate` >
 `Recalculate Hard`.

The final workbook should contain the dashboard plus the `Monthly Trend`,
`Product Analysis`, `Discount Analysis`, `KPI Definitions`, `Data`, `Returns`,
`Regional Managers`, and `Cleaning Log` sheets.

### Optional: create a dashboard preview

To create a smaller preview workbook with the data sheets hidden, run this
from `01-beginner` after step 6:

```powershell
$env:PREVIEW = "1"
python scripts\add_dashboard.py
Remove-Item Env:\PREVIEW
```

This creates `superstore_preview.xlsx` and does not replace the normal
`superstore_beginner.xlsx`.

### Rebuild everything from scratch

Run all four scripts in this exact order:

```powershell
python scripts\clean_superstore.py
python scripts\build_workbook.py
python scripts\add_analysis.py
python scripts\add_dashboard.py
```

The scripts overwrite the generated CSVs, cleaning log, and workbook. The raw
file in `data\raw` is not modified.

## Data dictionary

| Column | Meaning |
|---|---|
| Row ID | Line number in the original file |
| Order ID | Order reference; one order can have several lines |
| Order Date / Ship Date | Dates the order was placed and shipped |
| Ship Mode | Standard Class, Second Class, First Class or Same Day |
| Customer ID / Customer Name | Customer identifiers |
| Segment | Consumer, Corporate or Home Office |
| Country / City / State / Postal Code | Delivery location |
| Region | West, East, Central or South |
| Product ID / Product Name | Product identifiers (see known issue below) |
| Category / Sub-Category | Furniture, Office Supplies or Technology, and 17 sub-categories |
| Sales | Line revenue in USD, after discount |
| Quantity | Units on the line |
| Discount | Discount rate applied (0 to 0.8) |
| Profit | Line profit in USD; negative means a loss |

Columns added in the workbook (blue headers on the Data sheet, all formulas):

| Column | Formula idea |
|---|---|
| Order Year, Order Month, Year-Month, Quarter | Taken from Order Date |
| Ship Days | Ship Date minus Order Date |
| Line Profit Margin | Profit / Sales for that line |
| Is Returned | 1 if the Order ID appears on the Returns sheet |
| First Line of Order | 1 on the first line of each order, so orders can be counted without double counting |
| Discount Band | 0%, 1-20%, 21-40% or 41%+. The limits are inputs on the Discount Analysis sheet |

## Cleaning summary

Full detail with row counts is in `docs/cleaning_log.csv`.

| # | Issue | Action |
|---|---|---|
| 1 | 806 non-order rows at the bottom of the file (People and Returns tabs exported into the same CSV) | Split into three tables |
| 2 | Returns list has 800 entries but 296 distinct orders | Kept one row per returned order |
| 3 | Dates and numbers stored as text | Converted to dates and numbers |
| 4 | 11 rows missing Postal Code, all Burlington, Vermont | Filled with 05401 (outside fact, not used in any KPI) |
| 5 | Postal Code loses leading zeros when read as a number | Stored as 5-character text |
| 6 | 1 order line identical to another except Row ID (Row ID 3407) | Removed |
| 7 | 7 integrity checks (dates in order, positive sales and quantity, valid discounts, State to Region, Customer ID to name, managers cover all regions) | All passed |

Known issues left in place on purpose:

- **32 Product IDs are used for two different product names.** Product-level
  analysis therefore uses Product Name, not Product ID.
- **Extreme losses and 80% discounts are kept.** The biggest single-line loss
  is -$6,600 on a Machines item at 70% discount. These look like real
  discounting decisions, so they belong in the analysis, not in the bin.

## KPI definitions

| # | KPI | Calculation | Value |
|---|---|---|---|
| 1 | Total Sales | Sum of Sales | $2,296,919 |
| 2 | Total Profit | Sum of Profit | $286,409 |
| 3 | Profit Margin | Total Profit / Total Sales | 12.5% |
| 4 | Total Orders | Count of distinct Order IDs | 5,009 |
| 5 | Units Sold | Sum of Quantity | 37,871 |
| 6 | Average Order Value | Total Sales / Total Orders | $458.56 |
| 7 | Average Discount | Mean of Discount across lines | 15.6% |
| 8 | Return Rate (orders) | Returned orders / Total Orders | 5.9% |
| 9 | Returned Sales Share | Sales on returned orders / Total Sales | 7.9% |
| 10 | Average Ship Days | Mean of Ship Date minus Order Date | 4.0 |
| 11 | Loss-making Lines | Lines with Profit < 0 / all lines | 18.7% |
| 12 | Sales Growth | Sales latest year / prior year - 1 | 20.4% (2018 vs 2017) |

**Why these:** Sales, Profit and Margin say how big and how healthy the business
is. Orders and Average Order Value separate "more customers" from "bigger
baskets". Discount, Returns and Loss-making Lines are the likely causes of weak
profit. Growth gives the trend.

**Headline cards on the dashboard:** Total Sales, Total Profit, Profit Margin,
Total Orders, Average Order Value, Return Rate, Sales Growth. The rest are
supporting detail.

**Treatment of returns:** headline Sales and Profit include returned orders
(gross view). KPI 9 shows how much of Sales sits on returned orders. The
dataset does not say whether Profit was reversed on returns, so no adjustment
is made.

## Dashboard

[Insert screenshot of the dashboard sheet here]

Current version has seven KPI cards and five sections: sales trend, category and region,
sub-category performance, top and bottom 10 products, and discounting. The Monthly Trend
sheet also has a calendar-month by year grid for seasonality.

### Adding slicers (Year / Region / Segment)

Slicers only work with a PivotTable, so they are a separate step from the formula tables.

1. On the Data sheet, click any cell, then Insert > PivotTable. Put it on a new sheet.
2. Drag Order Year to Rows, and Sales and Profit to Values.
3. Click the PivotTable, then PivotTable Analyze > Insert Slicer. Tick Order Year, Region, Segment.
4. Insert > PivotChart for the sales and profit view. Slicers now filter it.
5. To drive several PivotTables with one slicer, right-click the slicer > Report Connections.

## Key insights

Evidence from the workbook. Check each number on its sheet, then put the reasoning
into your own words.

1. **Discounts above 20% lose money.** Lines with no discount have a 29.5% margin,
   1-20% gives 11.9%, 21-40% gives -15.3% and 41%+ gives -77.4%. Those two heaviest
   bands are 14% of order lines and together lost about $135K, against $286K total profit.
   (Discount Analysis, table 1.)
2. **The loss sits in Furniture, and mostly in two sub-categories.** Furniture earns
   a 2.5% margin against about 17% for the other categories. Tables (-$17.7K, 26% average
   discount) and Bookcases (-$3.5K) lose money. Machines sells $189K at a 1.8% margin
   with a 31% average discount. (Product Analysis.)
3. **Sales are seasonal, but discounts do not explain it.** September, November and
   December carry about 43% of sales, and January and February about 7%. Average
   discount barely changes by calendar month (14.6% to 16.5%), and across the 12
   months it has almost no link to margin (correlation -0.12). Across all 48 individual
   months the link is moderate (-0.49): months with deeper average discounts tend to
   have lower margins, which is association, not proof of cause. (Discount Analysis, table 4.)
4. **A few products drive big losses.** The worst is the Cubify CubeX 3D Printer
   (Double Head) at -$8.9K. The top product is the Canon imageCLASS 2200 copier at
   +$25.2K. (Product Analysis, tables 3 and 4.)
5. **Returns are modest but real.** 5.9% of orders and 7.9% of sales sit on returned orders.

Rewrite these in your own words and add what you would check next. Do not paste
them in unchanged, because you will need to explain them on video.

## Recommendations

[2-3 actions tied to the insights above]

## Limitations

- Discount findings show association in this dataset. They do not prove that cutting discounts would raise profit, because the products and customers that get deep discounts may differ.
- Single retailer, 2015-2018 only; no cost, marketing or customer-contact data.
- Profit effect of returns is unknown (see KPI treatment above).
- Postal Code fill for Burlington, VT is an outside assumption.

## Tools

Excel (pivot tables, charts, formulas), Python 3 with pandas and openpyxl
(cleaning and workbook build).
