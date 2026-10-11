# ShadowFox Data Analyst Internship

Submission repository for the ShadowFox Data Analyst Internship task list
(Beginner, Intermediate and Advanced levels).

**Azizul Abedin Azmi**

<small>&nbsp; [azmi00121@gmail.com](mailto:azmi00121@gmail.com) &nbsp;|&nbsp; [GitHub](https://github.com/azizulabedinazmi) &nbsp;|&nbsp; [Portfolio](https://azizulabedinazmi.is-a.dev/)</small>

## Progress

| Level | Dataset | Tools | Status |
|---|---|---|---|
| [01 Beginner](01-beginner/) | Superstore sales | Excel, Python (cleaning) | Complete: dashboard, validation and visual report |
| [02 Intermediate](02-intermediate/) | Online Retail | Python, Excel, LaTeX, Word | Complete: customer, revenue and retention report |
| [03 Advanced](03-advanced/) | [IBM HR Analytics or other] | Power BI or Tableau | Not started |

## Repository layout

```
.
├── README.md
├── requirements.txt
├── 01-beginner/        Spreadsheet dashboard: sales performance
├── 02-intermediate/    Customer / revenue analysis with recommendations
└── 03-advanced/        Interactive executive dashboard
```

Each level folder has its own README covering the data source, cleaning steps,
KPIs, findings and how to reproduce the work.

## Beginner deliverables

- [Beginner visual PDF report](01-beginner/docs/beginner_report.pdf)
- [Beginner Excel dashboard](01-beginner/superstore_beginner.xlsx)
- [Beginner project README](01-beginner/README.md)

## Intermediate deliverables

- [Intermediate visual PDF report](02-intermediate/report/intermediate_report.pdf)
- [Intermediate Excel](02-intermediate\analysis\analysis_tables.xlsx)
- [Intermediate project README](02-intermediate/README.md)

## Running the Python scripts

```bash
pip install -r requirements.txt
cd 01-beginner
python scripts/clean_superstore.py
python scripts/build_workbook.py
```

## Notes

- Datasets are public sample datasets. Each level README states where the data
  came from.
- Everything in this repository is my own work unless a source is cited.
