# Experiments Log (Past 6 Months)
**Version:** 1  
**Updated:** 2025-08-14  
**Tags:** baseline, experiments, decisions, evidence

## Purpose
Ground truth of what was tried recently, with outcomes and decisions. Strategy must use this to avoid repeating failed ideas and to scale proven wins. Follow experimentation guardrails in `constraints_policies.md`.

---

### EX-2025-03-01 — Chatbot Intent Expansion (C2 → variant v1.3)
- **Goal Type:** cost_to_serve  
- **Hypothesis:** Expanding L1 intents will reduce tickets/1k active → lower CtS without hurting NPS.
- **Design:** 50/50 traffic split for eligible intents; **min run 3 weeks**; exposures ≥ 20k sessions.
- **Dates:** 2025-03-10 → 2025-03-31  
- **Primary Metric:** Tickets per 1k active (monthly), CtS  
- **Secondary:** NPS, First-reply time  
- **Result:** Tickets/1k active **−7.1%** (95% CI −11.8% to −2.5%); CtS **−$0.22**; NPS neutral (Δ +0.1)  
- **Decision:** **Ship** (C2 updated)  
- **Key Learnings:** Best gains on “billing” and “permissions” intents; handoff CTA placement matters.  
- **Next:** Add self-serve article links to top 5 intents.

---

### EX-2025-04-02 — Onboarding Checklist Re-order (B3 → v2)
- **Goal Type:** acquisition (activation → conversion)  
- **Hypothesis:** Surfacing “first-value” step first increases Trial→Paid conversion.
- **Design:** 50/50 trial cohort; run 4 weeks; ≥ 5k trials.
- **Dates:** 2025-04-01 → 2025-04-30  
- **Primary Metric:** Trial→Paid conversion  
- **Result:** **+1.6 pp** (from 12.4% → 14.0%), p=0.02; retention 30-day unchanged  
- **Decision:** **Ship** (B3 updated)  
- **Key Learnings:** Persona-aware checklist mapping improved completion rate of step 1.  
- **Next:** Micro-copy test on Day-2 email CTA.

---

### EX-2025-05-03 — Referral Incentive Tuning (A3 offer)
- **Goal Type:** acquisition  
- **Hypothesis:** Switching from $50 one-sided to **$40/$20 double-sided** increases referral volume and reduces blended CAC.
- **Design:** Geo-split (NA/EU); run 4 weeks; ≥ 2k referrals.
- **Dates:** 2025-05-15 → 2025-06-15  
- **Primary Metric:** Referral new customers/week  
- **Secondary:** Blended CAC, Fraud flags  
- **Result:** Referral new customers **+18%** (CI +8% to +28%); blended CAC **−$6**; no fraud increase  
- **Decision:** **Ship** globally (A3 updated)  
- **Key Learnings:** Clear “both sides benefit” copy outperformed; partner co-ops promising.  
- **Next:** Test partner co-marketing with 2 ISVs.

---

### EX-2025-06-01 — Ads Landing Page Headline (A1 LP v5)
- **Goal Type:** acquisition  
- **Hypothesis:** ROI-focused headline improves CVR without hurting CPC.
- **Design:** 50/50 split on paid traffic; run 16 days; ≥ 30k sessions.
- **Dates:** 2025-06-20 → 2025-07-05  
- **Primary Metric:** Paid CVR to trial  
- **Secondary:** Cost per new customer  
- **Result:** CVR **+9.3%** (p=0.01); CPC flat; cost/new **−$11**  
- **Decision:** **Scale** (rollout to all paid; keep an eye on lead quality)  
- **Key Learnings:** ROI language resonated with SMB; Enterprise impact neutral.  
- **Next:** Create Enterprise-specific LP variant focusing on security/admin.

---

### EX-2025-07-02 — Pro Plan +5% Price Test (D1 regional)
- **Goal Type:** profit_cm  
- **Hypothesis:** A modest price lift raises ARPU with limited conversion drag and stable short-term churn.
- **Design:** Regional test (EU+NA); 50/50 split on eligible traffic; run 3 weeks; ≥ 3k opps.
- **Dates:** 2025-07-15 → 2025-08-05  
- **Primary Metric:** ARPU (Pro)  
- **Secondary:** Trial→Paid conversion, 30-day churn  
- **Result:** ARPU **+3.2%**; conversion **−1.1 pp** (not significant); churn neutral (30-day)  
- **Decision:** **Hold** (maintain +5% in EU/NA; monitor cohort churn through Oct)  
- **Key Learnings:** SMB most price-sensitive; Enterprise unaffected.  
- **Next:** Evaluate packaging of 1 admin feature to Enterprise only (within policy).

---

### EX-2025-05-10 — Support SLA “Fast First Reply” (C1/C2 ops change)
- **Goal Type:** cost_to_serve / NPS  
- **Hypothesis:** Auto-ack + staffing to respond <1h improves NPS with acceptable CtS.
- **Design:** Calendar-based (business hours only); run 3 weeks; > 1k tickets/week.
- **Dates:** 2025-05-01 → 2025-05-21  
- **Primary Metric:** NPS  
- **Secondary:** Ticket reopen rate, CtS  
- **Result:** NPS **+1.5**; reopen **−10%**; CtS **+ $0.05** (small increase due to coverage)  
- **Decision:** **Pilot** (keep during business hours; no weekends)  
- **Key Learnings:** Faster first touch reduces reopens; limited diminishing returns after 2h.  
- **Next:** Expand chatbot handoff quality to offset staffing cost.

---

### EX-2025-04-15 — Outbound Cadence Timing (A4 messaging)
- **Goal Type:** acquisition (Mid-Market)  
- **Hypothesis:** Moving 2nd email from day 5 → day 3 lifts reply and SQL rate while staying within policy.
- **Design:** 50/50 prospect split; run 2 weeks; ≥ 10k prospects.
- **Dates:** 2025-04-15 → 2025-04-29  
- **Primary Metric:** MQL→SQL rate  
- **Result:** **Flat** (Δ +0.2 pp, ns); opt-outs unchanged  
- **Decision:** **Keep** (timing at day 3 OK); focus on messaging personalization next  
- **Key Learnings:** Timing less material than value prop in email #2.  
- **Next:** Test persona-tailored value props.

---

## Reporting Conventions
- **Outcome labels:** Ship / Scale / Hold / Pilot / Stop  
- **Evidence:** Each entry should include sample size, run dates, confidence or CI when available.  
- **Data sources:** KPI deltas validated against `monthly_kpis` where applicable; ad platform/CRM stats stored separately.  
- **Retention checks:** For pricing/activation wins, run 30-/60-day follow-ups before “Scale.”