# Show & Tell — Planner Spec
**Forward Deploy Consulting · Jun 2026**

Single reference: **data flow → planner workflow → UI panels.**

Persona: demand planner (Parvi). Scope: **demand forecast only** — stops before allocation, replenishment, PO.

---

## 1. Data flow (combined)

### Scope boundary

| We own | Client owns (“tap outside the house”) |
|---|---|
| Hub Gold contracts + translate pipelines | Source ingest (POS, OMS, .com, CRM, PLM, ERP) |
| Planning Data Hub + Demand Sensing agent | Raw lakes/marts or adapter access into our contract |
| Planner app + Show & Tell toggle | Systems that consume approved forecast downstream |

- **Medallion:** Bronze → Silver → Gold per hub; skip layers if client already meets Gold contract.
- **Planning read rule:** UI/agents read **Planning Data Hub Gold only** — not raw clickstream or CLV scores.

### Hub inventory

| Hub | Contributes |
|---|---|
| **Product** | `style_id`, `sku_id`, category, season — row identity & filters |
| **OMS / Sales** | Sales history, returns, actuals — baseline forecast |
| **Member / Consumer** | Aggregated segments, member vs guest — translate only, no PII in UI |
| **Clickstream** | Search, browse, cart events — translate only |
| **Planning Data Hub** | Forecast rows, translated signals, session audit — **primary read/write** |

**Merch slice** (read-only into PDH): OTB, sales/margin vs plan by category/season.

### Translate join

Clickstream + Member → **planning units** (not marketing metrics):

| Input | Output on PDH |
|---|---|
| Intent events (search, PDP, cart) | `intent_units_lift` by SKU × region × week |
| Browse + OOS | Browse-to-buy gap → unit adjustment |
| Member vs guest sales | `units_member` / `units_guest` split |
| Repeat cadence | `units_replacement_adjusted` |
| Sales history | `units_historical` (Run 1 baseline) |

**Forward Demand Signal** data product lands in PDH. Agent proposes `units_intent_adjusted`; planner sets `units_final`.

### Gold contract — `DemandForecast`

**Grain:** `sku_id` × `location_id` (or `region_canonical`) × **`week` (date)**

| Field | Purpose |
|---|---|
| `units_historical` | Run 1 — history + promo |
| `units_intent_adjusted` | Run 2 — + consumer signals |
| `units_override` | Planner edit |
| `units_final` | Approved handoff |
| `confidence_score` | Model confidence |
| `consumer_signals_applied` | Run 1 vs Run 2 flag |
| `approved_by` / `approved_at` | Audit |

**Session-level:** `season_code`, `date_from`, `date_to`, category, region.

### What we don’t touch

Upstream ingest · Allocation (UC2) · Replenishment (UC3) · Assortment/line plan · PO/ERP write · Full MFP · Marketing activation · Real-time inventory · PLM/costing (future).

---

## 2. Planner workflow

**Persona:** Demand planner. Excel still used today; app = in-season weekly forecast workspace.

### Session inputs (step 2 — all required)

| Field | Example | Notes |
|---|---|---|
| **Season** | `FA26` | Context + merch plan |
| **Category** | Footwear › Trail | Product scope |
| **Region** | Pacific NW | `region_canonical` |
| **From date** | 2026-10-13 (W42) | Start of forecast window |
| **To date** | 2026-11-24 (W48) | End of forecast window |

**Rule:** Season = *which plan*; **from / to dates** = *which period you’re forecasting*. Grid columns = weeks within that range.

For long-range/seasonal work, same fields — wider date range (e.g. 18 months). Show & Tell uses 8-week in-season window.

### Steps

| # | Action | Output |
|---|---|---|
| 1 | Login → **New session** or resume | Session record |
| 2 | Enter **season, category, region, from date, to date** | Scope locked |
| 3 | Load **merch context** + **baseline grid** for date range | Run 1 |
| 4 | Review grid; optional **overrides** by week | Draft |
| 5 | Toggle **consumer signals ON** → **Rerun** (same dates) | Run 2 |
| 6 | Review **exceptions + insights** (units language) | Pending review |
| 7 | **Accept enriched** / **Keep baseline** / keep overrides | Decision |
| 8 | **Save session** | `units_final` → PDH Gold |

### Session states

`draft` → `pending_review` → `approved` · or `baseline_only` (Run 1 saved for demo)

### Show & Tell (5 min)

1. New session: FA26 / Trail / PNW / **Oct 13 – Nov 24**  
2. Signals **OFF** — baseline total (e.g. 1,850 units)  
3. Toggle **ON** — enriched total (e.g. 2,400) + insights  
4. **Accept enriched** → **Save**  
5. “Forecast written to PDH; buy/allocation consume downstream — not in this app.”

### Handoff

Approved rows at grain **SKU × region × week (date)** → client planning system / buyers.

---

## 3. Design panels

### Screen map

```
Home (sessions)
  → Wizard: Season · Category · Region · From · To
  → Workspace (3 panels)
```

### Workspace layout

```
┌ Top bar: season · category · region · from–to · [Signals OFF|ON] · Save ─┐
├ Panel 1 ──┬ Panel 2 (main) ──────────────┬ Panel 3 ───────────────────────┤
│ Merch     │ Forecast grid               │ Signals + HITL                 │
│ context   │ SKU × week (within dates)   │                                │
└───────────┴─────────────────────────────┴────────────────────────────────┘
Footer: Forecast only — allocation / replenishment / PO not built here.
```

### Panel spec

| Panel | Source | Shows | Edit? |
|---|---|---|---|
| **1 — Merch context** | Merch slice + Season | OTB left, YTD sales/margin vs plan, note | No |
| **2 — Forecast grid** | PDH + Product + OMS | Baseline, enriched (if ON), actuals, Δ, override | Overrides only |
| **3 — Signals + HITL** | PDH translated | Exception queue, 5 insights, confidence, Accept / Keep | Approve |

### Wizard (required fields)

1. Season  
2. Category  
3. Region  
4. **From date**  
5. **To date**  

Optional preset: “Next 8 weeks” / “Full season” (still stores explicit dates).

### Top bar

- Display: season, category, region, **from – to** (and week labels on grid)  
- **Consumer signals** toggle → rerun same date range  
- **Save session**

### Panel 3 — five insights (units only)

Search spike · Browse-to-buy gap · Cart abandon · Member vs guest · Replacement cadence

### Out of scope (don’t build)

Allocation map · Replenishment · Style bank · PO export · Raw clickstream / CLV in grid

---

## 4. Copy for UI build (Anil)

### B — Session workflow

Login → **Start planning session** → pick **season**, **category**, **region**, and **from / to dates** (forecast window; grid columns = weeks in that range) → load read-only **merch context** (OTB, plan vs actual) and **forecast grid** from Planning Data Hub Gold for that window → review **exceptions** and **signal explanations in units** (not marketing metrics) → **Accept enriched** / **Keep baseline** / optional **week-level overrides** → **Save session** so approved `DemandForecast` rows (`units_final`, confidence, audit) write back to PDH Gold for downstream planning systems and Show & Tell. No POs, transfer orders, or allocation from this app.

### C — Data + Show & Tell

UI reads **hubs at Gold**, not raw POS/Adobe: **Product Hub** (SKU/style), **OMS Hub** (history & actuals), **merch slice** (targets), **Planning Data Hub** (forecast + translated signals). Clickstream and Member hubs feed PDH only via translate — never shown raw in the grid. **Consumer signals toggle OFF** = Run 1 (`units_historical`, history + promo calendar). **ON** = Run 2 (same season, category, region, **dates** — rerun without re-entering filters; adds Forward Demand Signal at planning grain → `units_intent_adjusted`). Default **Run 1** on open; sales story = **delta** on the same grid. Hindsight (forecast vs actual), ops dashboards, and deeper merch edit come later.

---

## Related artifacts

- [Planner UI Wireframe](./UI%20Wireframe.md) — panel detail + sample SKU data  
- [Planner Application Flow](./Application%20Flow.md) — meeting notes, Anil paragraphs, build phases  
- [Connected loop dataflow](../../../diagrams/connected_loop_tobe_dataflow.md) — hub diagram  
- Interactive canvas: `canvases/demand-planner-show-tell-wireframe.canvas.tsx`

---

*Forward Deploy Consulting · Jun 2026*
