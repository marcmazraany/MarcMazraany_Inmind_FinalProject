# Constraints & Policies (Ground Truth)
**Version:** 1  
**Updated:** 2025-08-14  
**Tags:** baseline, guardrails, constraints, policies

## Purpose
Authoritative guardrails the Strategy workflow must respect. If any recommendation conflicts with these, the agent must either **adjust** the action or **flag for approval**.

---

## Business & Pricing
- **Billing cadence:** Monthly only (no annual prepay in v1).
- **Discount policy:** Max promotional discount **15%** off list price without approval.
- **Free trials:** Allowed up to **14 days**; extensions require approval.
- **Refund policy:** Pro-rata within first 30 days; otherwise case-by-case via Support.

## Market Scope
- **Segments served:** SMB, Mid-Market, Enterprise.
- **Regions supported:** MENA, EU, NA, APAC.
- **Language:** English primary; Arabic secondary where relevant (MENA).
- **Industry focus:** SaaS, Fintech, E-commerce, EdTech, Healthcare (others = low priority).

## Acquisition & Outreach
- **Approved channels:** Ads, Organic (SEO/Content), Referral, Outbound (SDR).
- **Outbound constraints:** No more than **2 cold emails** per prospect in 14 days; respect opt-out.
- **Referral incentives:** Monetary or credit up to **$100** equivalent; no cash gifts in EU.
- **Paid media:** Do not increase net paid spend estimate by > **20% MoM** without approval; reallocation within the current budget is allowed.

## Support & Success
- **SLA:** First reply within 24h on business days.
- **Automation:** Chatbot/assistant is allowed for L1 triage; must offer human handoff.
- **Knowledge base:** Must be kept current if deflection tactics are proposed.

## Product & Packaging
- **Plan boundaries:** Do not suggest moving critical Enterprise features to lower tiers.
- **Trials vs. freemium:** No permanent freemium at this stage.
- **Price changes:** Can test up/down by **±10%** as an experiment; global list changes need approval.

## Compliance & Privacy
- **PII handling:** No exporting end-user PII to external tools.
- **Data residency:** EU customer data must remain in compliant regions.
- **Email consent:** Honor unsubscribe; store proof of consent for marketing lists.

## Technology & Vendors
- **Infra:** No new core cloud vendors in v1; use existing stack.
- **Analytics:** Use existing product analytics and CRM; adding trackers requires legal review.
- **Payments:** Card processor only (no crypto/wire in v1).

## Experimentation Guardrails
- **Minimum run:** 2 full weeks or **≥ 500 user exposures** (whichever later) unless hitting stop-loss.
- **Stop-loss:** If **negative KPI movement > 10%** vs. control for 3 consecutive days, pause.
- **Concurrency:** Max **2** experiments per funnel stage simultaneously.
- **Primary metrics:** Respect KPI definitions doc; do not “metric shop.”
- **Reporting:** Every experiment must log hypothesis, variant, metric, start/end, outcome.

## Strategy Gating Checks (agents must run these)
1. **Redundancy:** If baseline shows the tactic already active, do not recommend it again (unless proposing an iteration with different scope).
2. **Conflict:** Reject any action that breaches a policy above; propose a compliant alternative.
3. **Feasibility alignment:** If ADK classifies goal as *Unrealistic*, propose a target/date adjustment **before** tactics.
4. **Resourcing:** If a tactic requires new teams/tools beyond scope, mark **Needs Approval**.
5. **Evidence:** Each recommended action must cite (a) baseline doc ID(s) for fit, and (b) source snippet(s) for rationale (RAG or cached web).