# Build guide: HR Attrition dashboard in Power BI

Everything you need is already prepared: cleaned data, the DAX measures, a Power Query
script, a colour theme, three page wireframes and a table of the values each number
should show. What is left is the part that has to happen inside Power BI Desktop:
loading the data, pasting the measures, and placing the visuals. Allow 3 to 4 hours.

The Power BI file (`.pbix`) cannot be created outside Power BI Desktop, so it is not in
this repository until you build and save it.

**Software:** Power BI Desktop (free from the Microsoft Store or Microsoft's download
page). It runs on Windows only. If you are on a Mac, the task also allows Tableau;
Tableau Public is free and runs on Mac. The CSV and the wireframes work for either, but
`measures.dax` and `power_query.m` are Power BI specific and would need rewriting as
Tableau calculated fields.

## Step 1. Load the data

Easiest: **Home > Get data > Text/CSV**, choose `data/clean/hr_employees.csv`, then
**Load**. Name the table `HR` (the measures assume this name).

To do the transformation inside Power BI instead (this shows more skill and is worth
doing for the video): **Home > Transform data > New Source > Blank Query > Advanced
Editor**, paste `powerbi/power_query.m`, change the `FilePath` line to point to
`data/raw/ibm_hr_attrition_raw.csv`, click Done, rename the query `HR`, then **Close &
Apply**.

Check: 1,470 rows. Attrition: Yes = 237, No = 1,233.

## Step 2. Set up the model

1. In **Data view**, click each column and check its data type. Numbers should be whole
   numbers, text columns text.
2. **Sort bands correctly.** Select `AgeBand`, then Column tools > Sort by column >
   `AgeBandSort`. Repeat for `TenureBand` (TenureBandSort), `IncomeBand`
   (IncomeBandSort), `DistanceBand` (DistanceBandSort) and `ManagerTenureBand`
   (ManagerTenureBandSort). Without this, bands sort alphabetically ("11+ yrs" before
   "2 yrs").
3. For each of the numeric columns you will not sum or average (EmployeeNumber, the
   ratings, the Sort columns, the Flag columns), set **Summarization** to **Don't
   summarize** so Power BI does not turn them into sums.
4. Hide columns you will not use in visuals (DailyRate, HourlyRate, MonthlyRate, the Sort
   columns, the Flag columns). Right-click > Hide in report view.

## Step 3. Add the measures

1. **Home > Enter data**, create a table with one column and no rows of data, name it
   `_Measures`, and load it.
2. Select `_Measures`, then **Modeling > New measure**. Paste the measures from
   `powerbi/measures.dax` **one at a time**. Each measure starts after its name and `=`.
3. Create the two what-if parameters first (the file explains how), because other
   measures reference them:
   - **Modeling > New parameter > Numeric range**: name `Replacement Cost %`, minimum 25,
     maximum 200, increment 5, default 50, tick "Add slicer to this page".
   - **Modeling > New parameter > Numeric range**: name `Risk Threshold`, minimum 1,
     maximum 6, increment 1, default 4, tick "Add slicer to this page".
4. Set formats (Measure tools > Format): rates as percentage with 1 decimal; Headcount,
   Leavers and counts as whole numbers; `Overtime Multiple` custom `0.0"x"`;
   `Attrition vs Company (pp)` custom `+0.0" pp";-0.0" pp"`; cost measures as whole
   numbers with thousands separators.

## Step 4. Check the numbers before building any visual

Put a **Card** on a blank page for each measure and compare with `docs/expected_values.csv`.
Do this now, not at the end, because a wrong measure will make every chart wrong.

| Measure | Should show |
|---|---|
| Headcount | 1,470 |
| Leavers | 237 |
| Attrition Rate | 16.1% |
| Overtime Attrition Rate | 30.5% |
| No Overtime Attrition Rate | 10.4% |
| Overtime Multiple | 2.9x |
| Avg Tenure Leavers (yrs) | 5.1 |
| Avg Tenure Stayers (yrs) | 7.4 |
| Annual Salary of Leavers | 13,614,492 |
| Early Leaver Share | 43.0% |
| At-Risk Employees (threshold 4) | 55 |
| Estimated Cost of Attrition (50%) | 6,807,246 |

Then add a table visual with `JobRole` and `Attrition Rate` and compare with the
Job Role rows in the expected values file (Sales Representative 39.8%, Research Director
2.5%, and so on). If a number differs, fix the measure before continuing.

## Step 5. Apply the theme

**View > Themes > Browse for themes**, choose `powerbi/theme.json`.

## Step 6. Build page 1: Executive Summary

Use `dashboard/wireframe_1_summary.png` as the layout. Page size: 16:9 (default).

| Visual | Fields | Notes |
|---|---|---|
| Six Cards | Headcount, Leavers, Attrition Rate, Overtime Multiple, Avg Tenure Leavers (yrs), Annual Salary of Leavers | Row along the top |
| Clustered bar chart | Axis: JobRole. Values: Attrition Rate | Sort by Attrition Rate descending. Colour: Format > Bars > Colors > fx > Field value > `Attrition Colour` |
| Clustered column chart | Axis: TenureBand. Values: Attrition Rate | Constant line at the company rate: Analytics pane > Constant line, or add `Company Attrition Rate` as a second value shown as a line |
| Clustered bar chart | Axis: Department. Values: Attrition Rate | |
| Clustered column chart | Axis: OverTime. Values: Attrition Rate | |
| Slicers | Department, JobRole, Gender, MaritalStatus, AgeBand, BusinessTravel | Use dropdown style for the long ones |
| Text box or Card | `Selection Summary` | Dynamic subtitle that changes as slicers change |

Show data labels, and add `Headcount` to each chart's **Tooltips** field so the group size
appears on hover. Add `Small Group Warning` to tooltips as well.

## Step 7. Build page 2: What Drives It

Layout: `dashboard/wireframe_2_drivers.png`.

| Visual | Fields |
|---|---|
| Column charts (x4) | Axis: OverTime / StockOptionLevel / BusinessTravel / IncomeBand. Values: Attrition Rate |
| Matrix | Rows: JobRole. Columns: OverTime. Values: Attrition Rate. Format > Cell elements > Background colour > Gradient (white to red) |
| Bar chart | Three satisfaction fields. Simplest route: three small charts of Attrition Rate by `JobSatisfactionLabel`, `EnvironmentSatisfactionLabel`, `WorkLifeBalanceLabel` |
| **Decomposition tree** | Analyze: Attrition Rate. Explain by: Department, JobRole, OverTime, TenureBand, MaritalStatus. This is a built-in visual (Visualizations pane). It lets the reader click down from company to department to role |
| Slicers | Department, JobRole, OverTime, MaritalStatus, IncomeBand, JobLevel |

Under **View > Sync slicers**, sync the Department and JobRole slicers across all pages.

## Step 8. Build page 3: Retention Watchlist

Layout: `dashboard/wireframe_3_watchlist.png`.

| Visual | Fields |
|---|---|
| Cards (x4) | At-Risk Employees, At-Risk Annual Salary, At-Risk Cost if Lost, and a rate card for the 4+ flag group |
| Column chart | Axis: RiskFlagCount. Values: Attrition Rate |
| Table | EmployeeNumber, JobRole, Department, YearsAtCompany, MonthlyIncome, RiskFlagCount, Role Attrition Rate. Filter on this visual: Attrition = No, RiskFlagCount >= the threshold (use a visual-level filter, or filter RiskFlagCount is greater than or equal to 4) |
| Slicers | Risk Threshold, Replacement Cost %, Department, JobRole |

**Drill-through:** make a fourth page called `Role detail`. In its **Drill through** well add
`JobRole`. Put a few cards and the table on it. Now right-clicking a role on page 1 gives
**Drill through > Role detail**.

## Step 9. Interactivity checklist

The task asks for filters, slicers or drill-downs. Make sure the finished file has all of:

- [ ] Slicers on every page, with Department and Job Role synced
- [ ] Decomposition tree (page 2)
- [ ] Drill-through from role to detail page
- [ ] Two what-if parameters (replacement cost, risk threshold)
- [ ] Tooltips that show group size
- [ ] A dynamic subtitle (`Selection Summary`)
- [ ] Optional: a bookmark button "Reset filters" (Insert > Buttons > Bookmark)

## Step 10. Save and export

1. Save as `03-advanced/dashboard.pbix`.
2. **File > Export > Export to PDF** for a copy anyone can open.
3. Take one PNG screenshot per page into `03-advanced/screenshots/` and link them in the README.
4. If the `.pbix` is over 100 MB GitHub will refuse it. This one should be a few MB.

## Common problems

| Problem | Fix |
|---|---|
| Bands in the wrong order | Sort by column (Step 2) |
| Rates show as 0 or 1 instead of percent | Format the measure as percentage |
| A card shows a sum of ratings or IDs | Set Summarization to Don't summarize |
| `At-Risk Employees` errors | Create the `Risk Threshold` parameter before the measure |
| A slicer does not affect a card | Check Format > Edit interactions |
| `Attrition Colour` does nothing | Use Format style "Field value", not "Rules" |
| Overtime Multiple shows blank | The `OverTime` text must be exactly "Yes" and "No" |

## Before you record the video

You should be able to explain, in your own words: where the data came from and that it is
a fictional IBM dataset; what you changed and why; why you chose these KPIs; what each
page is for; and the three or four things the dashboard tells a decision maker to do.
