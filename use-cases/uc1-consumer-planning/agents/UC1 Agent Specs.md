# UC1 Agent Specs

**Dataset:** `demandsensinglayer.dsl_dataset`  
**Grain:** product_cd × region × week (planning)  
**Phase 1:** Recommend-only — planner approves before `units_final`

**BigQuery deployment:** Forecast Signal = Agent catalog + scheduled query. **Orchestrator = Cloud Run agent** (same pattern as DS/RC). See [`agents/BQ_DEPLOYMENT.md`](BQ_DEPLOYMENT.md).

---

## 1. ForecastSignalBQAgent

**Role:** BigQuery-native agent on Gold hubs. Detects scopes where consumer or forecast signals changed since the last agent run, writes `signal_delta`, and answers on-demand planner questions (Inquiry path) via NL→SQL on the same datasets. Does not score unit lifts, route specialists, or publish recommendations.

**Status:** Deployed in BigQuery — Agent catalog (Inquiry) + scheduled query `UC1 – refresh signal_delta` (`glossary/bq_refresh_signal_delta.sql`)

### Input tables and fields

| Table | Fields | Why BQ agent reads them |
|-------|--------|-------------------------|
| `Clickstream Agg` | `product_cd`, `region`, `week`, `weighted_intent_score`, `search_count`, `pdp_view_count`, `cart_add_count`, `last_updated_dt` | Detect intent spikes/drops vs prior snapshot |
| `DemandForecast_AsIS` | `product_cd`, `region`, `week`, `units_forecast`, `last_updated_dt` | Baseline movement + freshness context |
| `Member Hub` | `region`, `ds_model_refresh_dt`, `membership_tier` | Segment-shift context per region |
| `agent_run_history` | `run_id`, `completed_at`, `scope_json` | Last-run boundary for delta detection |
| `Geo Region` | `enterprise_region`, `region_canonical` | Map source region labels to planning grain |

### Runtime computation (each hourly run)

1. **Last-run boundary** — `MAX(completed_at)` from `agent_run_history` where `run_status = completed`; first run uses 24h lookback.
2. **Intent delta** — compare current `Clickstream Agg` to prior snapshot per `product_cd × region × week`; emit row when `weighted_intent_score` change ≥ threshold (demo: 15%).
3. **Baseline delta** — compare `DemandForecast_AsIS.units_forecast` vs prior; emit when change ≥ threshold (demo: 10%).
4. **Classify** — set `delta_type` = `intent_spike` \| `intent_drop` \| `baseline_shift` \| `member_model_refresh`.
5. **Write** — append/merge rows to `signal_delta` with `detected_at = CURRENT_TIMESTAMP()`.
6. **Inquiry path (on demand)** — same BQ agent; planner NL question → SQL on Gold → structured answer (separate trigger, not hourly).

### Output — writes `signal_delta`

**Grain:** `product_cd × region × week × delta_type` (one row per detected change per run cycle)

| Field | Description |
|-------|-------------|
| `signal_delta_id` | Row PK (UUID) |
| `product_cd` | Style + color where signal moved |
| `region` | Enterprise region from source hub (mapped via Geo Region) |
| `region_canonical` | Planning region (e.g. US-PNW) |
| `week` | Affected forecast week |
| `delta_type` | Change class — `intent_spike`, `intent_drop`, `baseline_shift`, `member_model_refresh` |
| `delta_magnitude` | Size of move (e.g. % change in weighted intent or units_forecast) |
| `source_table` | Hub that triggered the row — `Clickstream Agg`, `DemandForecast_AsIS`, etc. |
| `detected_at` | UTC timestamp when BQ agent wrote this row |
| `prior_value` | Metric before change (audit) |
| `current_value` | Metric after change (audit) |

### Does NOT

- Run gates or issue `run_id` (OrchestratorAgent)
- Compute `intent_units_lift` or `replacement_units_lift` (DemandSensingAgent / ReplacementCycleAgent)
- Publish recommendations (PublisherAgent)

---

## 2. OrchestratorAgent

**Role:** Hourly traffic controller. Reads `signal_delta` from ForecastSignalBQAgent, runs freshness gates, builds `scope_json`, issues `run_id`, and routes specialist agents (RC ∥ DS → IP → Traceability → Publisher). Does not detect signal changes, score forecasts, or publish recommendations.

**Status:** Agent — Cloud Run (`agents/orchestrator/`, `POST /run`). Reads `signal_delta`, writes `agent_run_history`.

### Input tables and fields

| Table | Fields | Why Orchestrator reads them |
|-------|--------|----------------------------|
| `signal_delta` | `product_cd`, `region`, `region_canonical`, `week`, `delta_type`, `detected_at`, `source_table` | Routing input — which scopes to run this hour (from BQ agent) |
| `Clickstream Agg` | `last_updated_dt` | Freshness gate |
| `DemandForecast_AsIS` | `last_updated_dt` | Freshness gate |
| `Member Hub` | `ds_model_refresh_dt`, `region` | Model-refresh gate |

### Runtime computation (each hourly run)

1. **Freshness gates (Bucket 1)** — fail any → `run_status = skipped`, `gates_passed = FALSE`.
   - `Clickstream Agg.last_updated_dt` within 2h
   - `DemandForecast_AsIS.last_updated_dt` within 2h
   - `Member Hub.ds_model_refresh_dt` current for scope regions
2. **Read deltas (Bucket 2)** — load rows from `signal_delta` since last `agent_run_history.completed_at`; if empty → skip.
3. **Build scope** — `scope_json`: `[{product_cd, sku_id, region_canonical, week}, …]` from delta rows + Product lookup.
4. **Issue run** — `run_id = run_{YYYYMMDD_HHMM}_{uuid8}`; `started_at = NOW()`.
5. **Write run record** — `agent_run_history` with `run_status`, `scope_json`, timestamps.

### Output — writes `agent_run_history`

**Grain:** one row per `run_id`

| Field | Description |
|-------|-------------|
| `run_id` | Run PK — FK on all downstream agent tables |
| `run_status` | `completed` \| `skipped` \| `failed` |
| `gates_passed` | TRUE if Bucket 1 passed; FALSE → specialists do not run |
| `scope_json` | Routed scopes for DS + RC — JSON list of product_cd, sku_id, region_canonical, week |
| `agents_executed` | JSON list — `["BQ","ORCH"]` today; DS/RC/IP/TR/PUB added when wired |
| `started_at` | Run start UTC |
| `completed_at` | Run end UTC |

### Does NOT

- Detect signal changes on Gold (ForecastSignalBQAgent)
- Score intent, repurchase, or safety stock
- Write `demand_forecast_recommendation` or `recommendation`
- Map traceability or publish to Insight API

---

## 3. DemandSensingAgent

**Role:** Reads aggregated clickstream intent and baseline forecast. Converts intent into unit lifts and proposes an enriched forecast for Run 2. Does not build baseline or auto-apply.

**Status:** Built — `agents/demand_sensing/`

### Input tables and fields

| Table | Fields |
|-------|--------|
| `demand_forecast_base` | `product_cd`, `sku_id`, `region`, `week`, `week_start_dt`, `season_code`, `category`, `units_forecast`, `ly_same_week_sales`, `promo_factor` |
| `clickstream_agg` | `product_cd`, `region`, `week`, `week_start_dt`, `search_count`, `pdp_view_count`, `wishlist_add_count`, `cart_add_count`, `weighted_intent_score`, `member_intent_count`, `guest_intent_count`, `top_search_query`, `browse_score` |
| `member_hub` | `member_id`, `region`, `membership_tier`, `clv_tier`, `visit_count_12m`, `order_count_12m` |
| `geo_region` | `enterprise_region`, `region_canonical`, `source_system` |
| `product_global_line_plan` | `product_code`, `style_name` |

*Upstream (not read directly):* `clickstream_base` feeds `clickstream_agg`.  
*Fan-in:* reads `replacement_score` after ReplacementCycleAgent completes (parallel run).

### Runtime computation (each rerun)

All steps on routed scope (`product_cd` × `region` × `week`). Intermediates (`weighted_intent_score`, `intent_to_units_factor`) are computed in-agent — not separate glossary tables.

1. **Weighted intent** — from `Clickstream Agg` event counts × intent weights:
   - `weighted_intent_score = (search_count × 0.2) + (pdp_view_count × 0.4) + (wishlist_add_count × 0.8) + (cart_add_count × 1.0)`
   - Demo weights in `agents/demand_sensing/config.py`; production = BQML or client matrix.
2. **Intent → units factor** — `intent_to_units_factor = AVG(units_forecast / weighted_intent_score)` at grain from `DemandForecast_Base` + Clickstream; **default 0.019** if no history.
3. **Intent lift** — `intent_units_lift = ROUND(weighted_intent_score × intent_to_units_factor)` → `demand_forecast_recommendation`.
4. **Baseline** — `units_historical = units_forecast` from `DemandForecast_Base` at grain.
5. **RC fan-in** — `replacement_units_lift = SUM(replacement_score.replacement_units_lift)` for same `run_id` + `product_cd` + `region_canonical` + `week` (after RC completes).
6. **Run 2 total** — `units_intent_adjusted = units_historical + intent_units_lift + replacement_units_lift`.
7. **Confidence** — `confidence_score = MIN(1, MAX(0, (weighted_intent_score / 1000) × (1 − guest_share)))` where `guest_share = guest_intent_count / (member_intent_count + guest_intent_count)`.
8. **Run flag** — `consumer_signals_applied = TRUE` when consumer signals enabled for session/run.

### Output

| Output | Field / artifact | Lands in |
|--------|------------------|----------|
| Intent lift | `intent_units_lift` | `demand_forecast_recommendation` |
| Adjusted forecast | `units_intent_adjusted` | `demand_forecast_recommendation` |
| Confidence | `confidence_score` | `demand_forecast_recommendation` |
| Signals flag | `consumer_signals_applied` | `demand_forecast_recommendation` |
| Recommendation header | `recommendation_id`, `baseline_forecast`, `adjusted_forecast`, `delta_units` | `recommendation` (via Publisher) |
| Week detail / drivers | `week_details`, `drivers` | `recommendation_traceability` |

---

## 4. ReplacementCycleAgent

**Role:** Models repurchase likelihood windows by member segment × product. Identifies repeat buyers due to repurchase and translates that into a unit lift. Runs **in parallel with DemandSensingAgent** after Orchestrator. Separate signal path — does not read clickstream and does not replace intent scoring.

**Sub-agent:** `CohortScoringSubAgent` — BQML classification on inter-purchase intervals (demo may use heuristic rules until model is trained).

**Status:** TO-BE

**Glossary inputs only** — no `ConsumerAffinity_Consumer` or `DemandForecast_Consumer` tables. All intermediate features are computed at agent runtime.

### Input tables and fields

| Table (Business glossary) | Fields | Purpose |
|---------------------------|--------|---------|
| `Orders` | `member_id`, `product_cd`, `sku_id`, `transaction_dt_utc`, `sale_qty`, `transaction_type_desc`, `cancel_ind`, `enterprise_region` | 12-month purchase history; inter-purchase intervals |
| `Member Hub` | `member_id`, `membership_tier`, `clv_tier`, `region`, `last_purchase_dt` | Segment / cohort for scoring |
| `Product` | `product_cd`, `category_cd`, `category_nm`, `subcategory_nm`, `sport_activity` | Category cadence grouping |
| `Geo Region` | `enterprise_region`, `region_canonical`, `client_region_cd` | Map order region → planning grain |
| `DemandForecast_Base` | `product_cd`, `region`, `week` | Routed scope from Orchestrator only |

*Does not read:* `Clickstream Agg`, `Clickstream Base`, `ConsumerAffinity_Consumer`, `DemandForecast_Consumer`.

### Runtime computation (each rerun)

All steps run inside the agent on the routed scope (`product_cd` × `region` × `week`). Nothing below is stored as a glossary table.

1. **Filter orders** — last 12 months; `transaction_type_desc = SALES_ORDER`; `cancel_ind = 0`; `member_id IS NOT NULL`.
2. **Join segment** — `Orders.member_id` → `Member Hub` for `membership_tier`, `clv_tier`.
3. **Join category** — `Orders.product_cd` → `Product` for `category_cd` / `category_nm`.
4. **Member × product last purchase** — `last_purchase_dt = MAX(transaction_dt_utc)` per `member_id`, `product_cd`.
5. **Category cadence** — `category_cadence_days = MEDIAN(DATEDIFF between consecutive purchases)` from Orders, grouped by `category_cd` (or `category_nm`).
6. **Cohort score** — `CohortScoringSubAgent` scores repurchase probability by segment × product (BQML on inter-purchase intervals; optional cohort dimension: `sport_activity`).
7. **Due count** — `replacement_due_count = COUNT(member_id)` where `ABS(DATEDIFF(today, last_purchase_dt) − category_cadence_days) ≤ tolerance` at `product_cd` × `region_canonical` × `week`.
8. **Avg repurchase units** — `avg_repurchase_units = AVG(sale_qty)` per member-product repurchase from order history.
9. **Unit lift** — `replacement_units_lift = ROUND(replacement_due_count × avg_repurchase_units)` → `replacement_score`.

**Output field formulas (on `replacement_score`):**

| Field | Formula |
|-------|---------|
| `repurchase_probability` | CohortScoringSubAgent score from steps 1–6 |
| `replacement_due_count` | Step 7 |
| `avg_repurchase_units` | Step 8 |
| `replacement_units_lift` | Step 9 — read by DS for fan-in into `units_intent_adjusted` |

*`[FLAG: usage/wear signal — e.g. product mileage — not in Business glossary; client-specific TO-BE]`*

### Output

| Output | Field | Lands in |
|--------|-------|----------|
| Cohort repurchase probability | `repurchase_probability` | `replacement_score` |
| Members due | `replacement_due_count` | `replacement_score` |
| Avg units per repurchase | `avg_repurchase_units` | `replacement_score` |
| Replacement lift | `replacement_units_lift` | `replacement_score` → blended into `demand_forecast_recommendation` by DemandSensingAgent |
| Trace driver | `replacement_driver` | `recommendation_traceability` (INS-05 narrative) |

RC writes all scores to `replacement_score`. DemandSensingAgent reads `replacement_units_lift` and merges into `units_intent_adjusted` on `demand_forecast_recommendation` once RC completes.

### Does NOT

- Read clickstream or intent scores (DemandSensingAgent)
- Build baseline forecast (`DemandForecast_Base`)
- Write safety stock or inventory policy (InventoryPolicyAgent — UC2)
- Auto-apply forecasts

---

## 5. InventoryPolicyAgent

**Role:** Applies business rules to combine demand sensing and replacement signals into safety stock recommendations. UC2 handoff — marries both specialist outputs after they complete.

**Status:** TO-BE (UC2 scope; included in Miro hourly loop)

### Input tables and fields

| Table | Fields |
|-------|--------|
| `demand_forecast_recommendation` | `product_cd`, `sku_id`, `region_canonical`, `week`, `run_id`, `units_historical`, `units_intent_adjusted`, `intent_units_lift`, `replacement_units_lift`, `confidence_score` |
| `replacement_score` | `product_cd`, `region_canonical`, `week`, `run_id`, `replacement_due_count`, `replacement_units_lift`, `repurchase_probability` |
| `DemandForecast_Base` | `product_cd`, `region`, `week` — baseline reference |
| Inventory / WMS *(TO-BE)* | On-hand, lead time, service level target |

### Output

| Output | Field | Lands in |
|--------|-------|----------|
| Safety stock recommendation | `safety_stock_units` | `inventory_recommendation` |
| Exception priority | `exception_priority_flag` | `inventory_recommendation` |
| Reorder recommendation | `reorder_qty` | `inventory_recommendation` |
| Policy audit | `policy_rule_version`, `inputs_used` | `inventory_recommendation` |

---

## 6. TraceabilityAgent

**Role:** Wraps every recommendation with lineage — source tables, feature drivers, model version, and planner-readable reasoning.

**Status:** Partial — envelope built inside Demand Sensing pipeline; standalone agent TO-BE

### Input tables and fields

| Table | Fields |
|-------|--------|
| `demand_forecast_recommendation` | `run_id`, `product_cd`, `region_canonical`, `week`, `intent_units_lift`, `replacement_units_lift`, `units_intent_adjusted`, `confidence_score` |
| `replacement_score` | `run_id`, `replacement_due_count`, `replacement_units_lift`, `repurchase_probability` |
| `inventory_recommendation` | `run_id`, `safety_stock_units`, `exception_priority_flag` |
| Source table refs | `Clickstream Agg`, `DemandForecast_Base`, `Orders`, `Member Hub`, `Product` |

### Output

| Output | Field / artifact | Lands in |
|--------|------------------|----------|
| Traceability block | `signal`, `weight`, `source_table`, `detail` | `recommendation_traceability` |
| Top drivers | Feature contribution % (e.g. clickstream intent, replacement) | `recommendation_traceability` / INS-01…05 |
| Agent reasoning | NL explanation of adjustment | `recommendation_traceability` |
| Model version | Scoring method / model id | `recommendation_traceability` |

---

## 7. PublisherAgent

**Role:** Publishes finalized recommendations to Pub/Sub and Insight API. Idempotent by `recommendation_id`. Does not apply forecasts.

**Status:** TO-BE

### Input tables and fields

| Table | Fields |
|-------|--------|
| `demand_forecast_recommendation` | `run_id`, `product_cd`, `sku_id`, `region_canonical`, `week`, `units_historical`, `units_intent_adjusted`, `confidence_score` |
| `recommendation_traceability` | `signal`, `weight`, `source_table`, `detail`, `model_version`, `agent_reasoning` |
| `inventory_recommendation` | `run_id`, `safety_stock_units`, `exception_priority_flag` *(UC2 handoff)* |

### Output

| Output | Field | Lands in |
|--------|-------|----------|
| Recommendation header | `recommendation_id`, `recommendation_type`, `geo_scope`, `sku`, `product_cd`, `baseline_forecast`, `adjusted_forecast`, `confidence`, `status` | `recommendation` |
| `RecommendationEmitted` event | Pub/Sub topic | Downstream consumers |
| Insight API row | Planner insight feed | UI |
| Recommendation status | `pending` → `approved` / `rejected` / `overridden` | `recommendation` |

---

## 8. InquiryAgent

**Role:** On-demand planner Q&A — e.g. “What’s driving demand for this SKU in PNW?” Separate from the hourly loop.

**Status:** TO-BE

### Input tables and fields

| Table | Fields |
|-------|--------|
| `demand_forecast_recommendation` | `product_cd`, `sku_id`, `region_canonical`, `week`, `units_historical`, `units_intent_adjusted`, `intent_units_lift`, `replacement_units_lift`, `confidence_score`, `consumer_signals_applied` |
| `replacement_score` | `replacement_due_count`, `repurchase_probability`, `replacement_units_lift` |
| `recommendation` | `recommendation_id`, `status`, `baseline_forecast`, `adjusted_forecast` |
| `recommendation_traceability` | `signal`, `weight`, `source_table`, `detail`, `agent_reasoning` |
| `clickstream_agg` | `search_count`, `pdp_view_count`, `cart_add_count`, `top_search_query`, `weighted_intent_score`, `member_intent_count`, `guest_intent_count` |

### Output

| Output | Description |
|--------|-------------|
| NL answer | Plain-language explanation with trace refs |
| Structured metrics | Units, lift, confidence for requested scope |
| Optional insight card | Same format as push recommendations |

---

## End-of-run tables

Persisted at the end of each hourly agent loop. Input hubs (Orders, Member Hub, Product, Clickstream Agg, DemandForecast_Base) are pre-existing — not created per run.

| Table | Written by | Grain | Key fields |
|-------|------------|-------|------------|
| `signal_delta` | ForecastSignalBQAgent | `product_cd × region × week × delta_type` | `delta_type`, `delta_magnitude`, `source_table`, `detected_at`, `region_canonical` |
| `agent_run_history` | OrchestratorAgent | per `run_id` | `run_id`, `run_status`, `gates_passed`, `scope_json`, `agents_executed`, `started_at`, `completed_at` |
| `demand_forecast_recommendation` | DemandSensingAgent (+ RC blend) | `product_cd` × `region` × `week` × `run_id` | `units_historical`, `intent_units_lift`, `replacement_units_lift`, `units_intent_adjusted`, `confidence_score`, `consumer_signals_applied`, `recommendation_id` |
| `replacement_score` | ReplacementCycleAgent | segment × `product_cd` × `region` × `week` × `run_id` | `repurchase_probability`, `replacement_due_count`, `avg_repurchase_units`, `replacement_units_lift`, `membership_tier` |
| `inventory_recommendation` | InventoryPolicyAgent | `sku_id` × `location` × `run_id` | `safety_stock_units`, `exception_priority_flag`, `reorder_qty`, `policy_rule_version` — **UC2 handoff** |
| `recommendation` | PublisherAgent | per `recommendation_id` | `recommendation_id`, `run_id`, `product_cd`, `sku_id`, `geo_scope`, `baseline_forecast`, `adjusted_forecast`, `confidence`, `status` (`pending`) |
| `recommendation_traceability` | TraceabilityAgent | per `recommendation_id` × signal | `signal`, `weight`, `source_table`, `detail`, `model_version`, `agent_reasoning` |

**Not end of hourly run** — planner HITL write-back (separate): `approval_audit` + `units_final` on accept.

---

*UC1 · Forward Deploy Consulting · Jul 2026*
