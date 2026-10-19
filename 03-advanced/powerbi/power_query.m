// ============================================================================
// Power Query (M) script: raw IBM HR file -> model-ready table "HR"
//
// Use this if you want to do the transformation inside Power BI itself.
// Home > Transform data > New Source > Blank Query > Advanced Editor, paste this,
// change FilePath, and name the query HR.
//
// It reproduces scripts/prepare_hr_data.py. If you would rather skip it, load
// data/clean/hr_employees.csv directly (Get data > Text/CSV): same result.
//
// NOT run in Power BI by the author. After loading, check: 1,470 rows and
// 59 columns, and Attrition counts of Yes = 237, No = 1,233.
// ============================================================================
let
    FilePath = "C:\path\to\03-advanced\data\raw\ibm_hr_attrition_raw.csv",

    Source = Csv.Document(File.Contents(FilePath),
        [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),

    // The file starts with a byte-order mark. Make sure the first column is called "Age".
    FirstName = Table.ColumnNames(Promoted){0},
    Renamed = if FirstName = "Age" then Promoted
              else Table.RenameColumns(Promoted, {{FirstName, "Age"}}),

    // Text columns stay text, everything else becomes whole numbers
    TextCols = {"Attrition", "BusinessTravel", "Department", "EducationField", "Gender",
                "JobRole", "MaritalStatus", "Over18", "OverTime"},
    Typed = Table.TransformColumnTypes(Renamed,
        List.Transform(Table.ColumnNames(Renamed),
            each {_, if List.Contains(TextCols, _) then type text else Int64.Type})),

    // Columns that hold a single value for every employee
    NoConstants = Table.RemoveColumns(Typed, {"EmployeeCount", "Over18", "StandardHours"}),

    // Numeric flags
    AddLeft = Table.AddColumn(NoConstants, "Left", each if [Attrition] = "Yes" then 1 else 0, Int64.Type),
    AddOT = Table.AddColumn(AddLeft, "OvertimeFlag", each if [OverTime] = "Yes" then 1 else 0, Int64.Type),

    // Text labels for coded ratings
    Pick = (value as number, labels as list) as text => labels{value - 1},
    L1 = Table.AddColumn(AddOT, "EducationLabel",
        each Pick([Education], {"Below College", "College", "Bachelor", "Master", "Doctor"}), type text),
    L2 = Table.AddColumn(L1, "EnvironmentSatisfactionLabel",
        each Pick([EnvironmentSatisfaction], {"Low", "Medium", "High", "Very High"}), type text),
    L3 = Table.AddColumn(L2, "JobInvolvementLabel",
        each Pick([JobInvolvement], {"Low", "Medium", "High", "Very High"}), type text),
    L4 = Table.AddColumn(L3, "JobSatisfactionLabel",
        each Pick([JobSatisfaction], {"Low", "Medium", "High", "Very High"}), type text),
    L5 = Table.AddColumn(L4, "RelationshipSatisfactionLabel",
        each Pick([RelationshipSatisfaction], {"Low", "Medium", "High", "Very High"}), type text),
    L6 = Table.AddColumn(L5, "WorkLifeBalanceLabel",
        each Pick([WorkLifeBalance], {"Bad", "Good", "Better", "Best"}), type text),
    L7 = Table.AddColumn(L6, "PerformanceRatingLabel",
        each Pick([PerformanceRating], {"Low", "Good", "Excellent", "Outstanding"}), type text),

    // Bands (label and sort order)
    AgeBand = Table.AddColumn(L7, "AgeBand",
        each if [Age] <= 25 then "18-25" else if [Age] <= 35 then "26-35"
             else if [Age] <= 45 then "36-45" else "46+", type text),
    AgeSort = Table.AddColumn(AgeBand, "AgeBandSort",
        each if [Age] <= 25 then 1 else if [Age] <= 35 then 2 else if [Age] <= 45 then 3 else 4, Int64.Type),

    TenureBand = Table.AddColumn(AgeSort, "TenureBand",
        each if [YearsAtCompany] <= 1 then "0-1 yrs" else if [YearsAtCompany] <= 2 then "2 yrs"
             else if [YearsAtCompany] <= 5 then "3-5 yrs" else if [YearsAtCompany] <= 10 then "6-10 yrs"
             else "11+ yrs", type text),
    TenureSort = Table.AddColumn(TenureBand, "TenureBandSort",
        each if [YearsAtCompany] <= 1 then 1 else if [YearsAtCompany] <= 2 then 2
             else if [YearsAtCompany] <= 5 then 3 else if [YearsAtCompany] <= 10 then 4 else 5, Int64.Type),

    IncomeBand = Table.AddColumn(TenureSort, "IncomeBand",
        each if [MonthlyIncome] <= 3000 then "Up to 3K" else if [MonthlyIncome] <= 5000 then "3K-5K"
             else if [MonthlyIncome] <= 8000 then "5K-8K" else if [MonthlyIncome] <= 12000 then "8K-12K"
             else "Over 12K", type text),
    IncomeSort = Table.AddColumn(IncomeBand, "IncomeBandSort",
        each if [MonthlyIncome] <= 3000 then 1 else if [MonthlyIncome] <= 5000 then 2
             else if [MonthlyIncome] <= 8000 then 3 else if [MonthlyIncome] <= 12000 then 4 else 5, Int64.Type),

    DistanceBand = Table.AddColumn(IncomeSort, "DistanceBand",
        each if [DistanceFromHome] <= 5 then "1-5" else if [DistanceFromHome] <= 10 then "6-10"
             else if [DistanceFromHome] <= 20 then "11-20" else "21+", type text),
    DistanceSort = Table.AddColumn(DistanceBand, "DistanceBandSort",
        each if [DistanceFromHome] <= 5 then 1 else if [DistanceFromHome] <= 10 then 2
             else if [DistanceFromHome] <= 20 then 3 else 4, Int64.Type),

    MgrBand = Table.AddColumn(DistanceSort, "ManagerTenureBand",
        each if [YearsWithCurrManager] <= 0 then "New (<1 yr)" else if [YearsWithCurrManager] <= 2 then "1-2 yrs"
             else if [YearsWithCurrManager] <= 5 then "3-5 yrs" else "6+ yrs", type text),
    MgrSort = Table.AddColumn(MgrBand, "ManagerTenureBandSort",
        each if [YearsWithCurrManager] <= 0 then 1 else if [YearsWithCurrManager] <= 2 then 2
             else if [YearsWithCurrManager] <= 5 then 3 else 4, Int64.Type),

    // Pay
    Annual = Table.AddColumn(MgrSort, "AnnualIncome", each [MonthlyIncome] * 12, Int64.Type),

    // Risk flags
    F1 = Table.AddColumn(Annual, "FlagOvertime", each if [OverTime] = "Yes" then 1 else 0, Int64.Type),
    F2 = Table.AddColumn(F1, "FlagFrequentTravel", each if [BusinessTravel] = "Travel_Frequently" then 1 else 0, Int64.Type),
    F3 = Table.AddColumn(F2, "FlagNoStockOptions", each if [StockOptionLevel] = 0 then 1 else 0, Int64.Type),
    F4 = Table.AddColumn(F3, "FlagShortTenure", each if [YearsAtCompany] <= 2 then 1 else 0, Int64.Type),
    F4b = Table.AddColumn(F4, "FlagEntryLevel", each if [JobLevel] = 1 then 1 else 0, Int64.Type),
    F5 = Table.AddColumn(F4b, "FlagLowSatisfaction",
        each if [JobSatisfaction] = 1 or [EnvironmentSatisfaction] = 1 or [WorkLifeBalance] = 1 then 1 else 0, Int64.Type),
    RiskCount = Table.AddColumn(F5, "RiskFlagCount",
        each [FlagOvertime] + [FlagFrequentTravel] + [FlagNoStockOptions] + [FlagShortTenure] + [FlagEntryLevel] + [FlagLowSatisfaction], Int64.Type),

    Result = Table.Sort(RiskCount, {{"EmployeeNumber", Order.Ascending}})
in
    Result
