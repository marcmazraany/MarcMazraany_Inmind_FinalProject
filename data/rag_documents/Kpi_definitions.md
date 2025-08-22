# KPI Definitions (Ground Truth)

**Purpose:** Canonical formulas + inclusions/exclusions for feasibility math and strategy checks.  
**Scope:** Monthly granularity, one row per month (see `monthly_kpis` data).

---

## 0) Conventions (applies to all)
- **As-of alignment:** Use the **latest month ≤ `asof`**.
- **Currency:** USD. **Rounding:** display to 2 decimals (except rates/ratios).
- **Active customer:** Paying subscriber counted at end of month.
- **New customer:** First active month falls in the month.
- **Churned customer:** Subscription ends in the month (non-reactivated).

**Column mapping (from `monthly_kpis`):**
- `month`, `active_customers`, `new_customers`, `churned_customers`,  
  `arpu`, `mrr`, `payment_fees`, `infra_cost`, `support_cost`, `total_variable_cost`,  
  `contribution_margin_pct`, `cost_to_serve`, `acquisition_rate_ratio`.

---

## 1) MRR — Monthly Recurring Revenue
**Definition:** Predictable subscription revenue recognized within the month (recurring only).  
**Formula (reference):**  
`MRR = active_customers × ARPU`  
**Column:** `mrr`  
**Inclusions:** Monthly subscription charges.  
**Exclusions:** One-off fees, services, taxes, refunds (already netted out in v1).

**Pitfalls to avoid:**  
- Do not mix bookings/ACV with MRR.  
- Do not include expansion/contraction modeling in v1; it’s baked into ARPU trend.

---

## 2) ARPU — Average Revenue Per User (per month)
**Definition:** Average recurring revenue per active customer in a month.  
**Formula:** `ARPU = MRR / active_customers`  
**Column:** `arpu`  
**Notes:** ARPU trends modestly over time; do not statically assume plan-level ARPU.

---

## 3) Customer Acquisition (Count) — “New Customers”
**Definition:** Number of new paying customers in the month.  
**Column:** `new_customers`  
**Usage in feasibility:** Run-rate baseline for acquisition goals.

**Related ratio (optional):**  
**Acquisition Rate Ratio** = `new_customers / active_customers_prev_month`  
**Column:** `acquisition_rate_ratio`  
**Note:** Use for context, not as the primary feasibility target.

---

## 4) Contribution Margin % (CM%)
**Definition:** Share of MRR left after **variable** costs (payment fees, infra, support).  
**Primary business KPI for profit-oriented goals.**

**Formula:**  
`CM% = (MRR − VariableCosts) / MRR`  
where  
- `VariableCosts = payment_fees + infra_cost + support_cost`  
- `payment_fees = payment_fee_rate × MRR` (baseline 2.5%)  
- `infra_cost` scales with `active_customers`  
- `support_cost` scales with tickets; modeled directly as a monthly amount in data

**Columns:**  
- Result: `contribution_margin_pct`  
- Components: `payment_fees`, `infra_cost`, `support_cost`, `total_variable_cost`

**Inclusions:** Only **variable** costs.  
**Exclusions:** Fixed costs (R&D, Sales & Marketing, G&A), depreciation, taxes.

**Interpretation guide:**  
- 0.55–0.75 is typical for SaaS with healthy infra/support.  
- Rising CM% can come from ARPU lift, ticket deflection, or infra efficiency.

---

## 5) Cost to Serve (CtS) — per Active Customer
**Definition:** Monthly **variable** cost to serve one active customer.  
**Formula:** `CtS = total_variable_cost / active_customers`  
**Column:** `cost_to_serve`  
**Interpretation:** Lower is better. Use in cost-oriented goals and guardrails for profitability.

**Components:**  
- `total_variable_cost = payment_fees + infra_cost + support_cost`

---

## 6) Churn (supporting metric)
**Definition:** Number of customers that end their subscription in the month.  
**Column:** `churned_customers`  
**Note:** Churn rate (%) not required for v1 feasibility; count exists for context.

---

## 7) Feasibility math (how KPIs are used)
- **Acquisition goal:** compare **target new_customers per month** vs **6-month run-rate**.  
  - Required monthly increase = `(target − run-rate) / months_left`.  
  - Classification by required increase as a share of run-rate.
- **Profit (CM%) goal:** compare **required monthly CM% lift** vs **recent monthly slope**.  
- **Cost-to-Serve goal:** compare **required monthly reduction** vs **recent reduction slope**.

---

## 8) Display rules & units
- Show `%` for CM% (e.g., 61.3%).  
- Show `$` for CtS and ARPU (2 decimal places).  
- Show integer counts for customers.  
- Always annotate **as-of month** (aligned to last <= `asof`).

---

## 9) Known simplifications (v1)
- No expansion/contraction MRR split; ARPU trend absorbs this.  
- Support cost is modeled directly (tickets × cost) and stored as `support_cost`.  
- Infra cost is an average per active; plan-tier differences are abstracted.

---

## 10) Trust & lineage
- These KPIs are computed exclusively from `monthly_kpis` (CSV/SQLite).  
- The feasibility agent must **not** recompute with alternate formulas at runtime.  
- Strategy must treat these definitions as **authoritative.**
