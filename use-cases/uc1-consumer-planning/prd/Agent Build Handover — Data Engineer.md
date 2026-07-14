# Agent Build Handover — Data Engineer

**Project:** SenseAct / Forward Deploy Consulting — UC1 Show & Tell (Demand Forecasting)  
**Audience:** Data engineer joining the build  
**Prepared by:** PM (from May 28 meeting + agents architecture discussions)  
**Date:** June 10, 2026  

---

## 1. What you are building

Build the **data foundation and agent inputs** for UC1: consumer signals → planning-native insights at **SKU × region × week** grain. Planners review and approve/reject recommendations — **nothing auto-applies in V1**.

**North star for demo:** Run 1 (baseline forecast, no consumer signals) vs Run 2 (same scope with Forward Demand Signal applied) → measurable WMAPE improvement on a 12-week window.

**Guiding principle (Basu, May 28):** Sense → Reason → Act  
Agents **reason and route**. Heavy aggregation, joins, and model scoring stay in **BigQuery / Python / notebooks** — not inside the LLM.

---

## 2. Architecture (end to end)

```
Upstream (CRM, Loyalty, Clickstream, Campaign, OMS)
  → SFTP / GCS landing bucket
  → BQ Medallion (Bronze → Silver → Gold)
  → Forecast + signal models (BQ ML / Python)
  → Orchestrator (reads signal delta)
  → Specialist agents (Demand Sensing, Replacement Cycle, Inventory Policy)
  → Traceability → Publisher
  → Insight API + Inquiry API + Pub/Sub
  → Planner UI (approve / reject) → audit store
```

**Your primary deliverable:** clean Gold-layer tables, synthetic demo data, entity contracts, and the translate layer that turns consumer signals into **planning units** before agents or PDH consume them.

**Basu owns:** agent orchestration code, APIs, demo UI shell.

---

## 3. Agents inventory (7 Cloud Run agents)

| Agent | Role | Trigger |
|-------|------|---------|
| **OrchestratorAgent** | Gatekeeper + traffic controller — checks data quality/freshness, reads signal deltas, routes to specialists | Hourly (Cloud Scheduler → Pub/Sub) |
| **DemandSensingAgent** | Anchor agent — intent + loyalty + campaign → SKU × geo demand scores → `units_intent_adjusted` | Routed by Orchestrator |
| **ReplacementCycleAgent** | Repurchase likelihood by segment × SKU (e.g. shoe mileage, repeat cadence) | Parallel with Demand Sensing |
| **InventoryPolicyAgent** | Business rules — marries demand + replacement signals into safety stock recs | After specialist agents |
| **TraceabilityAgent** | Assembles recommendation envelope with full lineage (inputs, model version, drivers) | Before publish |
| **PublisherAgent** | Emits `RecommendationEmitted` to Pub/Sub + Insight API store | Last in hourly loop |
| **InquiryAgent** | On-demand NL planner Q&A via Inquiry API (separate from hourly loop) | Planner request |

**Phase 2 (out of scope for V1):** Promotion Optimization Agent, Store Execution Agent.

**Planner-facing modes (May 28):**
- **Insight API (push)** — recommendations surface for active category/SKU/region; planner must approve or reject
- **Inquiry API (pull)** — planner asks “what’s driving demand for SKU X in Chicago?” with traceability

---

## 4. Tech stack

| Layer | Options (any is fine) |
|-------|----------------------|
| **Data platform** | GCS landing → BigQuery medallion; Cloud Run on file drop |
| **Agent framework** | Google ADK, LangChain, or LangGraph |
| **LLM** | Mix per task; ADK supports routing to different models |
| **Models** | BQ ML or Python forecast + signal models on Gold — agents consume outputs |
| **Agent data access** | MCP server or thin Python service exposing Gold tables / DataFrames |
| **Messaging** | Pub/Sub for downstream; REST for Insight / Inquiry APIs |
| **Storage format** | Parquet for high-volume intermediates |
| **Synthetic data** | Required for demo — end-to-end if no client feeds |

**Basu’s rule (May 21):** If it’s a pandas computation, it’s a Python script. Agents only when genuine reasoning is needed.

---

## 5. Requirements (non-negotiable)

### Data

1. **Canonical Gold contract** — agents read Gold tables matching entity contract (product SKU, style variant, location/store, customer segment, etc.).
2. **Planning-native translation** — consumer signals in **units, SKU, region, week** — not raw marketing scores (CLV, churn probability).
3. **Identity-resolved signals** — one person = one customer; identity match rate is a data-quality gate (>80% in production spec).
4. **Assume worst case** — client may not have clean data; build medallion + synthetic data for demo. If client already has a mart, they satisfy Gold contract and skip layers above.
5. **Entity domains to build (Parul):** Member/Consumer, Product, Sales Orders, Clickstream — minimum columns + KPIs per domain.

### Agent / product

6. **Traceability on every recommendation** — geo scope, signal window (expiry/decay), input signals used, baseline vs adjusted forecast.
7. **Human-in-the-loop** — planner explicitly approves/rejects; write to **approval audit store** (V2 learning loop stores now, trains later).
8. **Recommend-only** — no auto-apply into planning systems in Phase 1.
9. **Show & Tell POC scope** — 1–2 regions (e.g. Chicago vs California), 1–2 product lines, one demographic cut; hero SKU story (Targhee IV × PNW × W42–48).

### Value measurement

10. **WMAPE dashboard:** `Σ|actual − forecast| / Σ actual` — 12-week baseline without signals vs with signals.

---

## 6. Gold mart vs PDH (Planning Data Hub)

| Term | Meaning |
|------|---------|
| **Gold mart** | Any curated table in the Gold layer of medallion (Bronze → Silver → Gold) |
| **PDH** | The **planning hub’s** Gold tables at forecast grain — e.g. `DemandForecast` with `units_historical`, `units_intent_adjusted`, `units_final` |

PDH Gold **is** a gold mart. Not every gold mart is PDH.

**Other Gold hubs:** Member/Consumer, Clickstream, Product/OMS — translated **into PDH** before planner UI and agents work at planning grain.

**For demo:** “Pre-load gold marts” mostly means **pre-load PDH** with Run 1 and Run 2 rows. Consumer signals land as PDH columns (`units_intent_adjusted`) after the translate layer.

---

## 7. OrchestratorAgent — deep dive

### Why it’s first

Hourly loop: **Cloud Scheduler → Pub/Sub `agent-orchestration-hourly` → OrchestratorAgent**

Nothing else runs until Orchestrator passes gates and builds an execution plan.

### What it checks (production)

**Bucket 1 — Gates (fail = skip entire run)**

| Check | Threshold | Source |
|-------|-----------|--------|
| Gold mart freshness | < 2 hours | `intent_signal_hourly`, `member_sales_attributed`, `forecast_baseline` |
| Identity match rate | > 80% | MDM join quality |
| Schema validation | 100% pass | Bronze/Silver ingest |
| Model version | Current BQML version | `ml.*` scoring tables |

**Bucket 2 — Signal delta**  
Reads scopes where intent, loyalty, or campaign signals moved since last run. Does not rescore everything.

**Bucket 3 — Dedup**  
Same SKU × region × week with pending recommendation → skip publish.

### Execution plan (order)

```
OrchestratorAgent
  ├── DemandSensingAgent       (parallel)
  ├── ReplacementCycleAgent    (parallel)
  ├── InventoryPolicyAgent     (depends on both)
  ├── TraceabilityAgent
  └── PublisherAgent
```

### Static data / Show & Tell — demo mode

Static synthetic data **breaks** production freshness gates. Do not run production Orchestrator as-is for demo.

**Recommended approach:**

| Phase | Orchestrator | What planner sees |
|-------|--------------|-------------------|
| **POC v0** | Not running — UI toggle reads static Run 1 / Run 2 from PDH or JSON | Same grid delta, same insights |
| **POC v2** | `DEMO_MODE=true` — runs once against pre-staged Gold | Real trace_id, real recommendation envelope |
| **Production** | Hourly scheduler, all gates live | Client deployment |

**Pre-stage for demo (minimum):**

| Table / artifact | Content |
|------------------|---------|
| `gold.forecast_baseline` | Run 1 — Targhee IV, PNW, W42–48 |
| `gold.intent_signal_hourly` | Pre-baked intent lift per SKU × week |
| `gold.member_sales_attributed` | Member vs guest split |
| `gold.signal_delta` | Rows flagging changed scopes (e.g. `STY-TARGHEE-IV × REG-PNW = delta_detected`) |
| `gold.recommendations` | Optional — pre-baked Run 2 with trace_id and drivers |

Set all `updated_at` to a fixed demo timestamp so freshness passes if gates run.

**Demo mode behavior:**

| Production check | Demo behavior |
|------------------|---------------|
| Freshness < 2h | Bypass or always pass |
| Identity match > 80% | Bypass (synthetic = 100%) |
| Hourly scheduler | Disabled — trigger on UI “Rerun” only |
| Signal delta | Read pre-staged `signal_delta` table |
| Sub-agents | Option A: real agents on static Gold · Option B: read pre-baked outputs (faster) |

**Toggle flow (POC v2):**

```
Planner toggles "Consumer signals ON" → Rerun
  → Orchestrator (demo mode)
  → reads signal_delta for scope
  → routes DemandSensing + ReplacementCycle
  → InventoryPolicy → Traceability → Publisher
  → UI grid: 1,850 → 2,400 units; Panel 3 insights populate
```

---

## 8. DemandSensingAgent — deep dive

### One-line job

Reads intent, loyalty, and campaign signals → detects demand shifts **4–8 weeks before sales** → outputs SKU × geo probability scores → proposes `units_intent_adjusted` on PDH.

### Sub-agents and inputs

| Sub-agent | Input mart | What it looks for |
|-----------|------------|-------------------|
| **ClickstreamIntent** | `IntentEvent` (Silver → aggregated) | Search, PDP, add-to-cart, wishlist, abandon |
| **LoyaltySegment** | `CustomerSegment` | Tier shifts, engagement, segment migration |
| **CampaignResponse** | `CampaignResponse` | Impressions/clicks/conversions by segment × day |

Inputs are **aggregated** — no PII, no raw clickstream in the agent. Grain in = style/SKU × region × week.

### Outputs

| Output | Where | Field |
|--------|-------|-------|
| Probability scores | PDH / recommendation store | per SKU × region × week |
| Unit adjustment | PDH `DemandForecast` | `units_intent_adjusted` |
| Recommendation card | Insight API / Pub/Sub | `demand_uplift` or `demand_downlift` |

Planner sees **units** and top drivers in Panel 3 — not raw scores.

### Run 1 / Run 2 (demo story)

| Column | Run 1 (signals OFF) | Run 2 (signals ON) |
|--------|---------------------|---------------------|
| `units_historical` | 1,850 total | same |
| `units_intent_adjusted` | null | 2,400 total |
| `confidence_score` | — | 0.82 |
| `consumer_signals_applied` | false | true |

**Proof narrative:** same pipeline, one toggle, +30% uplift (1,850 → 2,400).

### What DemandSensing does NOT do

- Build baseline forecast (`units_historical` = OMS + promo calendar)
- Model repurchase windows (ReplacementCycleAgent)
- Set safety stock (InventoryPolicyAgent)
- Auto-apply forecasts
- Answer planner NL questions (InquiryAgent)

---

## 9. Scoring logic — agreed vs placeholder

**Important:** Intent event weights in the Planner Loop PDF are **blueprint placeholders**, not validated in May 28 meeting.

| Concept | Status | Notes |
|---------|--------|-------|
| DemandSensingAgent as UC1 anchor | **Agreed** | Basu + May 28 + UC1 doc |
| 4–8 week sensing horizon | **Agreed (concept)** | PDF; not validated on client data |
| Sub-agents: ClickstreamIntent, LoyaltySegment, CampaignResponse | **Agreed (architecture)** | PDF agent table |
| Output: `units_intent_adjusted` on PDH | **Agreed for demo** | Show & Tell spec |
| Recommend-only → `units_final` | **Agreed** | Phase 1 everywhere |
| Translate clickstream → **units** (not CLV/churn) | **Agreed** | NFR2 |
| Forward Demand Signal as named data product | **Agreed** | UC1 + ontology |
| **Weights:** browse(0.1), search(0.3), wishlist(0.5), add-to-cart(0.6) | **Blueprint placeholder** | PDF §4 only; Basu said “aggregate user metrics” — no numbers |
| Rolling 7-day intent window | **Blueprint placeholder** | Implied, not specified |
| BQML `demand_sensing_v3` | **Blueprint placeholder** | Example model_id in PDF |
| Top driver % (clickstream 45%, replacement 30%) | **Demo illustration** | Hero SKU story |
| Client “data-to-decision” tuning | **Agreed (future)** | Basu May 21 — customize per client |

**Rule for build:** Use simple weights for demo story; production tuning replaces hard-coded weights with BQML feature importance or client-specific matrix.

---

## 10. Recommendation envelope (canonical format)

Every published recommendation must include:

```json
{
  "recommendation_type": "forecast_adjustment",
  "recommendation_id": "rec-uuid",
  "geo_scope": { "region": "REG-PNW", "store_ids": ["102", "118"] },
  "sku": "STY-TARGHEE-IV",
  "signal_window": { "valid_from": "2026-10-13", "valid_to": "2026-10-20", "decay_days": 5 },
  "baseline_forecast": 1850,
  "adjusted_forecast": 2400,
  "traceability": [
    { "signal": "clickstream_intent", "weight": 0.45, "source_table": "gold.intent_signal_hourly" },
    { "signal": "replacement_cycle", "weight": 0.30, "source_table": "gold.replacement_scores" },
    { "signal": "loyalty_segment_shift", "weight": 0.25, "source_table": "gold.customer_segment" }
  ],
  "confidence": 0.82,
  "status": "pending"
}
```

Planner actions: **approve / reject / override** → audit store.

---

## 11. Build sequence (data engineer)

| Step | Work | Owner |
|------|------|-------|
| 1 | Lock Gold entity schema + column defs (Member, Product, Orders, Clickstream) | Parul defines · **you implement** |
| 2 | Medallion pipelines + stored procedures (Bronze → Silver → Gold) | **You** |
| 3 | Synthetic data generation for demo scope (regions, hero SKU, 12-week window) | **You** |
| 4 | Identity resolution pipeline (`master_id` join) | **You** |
| 5 | Translate layer: consumer Gold → PDH fields (`intent_units_lift`, etc.) | **You** |
| 6 | Forecast + signal models on Gold (BQ ML / Python) | Parul/DS tune · **you pipeline** |
| 7 | Pre-stage `signal_delta`, Run 1 / Run 2 PDH rows for demo | **You** |
| 8 | MCP / data service exposing Gold + PDH to agents | **You** (with Basu on contract) |
| 9 | Agent orchestration, APIs, UI | Basu |
| 10 | WMAPE baseline vs enriched dashboard | Joint |

**Timeline:** ~12 weeks total (Basu, May 28). Data foundations + synthetic data = longest pole. Agent code is relatively fast; testing traceability and tool invocation takes iteration.

---

## 12. What NOT to build for V1

- Inventory / replenishment agents (UC2/UC3)
- Auto-apply insights into client planning systems
- Model retraining from rejection feedback (store audit data only)
- Full Kinexis/O9 integration — static HTML sidecar with approve/reject is enough
- Hourly Cloud Scheduler for static demo (manual rerun / toggle is fine)

---

## 13. Definition of done (Show & Tell)

1. Synthetic data loaded through medallion into PDH at SKU × region × week grain.
2. Run 1 and Run 2 rows exist for hero SKU (baseline vs enriched).
3. Translate layer produces planning-native unit fields from clickstream/member inputs.
4. Orchestrator (demo mode) or UI toggle demonstrates signal ON → enriched forecast + traceability.
5. Five Panel 3 insights in **units language** (not marketing metrics).
6. Planner can approve/reject; decision logged to audit store.
7. WMAPE dashboard shows delta vs 12-week baseline.

---

## 14. Reference documents

| Document | Purpose |
|----------|---------|
| `meetings/2026-05-28 Meeting Summary.md` | Architecture walkthrough (Basu Miro board) |
| `meetings/2026-05-28 Meeting Transcript.md` | Full meeting detail |
| `prd/Retail AI — Use Case 1 — Consumer & Planning Loop.md` | BRD, friction points, agent requirements |
| `show-and-tell/Planner Spec.md` | Demo scope, Run 1/Run 2, PDH fields |
| `glossary/Show and Tell — Planner Grid Glossary.xlsx` | UI + PDH + **Agent_Glossary** tab (agreed vs placeholder status) |
| `glossary/generate_planner_grid_glossary.py` | Regenerate glossary Excel |
| `glossary/Business glossary.xlsx` | Upstream entity definitions (Member, Clickstream, Orders, Product) |
| Planner Loop PDF (Basu) | 7-agent spec, hourly cadence, agent logic table §4 |

**Glossary status values** (see `Agent_Status_Legend` tab):

- `agreed_demo` — safe for Show & Tell static PDH and talk track
- `agreed_prod` — real architecture, not built in demo yet
- `blueprint_placeholder` — in PDF only, not validated in meetings
- `demo_illustration` — hero SKU sample numbers

---

## 15. Open questions for Parul / Basu

1. Final entity column list per domain (in progress on Miro / Business glossary).
2. Exact BQML model approach vs rule-based translate for v1 demo.
3. Leaner demo scope if 12-week timeline slips (Anil flagged holiday-season window).
4. Planner workbench UX reference (Lisa / Kinexis research in progress).

---

*Sources: May 28, 2026 meeting (Parul, Anil, Basu); agents architecture discussion (Planner Loop PDF + Show & Tell specs); PM synthesis June 10, 2026.*
