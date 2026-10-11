"""
Build the Level 2 report (Word) from metrics.json, the cleaning log and the charts.

Run from the 02-intermediate folder, after analyze_online_retail.py:
    python analysis/build_report.py
Output: report/Online_Retail_Customer_Analysis_Report.docx
"""
import json
from pathlib import Path
import pandas as pd
from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[1]
M = json.loads((ROOT / "analysis/metrics.json").read_text())
log = pd.read_csv(ROOT / "docs/cleaning_log.csv")
TB = pd.ExcelFile(ROOT / "analysis/analysis_tables.xlsx")
ctry = TB.parse("Country").set_index("Country")
mon = TB.parse("Monthly").set_index("InvoiceMonth")
pre = mon.loc["2010-12":"2011-08", "Revenue"]
newrev = TB.parse("New vs returning").set_index("Month").loc["2011-02":"2011-11", "New"]
CH = ROOT / "report/charts"
OUT = ROOT / "report/Online_Retail_Customer_Analysis_Report.docx"
NAVY = RGBColor(0x1F, 0x38, 0x64)

k = lambda v: f"£{v/1e3:,.0f}K"          # noqa: E731
m_ = lambda v: f"£{v/1e6:,.2f}M"         # noqa: E731
p = lambda v, d=0: f"{v*100:.{d}f}%"     # noqa: E731
R = M["rfm"]

doc = Document()
sec = doc.sections[0]
sec.left_margin = sec.right_margin = Cm(2.2)
sec.top_margin = sec.bottom_margin = Cm(2.0)
st = doc.styles["Normal"]
st.font.name = "Calibri"
st.font.size = Pt(10.5)
st.paragraph_format.space_after = Pt(6)
for name, size in (("Heading 1", 16), ("Heading 2", 13), ("Heading 3", 11)):
    h = doc.styles[name]
    h.font.name = "Calibri"
    h.font.size = Pt(size)
    h.font.bold = True
    h.font.color.rgb = NAVY


def shade(cell, hex_):
    tcPr = cell._tc.get_or_add_tcPr()
    sh = OxmlElement("w:shd")
    sh.set(qn("w:val"), "clear")
    sh.set(qn("w:color"), "auto")
    sh.set(qn("w:fill"), hex_)
    tcPr.append(sh)


def para(text, bold_lead=None, italic=False, size=None):
    pr = doc.add_paragraph()
    if bold_lead:
        r = pr.add_run(bold_lead)
        r.bold = True
    r = pr.add_run(text)
    r.italic = italic
    if size:
        for run in pr.runs:
            run.font.size = Pt(size)
    return pr


def bullet(text, lead=None):
    pr = doc.add_paragraph(style="List Bullet")
    if lead:
        pr.add_run(lead).bold = True
    pr.add_run(text)
    return pr


def table(rows, header, widths=None, size=9):
    t = doc.add_table(rows=1, cols=len(header))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(header):
        c = t.rows[0].cells[i]
        c.text = ""
        r = c.paragraphs[0].add_run(h)
        r.bold = True
        r.font.size = Pt(size)
        r.font.color.rgb = RGBColor(255, 255, 255)
        shade(c, "1F3864")
    for row in rows:
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = ""
            r = cells[i].paragraphs[0].add_run(str(v))
            r.font.size = Pt(size)
    if widths:
        for row in t.rows:
            for i, w in enumerate(widths):
                row.cells[i].width = Cm(w)
    doc.add_paragraph()
    return t


def figure(name, width=15.5, caption=None):
    doc.add_picture(str(CH / name), width=Cm(width))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    if caption:
        c = doc.add_paragraph(caption)
        c.alignment = WD_ALIGN_PARAGRAPH.CENTER
        c.runs[0].italic = True
        c.runs[0].font.size = Pt(9)


def finding(what, why, action):
    para(what, "What the data shows. ")
    para(why, "Likely reason. ")
    para(action, "What to do. ")


# ================================================================== title
t = doc.add_paragraph()
r = t.add_run("Customer and Revenue Analysis")
r.bold = True
r.font.size = Pt(26)
r.font.color.rgb = NAVY
t = doc.add_paragraph()
r = t.add_run("UK online giftware retailer, December 2010 to December 2011")
r.font.size = Pt(14)
doc.add_paragraph("ShadowFox Data Analyst Internship, Intermediate Level")
doc.add_paragraph("Prepared by: Azizul Abedin Azmi")
doc.add_paragraph("azmi00121@gmail.com | github.com/azizulabedinazmi | azizulabedinazmi.is-a.dev")
doc.add_paragraph()

# ================================================================ summary
doc.add_heading("1. Executive summary", 1)
para(f"The business sold {m_(M['revenue'])} of goods across {M['invoices']:,} orders to "
     f"{M['customers']:,} identified customers in {M['countries']} countries over one year. "
     f"Revenue runs at roughly £0.5M to £0.75M a month from January to August, then climbs sharply into November. "
     f"The more important story is who produces it: a small group of repeat buyers carries the business.")
bullet(f" The top 10% of customers produce {p(M['top10_rev_share'])} of revenue and the top 20% produce "
       f"{p(M['top20_rev_share'])}. The bottom half of customers produce {p(M['bottom50_rev_share'])}.",
       "Revenue is highly concentrated.")
bullet(f" {R['Champions']['customers']:,} customers ({p(R['Champions']['cust_share'])} of the base) generate "
       f"{p(R['Champions']['rev_share'])} of revenue. They order about {R['Champions']['avg_orders']:.0f} times a year.",
       "A Champions group does most of the work.")
bullet(f" {p(M['repeat_share'])} of customers ordered more than once, and those repeat customers account for "
       f"{p(M['repeat_rev_share'])} of revenue. In 2011, returning customers made {p(M['returning_rev_share_2011'])} of revenue from identified customers.",
       "Repeat buying is the business.")
bullet(f" Only about {p(M['ret_m1'])} of a month's new customers order again the following month, and the figure "
       f"stays near {p(M['ret_m6'])} six months later. New customers are being brought in, but most do not come back.",
       "Most new customers do not return.")
bullet(f" September to November brought in {p(M['q4_share'])} of revenue. November alone was "
       f"{M['nov_vs_avg_jan_aug']:.1f} times the average month from January to August.",
       "The business is highly seasonal.")
bullet(f" {R['At Risk']['customers']:,} customers who ordered several times before have been silent for about "
       f"{R['At Risk']['avg_recency']:.0f} days. They spent {k(R['At Risk']['revenue'])} with the business before going quiet.",
       "There is a recoverable pool of lapsed buyers.")
para("Main recommendations: protect and reward the Champions, run a win-back campaign aimed at At Risk and "
     "high-value quiet customers, add a second-order incentive for new customers, and build the Q4 plan "
     "(stock, staffing, campaigns) from August. Details are in section 7.", italic=False)

# ============================================================= dataset
doc.add_heading("2. Business question and data", 1)
para("Business question: where does revenue come from, how well does the company keep its customers, and "
     "which actions would grow revenue most?", "")
para("Supporting questions:")
for q in ["How does revenue move over time, and how seasonal is it?",
          "How concentrated is revenue across customers and products?",
          "How many customers come back, and how quickly do they drop off?",
          "Which customer segments matter most, and which are at risk?",
          "Which products and countries drive the business?"]:
    bullet(q)
table([["Source", "Online Retail dataset (UCI Machine Learning Repository), read from a public GitHub mirror"],
       ["Period", f"{M['date_min']} to {M['date_max']}"],
       ["Raw size", "541,909 order lines, 8 columns"],
       ["Grain", "One row = one product line on one invoice"],
       ["After cleaning", f"522,537 sales lines, {M['invoices']:,} invoices, {M['products']:,} products, "
                          f"{M['customers']:,} identified customers"],
       ["Customer field", f"CustomerID is missing on about 25% of lines. These lines are kept for revenue, "
                          f"product and country analysis, but excluded from customer analysis. "
                          f"Identified customers account for {p(M['identified_rev_share'])} of revenue."],
       ["Currency", "Pounds sterling (£). The retailer is UK based."]],
      ["Item", "Detail"], widths=[3.5, 13], size=9.5)

# ============================================================== cleaning
doc.add_heading("3. Data cleaning and preparation", 1)
para("Every change is recorded in docs/cleaning_log.csv and reproduced by scripts/clean_online_retail.py. "
     "The main steps:")
rows = []
for r_ in log.itertuples():
    if r_._4 and r_._4 != 0 and r_._2 != "Derived columns":
        rows.append([r_._2, r_._3, f"{int(r_._4):,}"])
table(rows, ["Issue found", "Action taken", "Rows affected"], widths=[6.2, 8.2, 2.1], size=8.5)
para("Three decisions are worth explaining:")
bullet(" Lines whose invoice number starts with C are returns. They were removed from revenue and analysed on "
       "their own, so revenue figures show completed sales only.", "Cancellations.")
bullet(" Two orders of more than 70,000 units were cancelled in full by the same customer. Left in, one of them "
       "would have shown up as the second best-selling product at £168K, when it earned nothing. Both the sale and the "
       "cancellation were removed.", "Order-and-cancel pairs.")
bullet(" Postage, manual adjustments, bank charges, Amazon fees and gift vouchers are not products. "
       "Removing them keeps product and revenue analysis honest.", "Non-product lines.")

# ============================================================= metrics
doc.add_heading("4. Metrics used and why", 1)
table([["Revenue", "Quantity x UnitPrice, completed sales only", "Size and trend of the business"],
       ["Orders and customers", "Distinct InvoiceNo; distinct CustomerID", "Separates more buyers from bigger baskets"],
       ["Average order value", "Revenue / orders", "Basket size; the median is shown too because a few huge orders skew the mean"],
       ["Repeat purchase rate", "Customers with 2+ orders / all customers", "Basic loyalty measure"],
       ["Revenue concentration", "Share of revenue from top 1%, 10%, 20% of customers", "How exposed the business is to a few accounts"],
       ["Cohort retention", "Share of customers first seen in a month who order again N months later", "Whether new customers stick"],
       ["RFM segments", "Recency (days since last order), Frequency (orders), Monetary (revenue); each scored 1 to 5 by quintile", "Groups customers by value and risk so each group gets a different action"],
       ["Cancellation rate", "Value of cancelled lines / revenue", "Revenue leakage"]],
      ["Metric", "Definition", "Why it matters"], widths=[3.4, 6.6, 6.5], size=9)

# ============================================================ findings
doc.add_heading("5. Findings", 1)

doc.add_heading("5.1 Revenue trend and seasonality", 2)
figure("01_monthly_revenue.png", 15)
finding(f"Revenue sits between {k(pre.min())} and {k(pre.max())} a month from December 2010 to August 2011, then rises to "
        f"£1.03M in September, £1.10M in October and {m_(M['nov_rev'])} in November. The number of active customers "
        f"rises with it, so the peak is driven by more buyers, not only bigger orders. December 2011 is a partial month "
        f"(data stops on 9 December) and should not be read as a fall.",
        f"Items with Christmas-themed names make up only {p(M['xmas_share_of_revenue'])} of revenue, but "
        f"{p(M['xmas_sep_nov_share'])} of their sales fall in September to November. The business sells giftware to "
        f"customers who are stocking up before the holidays, and trade buyers order early.",
        "Plan Q4 from August: secure stock for the best sellers, schedule warehouse and support staff, and start "
        "campaigns in late August, ahead of the September jump rather than during it.")

doc.add_heading("5.2 When customers order", 2)
figure("02_weekday_hour.png", 15.5)
finding(f"{p(M['peak_hours_share'])} of revenue is placed between 10:00 and 15:59. Thursday and Tuesday are the strongest "
        f"days and Sunday is {p(M['sunday_share'])} of revenue. No orders are recorded on Saturdays.",
        "This is a working-hours pattern, which fits trade and business buyers more than consumers. The Saturday gap "
        "may be a trading rule or a gap in how the data was recorded. The data cannot say which, so it is worth "
        "confirming with the business before acting on it.",
        "Schedule emails and promotions for Tuesday to Thursday mornings, and keep customer support staffed over the "
        "10:00 to 16:00 window.")

doc.add_heading("5.3 Countries", 2)
figure("03_countries.png", 12)
finding(f"The United Kingdom is {p(M['uk_share'])} of revenue. Export markets add {p(M['export_rev_share'])}, led by "
        f"the Netherlands ({k(ctry.loc['Netherlands','Revenue'])}), EIRE ({k(ctry.loc['EIRE','Revenue'])}), Germany "
        f"({k(ctry.loc['Germany','Revenue'])}) and France ({k(ctry.loc['France','Revenue'])}). The customer counts behind these "
        f"figures differ sharply: EIRE's revenue comes from only {int(ctry.loc['EIRE','Customers'])} customers, the Netherlands "
        f"and Australia from {int(ctry.loc['Netherlands','Customers'])} each, while Germany has {int(ctry.loc['Germany','Customers'])} "
        f"and France {int(ctry.loc['France','Customers'])}.",
        "The Netherlands, EIRE and Australia are essentially a handful of large accounts. Germany and France are "
        "broader markets with many smaller buyers.",
        "Manage EIRE, the Netherlands and Australia as key accounts, because losing one buyer would remove a large share "
        "of that market. Germany and France are better candidates for market-level marketing, since the customer base "
        "is already broad.")

doc.add_heading("5.4 Revenue concentration", 2)
figure("04_concentration.png", 11)
finding(f"The top 1% of customers ({round(M['customers']*0.01)} accounts) produce {p(M['top1_rev_share'])} of revenue, the top 10% "
        f"produce {p(M['top10_rev_share'])}, and the top 20% produce {p(M['top20_rev_share'])}. This is steeper "
        f"than the usual 80/20 rule.",
        f"Average order value is £{M['aov']:,.0f} but the median is £{M['aov_median']:,.0f}, so a few very large orders "
        f"pull the average up. Combined with orders placed during working hours (section 5.2), this suggests many "
        f"customers are businesses buying to resell. The dataset has no customer-type field, so this is an inference, "
        f"not a measured fact.",
        "Losing one top account costs far more than losing many small ones. Give the top 1% to 10% a named account "
        "owner and watch their order gaps closely.")

doc.add_heading("5.5 Repeat purchase behaviour", 2)
figure("05_orders_per_customer.png", 11)
finding(f"{p(M['repeat_share'])} of customers ordered more than once. The average customer ordered "
        f"{M['orders_per_customer_mean']:.1f} times, but the median is {M['orders_per_customer_median']:.0f}, so many customers "
        f"order once or twice while a smaller group orders very often. Repeat customers produce {p(M['repeat_rev_share'])} "
        f"of revenue, and returning customers have a higher average order (£{M['aov_returning']:,.0f}) than customers on their first "
        f"order month (£{M['aov_new']:,.0f}).",
        "Customers who come back also buy more each time, which is the usual sign of trust and familiarity "
        "building up.",
        "The cheapest growth comes from turning one-time buyers into second-time buyers.")

doc.add_heading("5.6 Retention by cohort", 2)
figure("06_cohort_retention.png", 15.5)
finding(f"On average, {p(M['ret_m1'])} of a month's new customers order again in the next month, {p(M['ret_m3'])} "
        f"are active three months later and {p(M['ret_m6'])} six months later. The rate does not fall steadily. It stays "
        f"flat or rises a little, which means customers who return do so in bursts. The December 2010 row is higher "
        f"({p(M['dec10_cohort_m1'])} in month 1) because the data starts that month, so those customers were already "
        f"established and are not truly new. It is excluded from the averages above.",
        "Customers reorder on their own cycle, probably restocking, not on a monthly rhythm. A one-month "
        "retention figure alone would make the business look worse than it is.",
        "Measure retention over 3 to 6 months, and time follow-up messages to the customer's own ordering gap "
        "rather than to a fixed calendar.")
figure("07_new_vs_returning.png", 15.5)
para(f"Returning customers supply about {p(M['returning_rev_share_2011'])} of monthly revenue during 2011, and their share "
     f"grows through the year. Revenue growth into November came mostly from existing customers ordering more. New-customer "
     f"revenue stayed between {k(newrev.min())} and {k(newrev.max())} a month from February to November.")

doc.add_heading("5.7 Customer segments (RFM)", 2)
figure("08_rfm_segments.png", 15.5)
seg_rows = []
desc = {"Champions": "Recent, frequent, high spend (R, F, M all 4 or 5)",
        "Loyal": "Order regularly and recently",
        "At Risk": "Ordered often before, quiet for months",
        "Lost / Hibernating": "Few orders, long silence",
        "Needs Attention": "Middling on every score",
        "New / Promising": "Recent, but only 1 or 2 orders"}
for nm in ["Champions", "Loyal", "At Risk", "Lost / Hibernating", "Needs Attention", "New / Promising"]:
    v = R[nm]
    seg_rows.append([nm, desc[nm], f"{v['customers']:,}", p(v["cust_share"]), p(v["rev_share"]),
                     f"{v['avg_recency']:.0f}", f"{v['avg_orders']:.1f}", f"£{v['avg_rev']:,.0f}"])
table(seg_rows, ["Segment", "Meaning", "Customers", "% of customers", "% of revenue", "Avg days since order",
                 "Avg orders", "Avg spend"], widths=[2.4, 4.2, 1.8, 1.7, 1.7, 1.7, 1.4, 1.6], size=8.5)
finding(f"Champions are {p(R['Champions']['cust_share'])} of customers and {p(R['Champions']['rev_share'])} of revenue, "
        f"each spending about £{R['Champions']['avg_rev']:,.0f} a year. At Risk customers are "
        f"{p(R['At Risk']['cust_share'])} of the base. They placed about {R['At Risk']['avg_orders']:.1f} orders each before going "
        f"quiet for roughly {R['At Risk']['avg_recency']:.0f} days. Separately, {M['valuable_quiet_customers']} customers in the top two "
        f"spend bands have not ordered in over 90 days, and they spent {k(M['valuable_quiet_revenue'])} before going quiet.",
        "A customer who used to order every few weeks and has been silent for five months has either moved to a "
        "competitor, changed what they sell, or been missed by the business. The data cannot say which. It does "
        "show that this group was valuable and is now inactive.",
        "Run a targeted win-back effort with a personal message first, before offering any discount. Recovering a modest share "
        f"of the {k(R['At Risk']['revenue'])} these customers brought in is a realistic first target.")

doc.add_heading("5.8 Products", 2)
figure("09_top_products.png", 13.5)
finding(f"The top 10 products make up {p(M['top10_products_share'])} of revenue and the top 10% of the "
        f"{M['products']:,} products make up {p(M['top10pct_products_share'])}. The best seller is the "
        f"{M['top_products'][0][0].title()} ({k(M['top_products'][0][1])}). Product revenue is spread widely "
        f"rather than resting on a few items.",
        "The catalogue is wide, with nearly 4,000 products, so no single item dominates. This is a description of the pattern; the data does not say why.",
        "Keep the long tail for variety, but make sure the top few hundred products are never out of stock, "
        "especially before September.")

doc.add_heading("5.9 Cancellations", 2)
para(f"Cancelled lines are worth {k(M['cancel_value'])}, or {p(M['cancel_rate'],1)} of revenue. The worst month for "
     f"cancellations (April 2011) reached {p(M['cancel_rate_peak_month'][1],1)}. Ten customers account for "
     f"{p(M['cancel_by_cust_top10_share'])} of the cancelled value. This is a low rate and is not the priority. "
     f"It is still worth checking whether the same few accounts cancel repeatedly.")

# ========================================================= recommendations
doc.add_heading("6. Why these patterns are happening: summary", 1)
bullet(" The pattern of heavy repeat ordering, large baskets and working-hours orders points to a trade customer base. "
       "In a trade business, a relatively small number of reliable accounts naturally carry the revenue.", "Concentration.")
bullet(" Gift and homeware buyers stock up before the holidays, and trade buyers order earlier than consumers would.",
       "Seasonality.")
bullet(" Many one-time customers are probably trying the business or placing a single stocking order. Without a prompt, "
       "there is no prompt to return. The data has no marketing information, so this is untested.", "Weak early retention.")
para("These are reasoned explanations from the patterns in the data. The dataset has no information about customer type, "
     "marketing activity, prices or competitors, so they should be tested with the business before large investments are made.",
     italic=True, size=9.5)

doc.add_heading("7. Recommendations", 1)
table([["1", "Protect the Champions",
        f"{R['Champions']['customers']:,} customers produce {p(R['Champions']['rev_share'])} of revenue.",
        "Assign account owners to the top 10%. Alert the team when a top customer's gap since last order is longer than usual. Offer early access to new lines.",
        "Champion count; their average orders per year"],
       ["2", "Win back lapsed high-value customers",
        f"{R['At Risk']['customers']:,} At Risk customers spent {k(R['At Risk']['revenue'])} before going quiet; "
        f"{M['valuable_quiet_customers']} high spenders have been silent over 90 days.",
        "Personal outreach to the highest spenders first, then a templated message. Ask why they stopped ordering. Test a small incentive on one half only.",
        "Reactivation rate; revenue from reactivated customers"],
       ["3", "Get a second order from new customers",
        f"Only about {p(M['ret_m1'])} of new customers order again the next month.",
        "Send a follow-up 2 to 3 weeks after the first order with best sellers and a modest incentive on the second order. Test it against a control group.",
        "Share of new customers who place a second order within 90 days"],
       ["4", "Build the Q4 plan from August",
        f"September to November is {p(M['q4_share'])} of revenue. November is {M['nov_vs_avg_jan_aug']:.1f}x a normal month.",
        "Forecast demand by product, order stock by July and August, schedule staff, and launch campaigns before the September jump.",
        "Stock-outs on top products; Q4 revenue vs plan"],
       ["5", "Time communication to when customers buy",
        f"{p(M['peak_hours_share'])} of revenue is ordered between 10:00 and 16:00, and Tuesday to Thursday are strongest.",
        "Send emails on Tuesday to Thursday mornings. Keep support staffed in the 10:00 to 16:00 window.",
        "Email-to-order conversion by weekday"],
       ["6", "Handle exports by market type",
        f"Exports are {p(M['export_rev_share'])} of revenue. EIRE rests on {int(ctry.loc['EIRE','Customers'])} customers, the Netherlands and Australia on "
        f"{int(ctry.loc['Netherlands','Customers'])} each; Germany and France have {int(ctry.loc['Germany','Customers'])} and {int(ctry.loc['France','Customers'])}.",
        "Key-account management for EIRE, the Netherlands and Australia. Market-level marketing for Germany and France.",
        "Revenue per export account; number of active buyers per country"]],
      ["#", "Action", "Evidence", "How", "How to measure"], widths=[0.7, 3.0, 4.4, 5.9, 3.0], size=8.5)

doc.add_heading("8. Limitations", 1)
for t_ in [
    "One year of data from one retailer. Seasonality is based on a single holiday season, so it cannot be separated from "
    "growth in the business.",
    f"About 25% of order lines have no CustomerID. Customer findings cover only the identified customers, who account for "
    f"{p(M['identified_rev_share'])} of revenue.",
    "December 2011 is a partial month. It is shown in grey and left out of averages.",
    "The first cohort (December 2010) contains existing customers because the data starts there, so it is excluded "
    "from average retention.",
    "RFM segment boundaries are quintile-based and somewhat arbitrary. Customers near a boundary could fall into either "
    "segment. The segments are for prioritising action, not exact classes.",
    "The dataset has no customer type, marketing, price or cost information. Profit cannot be calculated, so every "
    "'value' in this report is revenue, not profit.",
    "Reasons given for the patterns are inferences from the data and have not been tested."]:
    bullet(t_)

doc.add_heading("9. Reproducing this work", 1)
para("All code is in the repository. Run from the 02-intermediate folder:")
for line in ["python scripts/clean_online_retail.py", "python analysis/analyze_online_retail.py",
             "python analysis/build_report.py"]:
    pr = doc.add_paragraph(line)
    pr.runs[0].font.name = "Consolas"
    pr.runs[0].font.size = Pt(9.5)
para("Tables behind every chart are in analysis/analysis_tables.xlsx.")

doc.save(OUT)
print("saved", OUT)
