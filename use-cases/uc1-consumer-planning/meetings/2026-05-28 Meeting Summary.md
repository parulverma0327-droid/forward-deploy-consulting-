# Meeting Summary — May 28, 2026

**Participants:** Parul Verma, Anil Balwanti, Basu  
**Purpose:** Basu's Miro board walkthrough — detailed technical architecture review, planning types clarification, timeline reality check

---

## 1. Basu's Miro Board — Architecture Walkthrough

Basu presented a full solution architecture on the Miro board, organized into four main layers:

### Guiding Principle: Sense → Reason → Act
*(Basu renamed "Detect" to "Reason" to better reflect the agent's cognitive role)*

---

### Layer 1: Data Ingestion & Unification (Medallion Architecture)

**Source systems (consumer side):**
- CRM, Loyalty, E-commerce clickstream, Campaign data
- Each source has a defined ingestion frequency (hourly, daily, weekly — configurable per client)
- All data lands via **SFTP into a GCS landing bucket** (simplest possible ingestion for demo)
- Cloud Run functions trigger on new file drops — no polling needed

**BigQuery Medallion layers:**
- **Raw / Bronze** — raw ingested data as-is
- **Silver** — cleaned, normalized, canonicalized
- **Gold** — curated, KPI-aggregated, ready for agents
- Stored procedures / transformations written to move data between layers
- **Approval audit store** also feeds back into the gold layer — planner accept/reject decisions become training signals

**Key design decision (agreed):**
- Assume clients will NOT have clean, pre-processed data — build for the worst case
- If a client already has a clean data mart, they just satisfy the canonical contract at the gold layer and skip everything above
- Blueprint is the same regardless; complexity of implementation varies by client readiness

---

### Layer 2: Agent & Model Layer (Agentic Closed Loop)

**Agents identified:**
| Agent | Role |
|-------|------|
| Orchestrator Agent | Detects signal delta changes, routes to specialist agents |
| Demand Sensing Agent | Aggregates user metrics and demand signals |
| Replacement Cycle Agent | Detects product wear/usage patterns (e.g. 200 miles on running shoes = likely to repurchase) |
| Inventory Policy Agent | Applies business rules (e.g. max 100 units of X in store Y); marries demand + replacement signals |
| Traceability Agent | Assembles the final recommendation envelope with full lineage of why the recommendation was made |
| Publisher Agent | Publishes recommendations to the Planner Workbench via Insight API or Pub/Sub topics |

**Recommendation message structure (canonical format):**
- What is being recommended
- Geo scope (region / store ID)
- Signal window (time decay — signal expires after N days)
- Traceability: which data signals drove this recommendation
- Forecast delta: what the new forecast is vs. baseline

**Feedback loop (V2, not V1):**
- Planner approval/rejection rates captured in audit store
- Rejection patterns used for model drift detection
- Model retrained automatically based on rejection signals

---

### Layer 3: Planning Workbench / UI (Sidecar Model)

**Two delivery modes:**
1. **Insight API (push)** — recommendations surface automatically as planner works on a category/SKU/region; planner must approve or reject each one (V1: no auto-apply)
2. **Inquiry API (pull / chatbot)** — planner asks on-demand questions (e.g. "what is driving demand for this shoe in Chicago?") and receives answer with traceability

**UI approach options discussed:**
- **Chrome extension / sidecar** — overlays on top of existing tools like Kinexis, Anaplan, or O9 without requiring integration; reads planning context from the active tab
- **Separate web/desktop tool** — standalone for clients with InfoSec restrictions
- **Native integration** — publish via Pub/Sub into client's own data mart; their UI queries it natively

**For show & tell:** Build a simple custom planner UI (even a static HTML mockup) that demonstrates the approve/reject workflow and shows the before/after forecast comparison.

---

### Layer 4: Value Measurement (North Star KPI)

**Formula: WMAPE (Weighted Mean Absolute Percentage Error)**

```
WMAPE = Σ |Actual - Forecast| / Σ Actual
```

**How it works in the demo:**
1. Run 12-week historical data through pipeline **without** consumer/agent signals → establish baseline WMAPE
2. Run same 12-week window **with** consumer signals turned on → calculate new WMAPE
3. Show the delta as a dashboard — this is the proof of value

**Target:** 5–15% improvement in forecasting accuracy (per industry benchmarks; Parul's document cited 5–10%)

**Caveat:** The true validation only comes after the full sales cycle completes — the demo shows the projected improvement, not the realized one.

---

## 2. Planning Types Clarification (Parul)

Basu asked for clarity on what "planning" covers — Parul walked through all types:

| Planning Type | What It Does | Frequency | In Scope? |
|--------------|-------------|-----------|-----------|
| **Demand Forecasting** | How many SKUs/quantities per region/store for next season | Seasonal (2–3 month planning cycle) | **Yes — UC1 MVP** |
| **Assortment / Merchandising Planning** | Which products to offer (product mix decisions) | Seasonal | Future |
| **Materials Planning** | Supplier lead times, raw material availability | Per PO cycle | Future |
| **Buy Plan / PO Placement** | When to place purchase orders to hit manufacturing timelines | Per season | Future |
| **Inventory Planning** | Stock levels across DCs and stores | Monthly | **UC2** |
| **Replenishment** | Store-to-store / DC-to-store restocking | Weekly / twice weekly | **UC3** |

**Key nuance on data freshness:**
- Demand forecasting (UC1): 24-hour data lag is acceptable — planning cycle is months long
- Replenishment (UC3): 24-hour lag is a real problem — stock-outs are immediate revenue loss
- The "24 hours too late" line in Parul's document was specifically relevant to replenishment, not demand forecasting

**Demand forecast granularity:** Output is at product × region × DC × store level. Also rolled up to total for supplier-facing forecasts. Demographic cuts (age, gender) also available at Nike-scale.

**Nike context:** 18-month concept-to-store lead time; the critical 3-month planning window is when data quality and signal timing really matters — hard deadline before POs must be placed.

**Mid-market vs. brand distinction (Anil):** For a retail chain (American Eagle, smaller regional), inventory is the day-to-day pain point more than demand forecasting. Grocery is even more real-time (perishable). But UC1 / demand forecasting is still the show & tell anchor.

---

## 3. Show & Tell Scope (Agreed)

**UC1 MVP — Demand Forecasting only**

Suggested POC scope:
- One region (e.g. Chicago vs. California — two regions for contrast)
- One or two product lines
- Add one demographic factor (e.g. age) as a consumer signal
- Show: baseline forecast → turn on consumer signals → improved forecast
- Simple planner UI with approve/reject — even a static HTML page is fine for demo purposes

Parul to research planner workbench UX (Kinexis / similar tools) to ensure the demo UI isn't "total bogus" in front of a client. Will talk to Lisa (Nike contact) for guidance. YouTube research also viable.

---

## 4. Entity Contracts — Parul's Deliverable

Basu's Miro board has a placeholder entity list (generated via Gemini for footwear industry). **Parul to review and finalize.**

**Entities identified (draft — needs Parul's validation):**
- Customer Master / Aggregation
- Customer Segment
- Product SKU
- Style Variant
- Location / Store
- *(others TBD)*

**Parul's plan for data definitions:**
- Create tables for each domain: **Member/Consumer, Product, Sales Orders, Clickstream**
- Each domain: multiple tables with minimum required columns + KPI fields
- Column-level definitions (value types) — full semantic definitions to come later as ontology
- Start on Miro board directly (so everything is in one place)
- **Ontology document deferred** — details first, ontology later

---

## 5. Timeline Reality Check

Basu's honest assessment: **End of June is not realistic working part-time.**

**Basu's estimated timeline: ~12 weeks**

| Component | Estimated Effort |
|-----------|-----------------|
| Data foundations (pipeline, medallion, synthetic data) | Most effort |
| Models (forecast + signal) | 2 weeks aggressive; tuning from 80%→90% takes iteration |
| Agent development | Relatively fast to code; testing/tuning takes time |
| API + UI layer | Straightforward |
| Feedback / KPI / audit loop | V2 — not needed for demo |

**Bottleneck: model tuning.** Building models is fast (80% accuracy out of the box). Getting to production-ready accuracy (90%+) requires data science iteration — acknowledged gray area for both Basu and Parul.

**Synthetic data generation** was not in Basu's plan — needs to be added and accounted for.

**Potential resource:** Parul has a former data engineer from her Nike team who may be able to help with data pipeline and synthetic data generation work. Parul to discuss.

**Anil's concern:** Retail holiday season planning starts around August/September — must land first client conversation before then or lose the window until Q1 next year.

**Anil asked:** Is there a leaner version? Will think it through. No answer yet.

---

## 6. Anil's Work Situation

- Anil's entire practice has been given to a new practice manager (internal reorg)
- Transitioning now; one client project ending this week
- New manager wants to schedule for Monday
- Uncertainty about bandwidth going forward — flagged but not fully resolved

---

## 7. Action Items

| Owner | Action | Due |
|-------|--------|-----|
| Parul | Create entity tables with columns for Member/Consumer, Product, Sales Orders, Clickstream domains | ASAP |
| Parul | Add entity definitions to Miro board (not a separate document) | ASAP |
| Parul | Talk to Lisa re: planner workbench UX (how planners actually work in Kinexis/similar tools) | Next day |
| Parul | Research planning workbench UI on YouTube / Kinexis.com if Lisa can't help | This week |
| Parul | Discuss data engineer resource with Anil — scope what he could take on | This week |
| Parul | Create planning types slide (all swim lanes + which is UC1 anchor) | Pending from May 21 |
| Basu | Think through whether a leaner/scoped-down demo version is feasible | Async |
| Basu | Add synthetic data generation to the timeline estimate | Async |
| All | Agree on realistic revised timeline given part-time constraints | Next meeting |
