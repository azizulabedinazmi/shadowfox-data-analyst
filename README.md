# ShadowFox Data Analyst Internship

Submission repository for the ShadowFox Data Analyst Internship task list
(Beginner, Intermediate and Advanced levels).

**Author:** [[Azizul Abedin Azmi](https://www.facebook.com/azizul.abedin.azmi)]
**Contact:** [[LinkedIn](https://www.linkedin.com/in/azizulabedin/)]

## Progress

| Level | Dataset | Tools | Status |
|---|---|---|---|
| [01 Beginner](01-beginner/) | Superstore sales | Excel, Python (cleaning) | In progress: data cleaned, KPIs defined, dashboard to build |
| [02 Intermediate](02-intermediate/) | [Dataset name] | [Tools] | Not started |
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
