Version: 1
Updated: 2025-08-17
Tags: baseline, KPI, definitions, formulas, feasibility
Source of truth data: monthly_kpis (CSV/SQLite)
As-of alignment rule: For any asof date, use the latest month ≤ asof.

Column map (from monthly_kpis)

month, active_customers, new_customers, churned_customers, arpu, mrr, payment_fees, infra_cost, support_cost, total_variable_cost, contribution_margin_pct, cost_to_serve, acquisition_rate_ratio.

1) Churn Rate (logo churn)

What it measures
Share of customers who ended their subscription in the month.

Primary formula (period churn, monthly):

Churn Rate
=
Churned Customers in Month
Active Customers at Start of Month
Churn Rate=
Active Customers at Start of Month
Churned Customers in Month
	​


Numerator = churned_customers (that month).

Denominator ≈ active_customers from the previous month (if start-of-month isn’t stored, use active_customers_prev = LAG(active_customers,1)).

Alternative views (use when needed, not default):

Gross Revenue Churn %: churned MRR / start-of-month MRR.

Net Revenue Churn %: (churned MRR − expansion MRR) / start-of-month MRR.

Not modeled in v1 dataset; ARPU trend absorbs expansion/contraction.

Interpretation guide (monthly, logo churn):

1–3%: healthy for B2B SMB/Mid.

3–5%: watchlist; retention work needed.

5%: priority issue.

Pitfalls & rules:

Count reactivations as new, not negative churn.

Use start-of-month denominator; not end-of-month (avoids denominator shrink bias).

Don’t mix trial exits unless your definition of “active customer” includes paid only (this project does).

2) Contribution Margin % (CM%) — profit margin proxy for this project

What it measures
Percent of recurring revenue left after variable costs (payment, infra, support). It’s the profit lever you can move quickly without fixed-cost accounting.

Formula:

CM%
=
MRR
−
Variable Costs
MRR
where
Variable Costs
=
payment_fees
+
infra_cost
+
support_cost
CM%=
MRR
MRR−Variable Costs
	​

whereVariable Costs=payment_fees+infra_cost+support_cost

Inputs come directly from monthly_kpis.

Interpretation guide (SaaS, monthly):

0.55–0.75 typical when infra/support are efficient.

Rising CM% comes from ARPU lift, infra efficiency, and ticket deflection.

What CM% is not (here):

Not Gross Margin including COGS beyond variable items.

Not Operating/Net Profit Margin (no fixed costs here).

Pitfalls & rules:

Keep scope to recurring revenue only (MRR).

Do not recompute CM% from scratch at runtime; use the table’s contribution_margin_pct for consistency.

3) Customer Acquisition Rate (CAR)

What it measures
How many new paying customers you add per month (count), and optionally the rate relative to your base.

Primary KPI (count):

CAR (count)
=
new_customers
CAR (count)=new_customers

Optional ratio (context, not the primary target):

CAR Ratio
=
new_customers
Active Customers at Start of Month
CAR Ratio=
Active Customers at Start of Month
new_customers
	​


Denominator ≈ previous month’s active_customers.

Run-rate baseline (for feasibility):
Use 6-month average of new_customers to smooth seasonality.

Interpretation guide:

Track trend (slope over last 12 months) and mix by channel (if available).

For targets (e.g., “hit 450 new/mo by 2026-01-01”), compute required monthly delta vs. run-rate.

Pitfalls & rules:

Count paying activations only (trials are not “new customers”).

Avoid using end-of-month active as denominator for the ratio.

4) Cost to Serve (CtS)

What it measures
Monthly variable cost to serve one active customer.

Formula:

CtS
=
Variable Costs
Active Customers
=
payment_fees
+
infra_cost
+
support_cost
active_customers
CtS=
Active Customers
Variable Costs
	​

=
active_customers
payment_fees+infra_cost+support_cost
	​


Interpretation guide:

Lower is better. Typical ranges in this dataset: $8–$15.

Moves with ticket volume & handling, infra efficiency, and payment fee rate.

Pitfalls & rules:

Do not include fixed costs (R&D, S&M, G&A).

If active_customers is very small, monitor for ratio volatility (add guardrails in analysis).

Feasibility math (how the Strategy should use these)

Acquisition goal (count):

Baseline = 6-month avg of new_customers.

Required delta = (target_per_month − baseline) / months_left.

Difficulty bands (rule of thumb):

≤25% of baseline → Feasible

25–75% → Stretch

75% → Unrealistic

CM% goal:

Compare required monthly lift to the 12-month slope of contribution_margin_pct.

If required lift ≲ 1.5× recent slope → Feasible; 1.5–3× → Stretch; >3× → Unrealistic.

CtS goal:

Compare required monthly reduction to the 12-month slope of cost_to_serve (typically negative if improving).

Similar bands as CM%, using absolute values.

Worked micro-examples (sanity checks)

Churn Rate

Prev month active: 10,000

Churned this month: 250

Churn Rate = 250 ÷ 10,000 = 2.5%

CM%

MRR = $1,000,000

Payment fees = $25,000; Infra = $220,000; Support = $210,000

Variable Costs = $455,000

CM% = (1,000,000 − 455,000) ÷ 1,000,000 = 54.5%

CAR (count & ratio)

New customers = 1,500

Prev month active = 50,000

CAR (count) = 1,500; CAR Ratio = 1,500 ÷ 50,000 = 3.0%

CtS

Variable Costs = $455,000

Active customers = 50,000

CtS = 455,000 ÷ 50,000 = $9.10

Quality & governance rules (for agents)

Cite the source: When reporting KPI values, include the month used and confirm alignment to asof.

Don’t double-count: Keep period definitions consistent (monthly).

Be explicit about units: % for rates (CM%, Churn), $ for dollar metrics (CtS, ARPU, MRR), integers for counts (CAR).

Flag anomalies: If a value deviates >3σ from its 12-month mean, tag Data Anomaly and recommend a data check before acting.