# Level 3 (Advanced): HR Attrition Executive Dashboard

## Audience and purpose

HR leadership deciding where to focus retention effort. The dashboard answers three
questions: how big is the attrition problem, what is driving it, and which current
employees should be spoken to first.

## Status

- [x] Dataset chosen, downloaded and checked
- [x] Data cleaned and transformed (`scripts/prepare_hr_data.py`, `docs/cleaning_log.csv`)
- [x] KPIs selected and defined
- [x] DAX measures, Power Query script and theme written (`powerbi/`)
- [x] Expected value for every measure computed (`docs/expected_values.csv`)
- [x] Three-page dashboard wireframes (`dashboard/`)
- [ ] **Build the dashboard in Power BI Desktop** and save `dashboard.pbix` (follow `docs/BUILD_GUIDE.md`)
- [ ] Check every card against `docs/expected_values.csv`
- [ ] Add screenshots to `screenshots/` and link them below
- [ ] Rewrite the insights in your own words

## Dataset

| | |
|---|---|
| Name | IBM HR Analytics Employee Attrition and Performance |
| Source | https://github.com/IBM/employee-attrition-aif360 (`data/emp_attrition.csv`). A second public copy has an identical SHA-256 hash. |
| Size | 1,470 employees, 35 columns |
| Grain | One row = one employee |
| Outcome field | `Attrition` (Yes/No). 237 left, 1,233 stayed: 16.1% |
| Nature of the data | The dataset is widely described as fictional, created by IBM data scientists. Findings describe this dataset, not a real company. Confirm this on the source page before stating it in your video. |
| Time | No dates. It is a single snapshot, so there is no attrition trend over time. Tenure is used as the time view. |

## Files

```
03-advanced/
├── README.md
├── dashboard.pbix              <- you create this (see BUILD_GUIDE)
├── data/
│   ├── raw/ibm_hr_attrition_raw.csv
│   └── clean/hr_employees.csv  59 columns, load this into Power BI
├── scripts/
│   ├── prepare_hr_data.py      raw -> clean CSV + cleaning log + data dictionary
│   ├── expected_values.py      pandas value for every DAX measure
│   └── make_wireframes.py      draws the three page wireframes
├── powerbi/
│   ├── measures.dax            all measures
│   ├── power_query.m           raw -> model in Power Query
│   └── theme.json              colour theme
├── dashboard/                  wireframe_1_summary / _2_drivers / _3_watchlist .png
├── docs/
│   ├── BUILD_GUIDE.md          step by step build instructions
│   ├── VIDEO_OUTLINE.md        5 minute video plan
│   ├── cleaning_log.csv
│   ├── data_dictionary.csv
│   └── expected_values.csv     what each measure should show
├── analysis/metrics.json
└── screenshots/                add after building
```

## Data cleaning and transformation

The raw file is already clean: no missing values, no duplicates, no inconsistent text. The
work is therefore mostly **transformation**. Full detail: `docs/cleaning_log.csv`.

| # | Issue or need | Action | Where |
|---|---|---|---|
| 1 | Byte-order mark corrupts first column name | Read as UTF-8 with BOM removed | Python / Power Query |
| 2 | Three columns have one value for everyone (EmployeeCount, Over18, StandardHours) | Dropped | Both |
| 3 | Attrition stored as Yes/No | Added `Left` (1/0) for rates | Both |
| 4 | Ratings stored as numbers 1 to 4 | Added text labels (Low to Very High, etc.) | Both |
| 5 | Age, tenure, income, distance, time with manager too granular | Added bands with sort-order columns | Both |
| 6 | Pay columns: DailyRate, HourlyRate, MonthlyRate are unrelated to MonthlyIncome (correlation 0.03, -0.02, 0.01) | Kept but not used. MonthlyIncome is the pay measure | Decision |
| 7 | Cost questions need a yearly figure | `AnnualIncome` = MonthlyIncome x 12 | Both |
| 8 | Need a way to prioritise current staff | Six yes/no risk flags and `RiskFlagCount` (see below) | Both |
| 9 | Logic checks: tenure not more than career length, years in role and with manager not more than tenure, age consistent | All passed | Python |

## KPI selection

| KPI | Definition | Why it is on the dashboard |
|---|---|---|
| Attrition Rate | Leavers / headcount | The core measure. Always shown against the company rate |
| Headcount, Leavers | Counts | Size of each group, so small groups are not over-read |
| Overtime Multiple | Attrition rate with overtime / without | Overtime is the strongest single driver, and the one management controls directly |
| Avg Tenure of Leavers | Mean years at company among leavers | Shows how early people leave |
| Early Leaver Share | Leavers with 2 years or less / all leavers | Points to onboarding and early-career retention |
| Annual Salary of Leavers | Sum of annualised pay of leavers | Puts a size on what is lost. Currency not stated in the data |
| Estimated Cost of Attrition | Salary of leavers x replacement cost % | Replacement cost % is a **what-if input and an assumption**: set it to your organisation's figure |
| At-Risk Employees | Current staff with N or more risk flags | Turns analysis into a list of people to talk to |
| Role Attrition Rate | Base rate for the employee's role | Context for the watchlist |

## Dashboard design

Wireframes in `dashboard/`. Build steps in `docs/BUILD_GUIDE.md`.

**Page 1, Executive Summary:** KPI cards, attrition by job role, tenure, department and overtime.
**Page 2, What Drives It:** overtime, stock options, travel, income, a role-by-overtime matrix,
satisfaction ratings, and a decomposition tree for drilling from company to department to role.
**Page 3, Retention Watchlist:** at-risk count and cost, attrition by flag count, and a table of
current employees to speak to first. Drill-through from any role.

**Interactivity:** slicers on every page (department and role synced), decomposition tree,
drill-through, two what-if parameters (replacement cost, risk threshold), tooltips with group size.

## Screenshots

[Add after building: `screenshots/page1.png`, `page2.png`, `page3.png`]

## Key insights

Evidence from the data. Check each against the dashboard, then rewrite in your own words.

1. **Overtime is the biggest driver.** 30.5% of employees working overtime left, against 10.4%
   of those who do not (2.9 times). Overtime workers are 28% of staff but 54% of leavers.
   The gap holds inside groups that would otherwise explain it: among entry-level staff it is
   52.6% vs 15.8%, among single employees 49.6% vs 16.2%.
2. **Attrition is concentrated in a few roles.** Sales Representatives (39.8%, 83 people),
   Laboratory Technicians (23.9%, 259) and Human Resources (23.1%, 52) are well above the
   16.1% company rate. Research Directors (2.5%) and Managers (4.9%) are very low. Overtime
   makes the gap larger: Laboratory Technicians on overtime leave at 50%, Research
   Scientists at 34%.
3. **People leave early.** 34.9% of employees in their first year left, and 43% of all
   leavers had 2 years or less, though that group is 23% of staff. Employees 25 or younger
   leave at 35.8%.
4. **Lower pay, lower level, no stock options go together with leaving.** Employees earning up
   to 3K a month leave at 28.6%; those with no stock options at 24.4% against 9.4% and 7.6% for
   stock option levels 1 and 2. These overlap heavily (income and job level correlate at 0.95, and younger
   staff are mostly entry level with short tenure), so the data cannot say which one matters
   most.
5. **Frequent travel and low satisfaction add risk.** Frequent travellers leave at 24.9%
   (non-travel 8.0%). Employees who rate work-life balance 1 leave at 31.2% (80 people).
6. **Some things do not matter here.** Performance rating (16.1% vs 16.4%, p = 0.99), last
   salary increase percentage (p = 0.50), gender (p = 0.29) and education (p = 0.55) show
   no clear link with leaving. Because performance does not predict leaving, the company
   is losing high-rated people at the same rate as everyone else.
7. **A simple rule finds a high-risk group.** Employees with 4 or more of six risk flags left
   at 60%, against 5% for those with 0 or 1. 55 current employees are in that group, with
   about 3.3M in annual pay. This is measured on the same data used to design the flags,
   so the real accuracy will be lower.

## Recommendations

| Decision | Evidence | Suggested action |
|---|---|---|
| Review overtime in the roles where it is costly | Overtime attrition: Sales Rep 67% (24 people), Lab Tech 50%, Research Scientist 34%, Sales Exec 33% | Check workload and staffing in those roles; set an overtime limit or rotate it. Track attrition among overtime staff as the measure |
| Improve the first two years | 43% of leavers had 2 years or less | Structured onboarding, 90-day and 12-month check-ins, a named buddy or manager contact |
| Look closely at Sales Representatives and Laboratory Technicians | 39.8% and 23.9% attrition | Role review: pay progression, workload, career path. Talk to current staff and to leavers |
| Pilot incentives for entry-level staff without stock options | 37% attrition for level 1 with none vs 17% with some | Small pilot with a comparison group. This is an association, so test before rolling out |
| Reduce frequent-travel load where possible | 24.9% vs 8.0% for non-travel | Review who needs to travel and how often |
| Talk to the 55 highest-risk current employees | 60% attrition among 4+ flags | Manager conversations, starting with entry-level and overtime staff. Note that a flagged Research Director is a lower concern than a flagged Sales Representative because the role base rate differs |

## How to open

Power BI Desktop (free, Windows). Open `dashboard.pbix`. To refresh, run
`python scripts/prepare_hr_data.py` and use Home > Refresh. If Power BI cannot find the data,
use Transform data > Data source settings > Change source and point to `data/clean/hr_employees.csv`.

## Limitations

- Fictional dataset, one snapshot, no dates. No attrition trend, and no way to know whether
  people left voluntarily or were dismissed.
- Many strong drivers overlap (age, tenure, level, income). The dashboard shows association,
  not cause, and cannot say which factor to change first.
- Several roles are small (Human Resources 52, Sales Representative 83), and
  role-by-overtime cells can have fewer than 30 people. The tooltips show group size.
- The risk flags were chosen after looking at this same data. One flag (entry level) was added
  after a first version over-flagged senior staff. The rule needs testing on new data.
- No currency is given, so money figures are in the dataset's own units. The replacement
  cost % is an assumption set by the user.
- The DAX and Power Query code has not been run in Power BI Desktop by its author. Check every
  card against `docs/expected_values.csv`.

## Tools

Python (pandas, matplotlib) for preparation and checking. Power BI Desktop (Power Query, DAX).
