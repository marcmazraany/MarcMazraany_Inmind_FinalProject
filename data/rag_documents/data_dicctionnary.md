# Data Dictionary — `monthly_kpis`
**Version:** 1  
**Updated:** 2025-08-14  
**Tags:** baseline, data, dictionary

## Table Overview
- **Granularity:** Monthly (one row per calendar month).
- **Time zone:** UTC.
- **Coverage:** 2015-01-01 → 2025-08-01 (inclusive).
- **Primary key:** `month` (YYYY-MM-01).
- **Source of truth:** `monthly_kpis_2015_2025.csv` (CSV) and `monthly_kpis` (table) in `monthly_kpis.db`.
- **Alignment rule:** When given an `asof` date, select the latest `month` **≤ asof**.

## Columns

| Column                   | Type      | Unit / Format | Nulls | Definition / Derivation | Notes & Examples |
|--------------------------|-----------|---------------|-------|-------------------------|------------------|
| `month`                  | date      | `YYYY-MM-01`  | No    | Calendar month key      | e.g., `2025-08-01` |
| `active_customers`       | integer   | count         | No    | Customers active at end of the month | Monotonicity not guaranteed (churn/new) |
| `new_customers`          | integer   | count         | No    | New paying customers whose **first active** month is this month | Primary for acquisition goals |
| `churned_customers`      | integer   | count         | No    | Customers whose subscription ended in this month | Context/supporting only |
| `arpu`                   | decimal   | USD (2 dp)    | No    | Average revenue per active customer | `mrr / active_customers` in reference terms |
| `mrr`                    | decimal   | USD (2 dp)    | No    | Monthly Recurring Revenue | Equals `active_customers × arpu` in this dataset |
| `payment_fees`           | decimal   | USD (2 dp)    | No    | Variable payment processing fees | Baseline rate 2.5% × `mrr` |
| `infra_cost`             | decimal   | USD (2 dp)    | No    | Variable infrastructure cost | Scales with `active_customers` |
| `support_cost`           | decimal   | USD (2 dp)    | No    | Variable support cost (ticket-driven) | Already aggregated monthly |
| `total_variable_cost`    | decimal   | USD (2 dp)    | No    | `payment_fees + infra_cost + support_cost` | Authoritative sum |
| `contribution_margin_pct`| decimal   | ratio (0–1)   | No    | `(mrr − total_variable_cost) / mrr` | Profit KPI (higher is better) |
| `cost_to_serve`          | decimal   | USD (2 dp)    | No    | `total_variable_cost / active_customers` | Cost KPI (lower is better) |
| `acquisition_rate_ratio` | decimal   | ratio         | No    | `new_customers / active_customers_prev_month` | Context metric |

## Accepted Value Ranges (sanity checks)
- `active_customers` ≥ 0  
- `new_customers`, `churned_customers` ≥ 0  
- `arpu` ∈ [\$50, \$200] typical; dataset trends ~\$100 → \$130  
- `mrr` ≥ 0  
- `payment_fees` ≥ 0 (≈ 2.5% of `mrr`)  
- `infra_cost`, `support_cost`, `total_variable_cost` ≥ 0  
- `contribution_margin_pct` ∈ [0, 1] (typical 0.45–0.75)  
- `cost_to_serve` > 0 (typical \$8–\$15)  
- `acquisition_rate_ratio` ≥ 0 (typical 0.02–0.15)

## Lineage & Computation Rules
- **Do not recompute:** Treat `contribution_margin_pct` and `cost_to_serve` in this table as canonical for feasibility; recomputation at runtime can cause mismatches.
- **ARPU vs. MRR:** Minor rounding differences may occur; keep display to 2 decimals.
- **Churn metrics:** `churned_customers` is provided for context; churn **rate** is not required in v1 feasibility.

## Join & Access Patterns
- **Single-table read:** Feasibility and Strategy flows can read everything from `monthly_kpis` without joins.
- **Filters:** Use `WHERE month <= :asof` for snapshots; use `ORDER BY month DESC LIMIT n` for recent trends.
- **Time windows:** For acquisition run-rate, prefer **6-month** average; for slopes, prefer **12-month** window.

## Quality & Validation Checklist (agents)
- **As-of selection:** Always align to last `month` ≤ `asof`.
- **Missing row:** If `asof` precedes coverage, use the first row and flag **Low Confidence**.
- **Outliers:** If any metric varies > **3σ** from 12-month mean, tag recommendation with **Data Anomaly**.
- **Units:** Display `%` for CM%, `$` for CtS/ARPU/MRR, integers for counts.

## Example Snapshots (display guidance)
- **Feasibility card:**  
  - `as-of`: 2025-08-01  
  - Acquisition run-rate (6m avg): **N**/mo  
  - CM%: **X%** (trend: ±Y pp/mo)  
  - CtS: **$Z** (trend: ±W $/mo)