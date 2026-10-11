# Level 2 (Intermediate): Customer and Revenue Analysis, Online Retail

**Azizul Abedin Azmi**  
[azmi00121@gmail.com](mailto:azmi00121@gmail.com) | [GitHub](https://github.com/azizulabedinazmi) | [Portfolio](https://azizulabedinazmi.is-a.dev/)

## Business question

Where does revenue come from, how well does the company keep its customers, and
which actions would grow revenue most?

## Status

- [x] Dataset chosen and documented
- [x] Data cleaned and prepared (`scripts/clean_online_retail.py`, `docs/cleaning_log.csv`)
- [x] Exploratory analysis
- [x] Customer, segment (RFM), product and country analysis
- [x] Trend, seasonality and cohort retention analysis
- [x] Charts and written reports (`report/Online_Retail_Customer_Analysis_Report.docx`, `report/intermediate_report.pdf`)
- [x] Recommendations
- [x] Author details added to the reports and README

## Dataset

| | |
|---|---|
| Name | Online Retail (UCI Machine Learning Repository) |
| Source | Public GitHub mirror: https://github.com/databricks/Spark-The-Definitive-Guide (`data/retail-data/all/online-retail-dataset.csv`). Original: https://archive.ics.uci.edu/dataset/352/online+retail |
| Period | 1 Dec 2010 to 9 Dec 2011 (December 2011 is a partial month) |
| Size | 541,909 raw lines; 522,537 after cleaning; 4,333 identified customers; 3,908 products; 38 countries |
| Grain | One row = one product line on one invoice |
| Why this dataset | Has customer IDs and invoice dates, so it supports repeat purchase, retention, segmentation, revenue concentration, seasonality, product and country analysis |

## Files

```
02-intermediate/
├── README.md
├── data/
│   ├── raw/online_retail_raw.csv         untouched download
│   └── clean/                            created by the cleaning script
├── docs/cleaning_log.csv                 every cleaning step with row counts
├── scripts/clean_online_retail.py        raw -> clean CSVs + cleaning log
├── analysis/
│   ├── analyze_online_retail.py          metrics, tables, charts
│   ├── build_report.py                   builds the Word report
│   ├── metrics.json                      every headline number
│   └── analysis_tables.xlsx              the table behind each chart
└── report/
    ├── intermediate_report.pdf
    ├── intermediate_report.tex
    └── charts/*.png
```

## How to reproduce

```bash
pip install pandas openpyxl matplotlib python-docx
cd 02-intermediate
python scripts/clean_online_retail.py
python analysis/analyze_online_retail.py
python analysis/build_report.py
```

To compile the complete visual LaTeX report after the analysis:

```bash
pdflatex -interaction=nonstopmode -halt-on-error -output-directory report report/intermediate_report.tex
pdflatex -interaction=nonstopmode -halt-on-error -output-directory report report/intermediate_report.tex
```

## Data cleaning summary

Details and row counts: `docs/cleaning_log.csv`.

| Issue | Action | Rows |
|---|---|---|
| Exact duplicate lines | Removed | 5,268 |
| Cancellation invoices (start with "C") | Moved to their own file; revenue is completed sales only | 9,251 |
| Non-product lines (postage, manual, bank charges, Amazon fees, vouchers) | Removed | 2,356 |
| Quantity or price of zero or below on normal invoices | Removed | 2,493 |
| Product descriptions with several spellings | One description per StockCode | 6,784 |
| Two orders of 70,000+ units cancelled in full by the same customer | Removed sale and cancellation. One would otherwise rank as the #2 product while earning nothing | 2 |
| Missing CustomerID (about 25% of lines) | Kept for revenue and product analysis; excluded from customer analysis | 131,388 |

## Method

- **Revenue** = Quantity x UnitPrice on completed sales.
- **Repeat rate** = customers with 2 or more orders / all identified customers.
- **Concentration** = share of revenue from the top 1%, 10% and 20% of customers.
- **Cohort retention** = share of customers first seen in a month who order again N months later. The December 2010 cohort is excluded from averages (data starts then, so they are not truly new), and December 2011 cells are blanked (partial month).
- **RFM** = Recency, Frequency and Monetary scores (1 to 5, by quintile), grouped into six segments.

## Key findings

| # | Finding | Evidence |
|---|---|---|
| 1 | Revenue is highly concentrated | Top 10% of customers = 60% of revenue; top 20% = 74%; bottom 50% = 8% |
| 2 | Champions carry the business | 912 customers (21%) produce 66% of revenue, about 11 orders each |
| 3 | Repeat buying is the business | 65% of customers reorder and produce 94% of revenue |
| 4 | Most new customers do not return | About 20% order again next month; about 25% are active six months later |
| 5 | Strong Q4 seasonality | Sep to Nov = 38% of revenue; November is 2.2x a normal month |
| 6 | Recoverable lapsed customers | 641 At Risk customers spent £734K before going quiet for about 154 days |
| 7 | Export markets are thin in places | EIRE revenue (£271K) comes from 3 customers; Germany and France have about 90 each |
| 8 | Orders are placed in working hours | 75% of revenue between 10:00 and 15:59; no Saturday orders recorded |
| 9 | Cancellations are low | 2.3% of revenue |

## Recommendations

1. Protect the Champions with account owners and early warning on order gaps.
2. Win back lapsed high-value customers with personal outreach before discounts.
3. Get a second order from new customers with a follow-up after 2 to 3 weeks (test against a control group).
4. Build the Q4 plan (stock, staff, campaigns) from August.
5. Send communications Tuesday to Thursday mornings.
6. Key-account management for EIRE, the Netherlands and Australia; market-level marketing for Germany and France.

Full reasoning, charts and measurement ideas are in the report.

## Limitations

- One year, one retailer. Seasonality cannot be separated from growth.
- About 25% of lines have no CustomerID. Customer findings cover identified customers (85% of revenue).
- No cost or profit data, so all value figures are revenue.
- No customer type, marketing or price data. The explanations for the patterns are inferences and are not tested.
- RFM boundaries are quintile-based and somewhat arbitrary.

## Tools

Python 3 (pandas, matplotlib, openpyxl, python-docx).
