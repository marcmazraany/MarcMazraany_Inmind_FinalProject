# Current Tactics Inventory (Baseline)
**Version:** 1  
**Updated:** 2025-08-14  
**Tags:** baseline, tactics, acquisition, onboarding, success, pricing, analytics

## Purpose
Authoritative list of what’s already in place. Strategy must **not** recommend a tactic that is already “Active” unless proposing a clearly differentiated iteration. Use this file for redundancy/conflict checks.

---

## A. Acquisition (Top of Funnel)

### A1. Paid Ads (Search + Social)
- **Status:** Active (always-on)
- **Owner:** Performance Marketing Lead
- **Channels:** Google Search, LinkedIn, Meta
- **Primary KPI:** New customers (monthly), CAC by channel
- **Target Segment:** SMB, Mid-Market
- **Guardrails:** Spend reallocation allowed; **no net budget +>20% MoM** without approval (see constraints)
- **Notes:** Broad match limited; use exact/phrase for B2B intent; UTM governance in place
- **Last change:** 2025-07-20 (LP headline test scaled)

### A2. Organic (SEO + Content)
- **Status:** Active
- **Owner:** Content Lead
- **Cadence:** 3 posts/week, 1 pillar/month, quarterly refresh
- **Primary KPI:** Organic new customers, non-brand traffic
- **Notes:** Topic clusters around onboarding, workflow automation, ROI cases
- **Last change:** 2025-06-30 (new pillar: “Onboarding Playbooks by Segment”)

### A3. Referral Program (Credit-based, Double-Sided)
- **Status:** Active
- **Owner:** Growth PMM
- **Incentive:** Up to $100 equivalent; current offer: **$40 referrer / $20 referee credit**
- **Primary KPI:** Referral share of new customers; CAC blended
- **Regions:** All; **no cash** payouts in EU (credits only)
- **Last change:** 2025-06-16 (offer structure updated)

### A4. Outbound (SDR)
- **Status:** Active
- **Owner:** Sales Development Manager
- **Cadence:** **2 touches**/14 days (policy), calls optional if opted-in
- **Primary KPI:** SQL rate, Close rate for Mid-Market/Enterprise
- **Notes:** Strict opt-out compliance; ICP lists refreshed monthly
- **Last change:** 2025-05-12 (messaging tweaks; cadence aligned to policy)

---

## B. Lifecycle & Onboarding (Activation)

### B1. 14-Day Free Trial
- **Status:** Active
- **Owner:** Growth PM
- **Primary KPI:** Trial→Paid conversion
- **Notes:** No extensions without approval
- **Last change:** 2025-04-05 (trial email sequence updated)

### B2. Onboarding Email Sequence (3 touches)
- **Status:** Active
- **Owner:** Lifecycle Marketing
- **Cadence:** Day 0, Day 2, Day 7
- **Primary KPI:** First-value event completion; Trial→Paid conversion
- **Notes:** Emphasis on “first value” task in email #1
- **Last change:** 2025-04-30 (re-ordered checklist CTA)

### B3. In-App Product Tour + Checklist
- **Status:** Active
- **Owner:** Product Growth
- **Primary KPI:** First-day activation; Feature adoption
- **Notes:** 2-minute tour; 5-step checklist (persona-aware)
- **Last change:** 2025-04-10 (step order revised)

### B4. Weekly Live Onboarding Webinar
- **Status:** Active
- **Owner:** Customer Success
- **Primary KPI:** Trial→Paid conversion for attendees
- **Notes:** Recording available on help center
- **Last change:** 2025-03-22 (Q&A segment added)

---

## C. Customer Success & Support (Retention / Cost-to-Serve)

### C1. Help Center (KB) + Search
- **Status:** Active
- **Owner:** Support Ops
- **Primary KPI:** Deflection rate; Tickets per 1k active
- **Notes:** Quarterly article refresh; coverage ≥ top 50 intents
- **Last change:** 2025-06-05 (20 articles updated)

### C2. Chatbot (L1 Triage) with Human Handoff
- **Status:** Active
- **Owner:** Support Ops
- **Primary KPI:** First-reply time; Deflection rate; CtS
- **Notes:** Human handoff mandated; 15 high-volume intents configured
- **Last change:** 2025-03-28 (intent expansion)

### C3. Office Hours (CSM)
- **Status:** Active (Enterprise)
- **Owner:** Customer Success Lead
- **Primary KPI:** Ticket reopen rate; NPS (Enterprise)
- **Notes:** Scheduled weekly; solution-focused sessions
- **Last change:** 2025-05-01 (agenda template standardized)

---

## D. Pricing & Packaging

### D1. Price Ladder: Basic / Pro / Enterprise
- **Status:** Active
- **Owner:** Monetization PM
- **Primary KPI:** ARPU, Win rate (Pro), Churn (Enterprise)
- **Notes:** ±10% price test allowed as experiment; no tier reshuffling of critical Enterprise features
- **Last change:** 2025-07-28 (Pro +5% regional test)

### D2. Discounts (Promo)
- **Status:** Active within policy
- **Owner:** Sales Ops
- **Policy:** Max **15%** off list without approval
- **Primary KPI:** Close rate vs. Net ARPU impact
- **Last change:** 2025-05-18 (SMB seasonal promo)

---

## E. Analytics & Data

### E1. Product & Web Analytics
- **Status:** Active (standard stack)
- **Owner:** Data Engineering
- **Primary KPI:** Data completeness; Funnel coverage
- **Notes:** No new trackers without legal review
- **Last change:** 2025-02-14 (event schema cleanup)

### E2. KPI Source of Truth
- **Status:** Active
- **Owner:** Data Analytics
- **Data:** `monthly_kpis` (CSV/SQLite); **as-of alignment** per definitions
- **Notes:** Strategy and Feasibility must consume from this source
- **Last change:** 2025-08-01 (data refresh)

---

## F. “Do-Not-Recommend” Rules (Deduplication)
- If **Status: Active**, do not propose the same tactic again unless:
  - It’s a **materially different variant** (new audience/geo, new incentive structure, new offer) **and** cites a clear rationale.
- If a tactic **conflicts** with any item in `constraints_policies.md`, propose a compliant alternative.
- Always include the **tactic ID** from this file in recommendations for traceability (e.g., “build on A3: Referral Program — variant: partner co-ops”).