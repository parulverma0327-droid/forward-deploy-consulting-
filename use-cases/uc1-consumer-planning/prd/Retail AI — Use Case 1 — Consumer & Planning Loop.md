# Retail AI — Use Case 1
## Demand Planning and Consumer / Member Loop
**Forward Deploy Consulting · May 2026 · Confidential**
**Version:** 0.1 — Draft

---

## Index

1. Dictionary of Terms
2. Use Case and Problem Statement
3. Impact
4. Impacted Domains & Systems
5. As-Is and To-Be Process Flows
6. Blind Spots / Friction Points
7. Solution and Requirements
8. In Scope
9. Out of Scope
10. Assumptions
11. Implementation Approach

*(Business Glossary, Taxonomy, Data Dictionary, Ontology, Semantic Layer — covered in companion Excel workbook)*

---

## 1. Dictionary of Terms

| Term | Definition |
|---|---|
| **Consumer Loop** | The end-to-end flow of customer activity: touchpoints (store, .com, app), transactions, intent signals (browse, search, wishlist), identity resolution, analytics, segmentation, and marketing activation. |
| **Planning Loop** | The end-to-end flow of inventory decisions: product data from Line Plan → Product Data Hub → ERP/WMS/.com, and sales signals back into demand forecasting, allocation, and replenishment. |
| **Connected Loop** | The integrated state where consumer intelligence (intent signals, CLV, Data Science outputs, post-purchase feedback) flows directly into planning decision points. This is the target state this use case builds toward. |
| **Friction Point (FP)** | A specific location in the consumer-planning workflow where a signal exists in one system but fails to reach the system that needs it. Each FP is a scoped, fixable problem with measurable impact. |
| **Master Customer ID (`master_id`)** | A single canonical identifier assigned to a customer by resolving all system IDs (POS ID, .com account, loyalty number, CRM ID) using deterministic matching (email, phone) and probabilistic fallback. Does not exist in most retailers today — must be built. |
| **Guest** | A customer who has transacted but is not enrolled in the loyalty program. Invisible in CRM. May be a high-value repeat buyer with no observable record outside of anonymous POS transactions. |
| **Member** | A customer enrolled in the loyalty program. Has a loyalty ID. May also have a .com account and POS record — but these are not automatically linked to the loyalty ID without an identity graph. |
| **Intent Signal** | A non-transactional customer behaviour on .com or app that indicates future purchase intent: search queries, product page views, wishlist adds, cart adds, cart abandons, category browses. Today these live only in .com analytics tools and never reach Planning. |
| **Forward Demand Signal** | An aggregated, SKU-level demand indicator built from intent signals and replacement cycle data. Represents what customers *will* buy, not what they *have* bought. Feeds the Demand Sensing Agent. |
| **Demand Forecast (Baseline)** | The current-state demand forecast produced by Planning using historical sales data, promo calendars, and seasonal patterns only. No consumer signals included. |
| **Demand Forecast (Enriched)** | The target-state demand forecast that incorporates the Forward Demand Signal, member segment affinity, and Data Science outputs alongside historical sales. |
| **Canonical Data Model** | A standardised, system-agnostic data schema that SenseAct pre-builds for each domain (consumer, planning, product, sales orders). Client-specific source systems connect to the canonical model via adapters — the agent pipeline works off the canonical model and does not need to be rebuilt per client. |
| **Adapter** | A lightweight connector that translates a client's source system data format (e.g. SAP ERP, Oracle, NetSuite) into the canonical schema that SenseAct's agents are pre-built to consume. The only bespoke build per client engagement. |
| **CLV (Customer Lifetime Value)** | Predicted 12-month net revenue from a customer, calculated by a Data Science model. Used to prioritise allocation (send stock where high-CLV customers are concentrated) and personalise offers. |
| **Sell-Through Rate** | Units sold at full price ÷ total units received, by style, at end of season. A key signal of product success or failure — currently never fed back to PLM. |
| **Return Reason Code** | A structured classification of why a product was returned (sizing, quality, changed mind, wrong item, etc.). Currently captured as free text or absent entirely. Must be structured and linked back to Planning and PLM. |
| **Data Product** | A curated, governed, SLA-backed dataset built from one or more entities for a specific consuming team. Examples: Forward Demand Signal (for Planning), Master Customer Profile (for all teams), Returns Intelligence (for PLM). |
| **MCP Server** | Model Context Protocol server — the interface through which AI agents access data. SenseAct pre-builds MCP servers that expose canonical data models to agents. Adapters plug into the MCP server, not into the agents themselves. |
| **Medallion Architecture** | A layered data architecture: Bronze (raw ingested data) → Silver (identity-resolved, standardised) → Gold (business-ready models and aggregated KPIs). The agent operates on Gold-layer data. |
| **Human-in-the-Loop** | A design principle where AI agents propose recommendations that a planner, buyer, or merchant reviews and approves before action is taken. No agent acts autonomously on planning decisions without human approval in Phase 2. |
| **Show & Tell** | SenseAct's POC demonstration format: a simulated retail pipeline run twice — once without consumer signals, once with. The delta in forecast output demonstrates the value of the connected loop to a prospect. |

---

## 2. Use Case and Problem Statement

### Use Case

**UC1 — Consumer → Planning: Disconnected Loops**

Retail planning makes billion-dollar inventory decisions — what to buy, how much, where to send it, when to markdown — using one input: historical sales data. That signal is aggregate, backward-looking, delayed, and incomplete.

Meanwhile, the consumer side of the business generates rich, real-time intelligence about what customers want: what they are searching for, what they are saving, what they are returning and why, and what Data Science models predict they will do next. This intelligence stays entirely within the marketing and analytics stack. It never crosses into operational planning.

The result is predictable and expensive: stock in the wrong locations, promotions targeting the wrong customers, returns repeating the same product mistakes, and the most sophisticated models the company has built producing dashboards that nobody in Planning ever reads.

### Problem Statement

**The core problem: Customer Intelligence is disconnected from Inventory Intelligence.**

The consumer loop and the planning loop run in parallel — each internally functional, each generating data — but with no active connection between them. The consumer loop does not know what Planning decided. Planning does not know what consumers are signalling.

The planning signal that does exist is structurally limited:

- **Aggregate** — the "who bought" is stripped from every transaction before it reaches the forecast model. Planning sees units, not customers.
- **Backward-looking** — it tells you what sold last season, not what customers are searching for right now.
- **Delayed** — POS data arrives in nightly batch files. The signal is always at least 24 hours stale, often more.
- **Incomplete** — guest purchases are invisible (no loyalty record), returns are siloed in OMS, browse intent never leaves the .com analytics platform, and Data Science outputs are never routed to Planning.

### Why This Matters Now

Retail has invested heavily in AI and Data Science. 89% of retailers are piloting AI; only 33% have deployed it at scale. The gap is not a technology gap. It is a data and connection gap. The models exist. The signals exist. The connection between them does not.

This use case builds that connection.

---

## 3. Impact

### Business Impact (Estimated — $1–2B Retailer)

| Impact Area | Metric | Estimated Value |
|---|---|---|
| Forecast accuracy improvement | 3–5% accuracy uplift | $8–12M reduced working capital |
| Inventory distortion reduction | 25–40% overstock reduction | $18–30M markdown avoidance |
| Member stockout prevention | 35% reduction in member-facing OOS | $9–14M recovered revenue |
| Promotion ROI improvement | 15–20% lift on targeted promotions | $4–6M margin improvement |
| Buyer / planner productivity | 40% reduction in analysis time | $3–5M FTE redeployment |
| **Total estimated Year 1 impact** | | **$42M–$67M** |

**Investment:** ~$600K–$900K
**ROI:** 50–75×

### The B-Test: Planning Output Without vs. With Consumer Signals

The impact is best illustrated by running the same planning scenario twice — once with today's baseline data only, once with consumer signals added. This is the SenseAct Show & Tell format.

| Planning Output | Without Consumer Data (Today) | With Consumer Data (SenseAct) |
|---|---|---|
| **Demand forecast (units)** | Based on sales history + promo calendar | Adjusted by browse-to-buy gap, intent signals, member affinity |
| **Buy quantity recommendation** | Flat seasonal curve | Peaks aligned to forward consumer demand signals |
| **Product priority ranking** | Driven by last season's sell-through | Re-ranked by current consumer affinity score |
| **Regional allocation** | History-based or even split | Skewed toward high-CLV customer geographies |
| **Markdown risk flag** | Lagging — identified after sales decline | Leading — high browse + low buy = early markdown signal |
| **Returns forecast** | Not modeled | Predicted by segment behaviour patterns from returns history |
| **Member vs. total demand split** | Not available — aggregate only | Visible — member-driven demand separated from guest demand |

---

## 4. Impacted Domains & Systems

### Domains

**1. Consumer & Member**
The origin of the demand signal that is currently missing from Planning. Includes customer identity, loyalty membership, browse and purchase behaviour, returns, and Data Science outputs (CLV, churn, affinity).

- Customer identity and master ID resolution
- Loyalty / member attributes and activity
- Browse and intent signals (.com, app)
- Transaction and return history at individual level
- Data Science model outputs (CLV score, churn risk, category affinity)

**2. Planning**
The consuming domain. Makes demand forecasts, buy decisions, allocation plans, and replenishment calls. Currently operates on aggregate, anonymous, stale sales data.

- Demand forecasting
- Buy quantity and OTB management
- Allocation and replenishment
- Inventory positioning by geography

**3. Product**
Provides the product dimension that links consumer signals to planning decisions. A consumer browsing "heavyweight parkas" must be matched to a specific style/SKU in the assortment for the signal to be actionable.

- Product Line Plan
- PLM / Product Data Hub
- Item Master / UPC
- Category, style, SKU, size, colorway attributes

**4. Sales Orders**
The transactional record that currently forms the entirety of Planning's input signal. With consumer data added, this becomes one input among several — and can be disaggregated by member vs. guest.

- Store POS transactions
- .com / OMS orders and returns
- Return reason codes (currently unstructured or absent)

### Impacted Systems

| System | Domain | What It Holds | Role in Use Case |
|---|---|---|---|
| POS | Store / Finance | In-store transactions | Source of sales signal; arrival in Planning is EOD batch (FP — batch lag) |
| OMS | .com / Fulfillment | Online orders and returns | Source of online sales + return reasons (currently unstructured) |
| CRM / Loyalty | Marketing | Member profiles, loyalty IDs, campaign history | Source of member identity and loyalty attributes |
| .com Platform | Digital | Browse, search, wishlist, cart events | Source of intent signals — currently siloed (FP2) |
| ERP / SAP | Finance | POs, costs, actuals | Planning system of record for cost and PO data |
| Planning System | Planning | Demand forecasts, allocation decisions | Primary consumer of the connected signal; output system |
| PLM | Merchandising | Product data, style/SKU attributes | Receiver of post-purchase feedback (FP9) |
| Data Lake / Hub | Data Engineering | Central data store, pipelines | Where canonical models live; Bronze → Silver → Gold |
| Identity Graph | Data Engineering | Master customer ID resolution | Prerequisite — resolves 3+ IDs per customer into `master_id` |
| MCP Server (SenseAct) | AI Layer | Canonical data models exposed to agents | Interface between data layer and AI agents; adapter layer plugs in here |

---

## 5. As-Is and To-Be Process Flows

### 5.0 Diagrams

**As-Is — Consumer Loop Data Flow**
![Consumer Loop As-Is](diagrams/consumer_loop_asis_dataflow.png)

**To-Be — Connected Loop Data Flow (SenseAct)**
![Consumer Loop To-Be](diagrams/consumer_loop_tobe_dataflow.png)

---

### 5.1 As-Is: Two Loops That Do Not Connect

#### The Consumer Loop — As-Is

The consumer loop captures everything on the demand side of the business. It is internally functional but entirely self-contained.

```
Customer Touchpoints
  └── Store POS  ──────────────────────────────┐
  └── .com / App ──► Browse & Intent Data       │  These signals stay inside
  └── Loyalty     ──► CRM / Member System  ──►  │  the consumer / marketing
                       Customer Analytics        │  stack. None of them
                       Data Science Models       │  reach Planning.
                       Segmentation              │
                       Marketing Activation ─────┘
```

Key gap: every signal generated in the consumer loop — browse intent, loyalty data, CLV scores, churn predictions, category affinity — activates a marketing campaign. It never activates a planning or allocation decision.

#### The Planning Loop — As-Is

The planning loop operates as two sub-loops:

**Product data loop (top):**
```
Line Plan ──► Product Data Hub ──► ERP / WMS / .com / DCs
```

**Sales signal loop (bottom):**
```
Store POS ──► (EOD batch) ──► Planning Systems ──► Demand Forecast
.com / OMS ──────────────────────────────────────► Allocation
ERP ─────────────────────────────────────────────► Replenishment
                                                    └──► (post-season) ──► Line Plan
```

Key gap: the planning loop is complete on paper. In practice it runs on stale (EOD batch), anonymous (member identity stripped), and aggregate (no segment breakdown) data. The most valuable input — what consumers are signalling *now* — does not exist in this loop.

#### The Missing Connection

Four connections should exist between the loops but do not:

| Node | From | To | Signal Missing |
|---|---|---|---|
| Node 1 | Browse / Search / Wishlist (.com) | Planning Demand Forecast | What customers WANT — not just what they bought |
| Node 2 | CRM Segments by geography | Allocation Engine | Send inventory where high-CLV customers are concentrated |
| Node 3 | Inventory Hub (aging stock) | Marketing Activation | Trigger targeted markdown to the right customer segment |
| Node 4 | Post-purchase signals (sell-through, returns, reviews) | Line Plan / PLM | What to make next season based on what customers validated |

Today: all 4 connections are manual or nonexistent.

---

### 5.2 To-Be: The Connected Loop

When friction points are resolved, the consumer loop and planning loop become one continuously learning system. Consumer intelligence flows directly into every planning decision point.

```
Customer Touchpoints
  └── Store POS  ──────────────────────────────────────────────────────────┐
  └── .com / App ──► Intent Signal Pipeline ──► Forward Demand Signal ──► Demand Forecast
  └── Loyalty     ──► Identity Graph ──► Master Customer Profile ──►      Allocation Engine
                       Returns Pipeline ──► Returns Intelligence ──►       PLM / Line Plan
                       Data Science ──► DS Output (routed to Planning) ──► Planning System
```

**Four signal flows that drive the transformation:**

1. **Intent signals + replacement cycle triggers → Demand Forecast:** Planning sees what customers want *before* it shows in sales data. Browse-to-buy gap becomes a leading indicator.

2. **CLV by geography + member segments → Allocation Engine:** Stock goes where the most valuable customers are concentrated — not where it went last season.

3. **Returns data + post-purchase signals → Line Plan / PLM:** What sold at full price and what failed feeds directly into next season's product and size decisions.

4. **Data Science output → Planning Systems:** Intelligence built for marketing now drives operational decisions. Churn signals trigger retention stock positioning. Affinity models inform assortment buys.

---

## 6. Blind Spots / Friction Points

Seven friction points are in scope for Use Case 1. Each represents a point where a consumer signal exists but fails to reach the demand forecasting / planning system that needs it.

FPs that touch current inventory management (allocation, real-time inventory sync), replenishment, PLM product feedback, or inventory-triggered marketing are out of scope for this use case — they are addressed in UC2 (Inventory Planning) and UC3 (Replenishment).

| ID | Description | Type | Priority | Impact on Demand Forecast |
|---|---|---|---|---|
| **FP1** | **Identity Fragmentation** — The same customer exists as 3+ separate records across .com, CRM, and loyalty. No master ID links them. All downstream analytics (CLV, affinity, churn) are built on a fractured sample. Nothing downstream works reliably until identity is resolved. | Data | **High — Prerequisite** | All consumer-to-planning signals are unreliable until this is fixed. Every other FP fix depends on this. |
| **FP2** | **Clickstream Data Siloed in .com** — Browse queries, add-to-cart, save-for-later, and wishlist events sit in Adobe Analytics or GA4. They never reach Planning. The signal that says "customers are searching for a product and not finding it" never triggers a buy decision. | Integration | **High** | Demand forecast misses the forward demand signal entirely. Planning always reacts to past sales, never anticipates future demand. |
| **FP3** | **Repeat Purchase Signal Not Modeled** — For repeat-purchase categories, purchase history contains an implicit replacement cadence. This signal exists in transaction history but is never modelled and never reaches Planning. Demand spikes are reactive, not anticipated. | Data + Integration | **Medium** | Replenishment and buy decisions are triggered after demand appears in sales data — always too late. |
| **FP4** | **Promotion Response Not Fed Back to Planning** — When a promotion runs, Planning has no visibility into which customer segments responded or whether lift was incremental vs. pull-forward. The forecast signal cannot be cleaned after a promotional event. | Integration | **Medium** | Forecast is polluted by promo-induced demand. Planning cannot distinguish genuine demand from discount-driven pull-forward. Accuracy degrades around every promotional period. |
| **FP5** | **Data Science Output Stays in Marketing and Personalization** — Recommendation engines, churn scores, demand signals, and affinity models built by Data Science stay entirely inside the marketing stack. Planning never sees them. The intelligence already exists — only the routing to Planning is missing. | Integration | **High — Highest leverage** | Planning ignores the most sophisticated intelligence the company has built. CLV, affinity, and demand sensing models produce dashboards, not buy decisions. |
| **FP6** | **Guest Purchases Invisible** — Non-loyalty customers are invisible in CRM. All CLV and demand analysis is built on a members-only sample — a biased and incomplete picture of actual customer demand. A guest spending $2,000/year at full price is indistinguishable from noise. | Data + Integration | **High** | Demand forecast is built on a subset of customers. Buy and assortment decisions misrepresent the true demand base. |
| **FP7** | **Member Sales Not Attributed in Planning** — Planning receives aggregate sales data only. The "who bought" is stripped before it reaches the forecast model. A retailer can be losing members in a specific category while total sales look flat — entirely invisible without member attribution. | Integration | **High** | Planning cannot see member-driven demand separately from total demand. Loyalty signal is invisible to the people making buy decisions. |

### Friction Points Deferred to Other Use Cases

*These FPs are out of scope for UC1. They will be numbered FP8 onwards in their respective use case documents.*

| UC1 Ref | Description | Deferred To |
|---|---|---|
| — | Returns Data Siloed in OMS — return reasons never reach PLM or trigger size curve corrections | Future — PLM feedback loop |
| — | Offer Irrelevance — promotions pushed by category, not individual behaviour; inventory-triggered markdown | UC2 — Inventory + Marketing activation |
| — | Post-Purchase Signal Does Not Reach PLM — sell-through, returns, reviews not fed into next season's product design | Future — PLM feedback loop |
| — | Member Rewards Program Used Only for Dashboards — loyalty data not operationalised into planning workflows | UC2 / UC3 — Loyalty operationalisation |

---

## 7. Solution and Requirements

### Solution Overview

The solution has two parts, sequenced deliberately. Data and pipeline issues must be fixed before agents are deployed. Agents built on broken data produce recommendations nobody trusts.

**Part 1 — Fix the Data Foundation (Prerequisite)**
Build the clean, identity-resolved, connected data layer that the agentic workflow will reason over.

**Part 2 — Build the Agentic Layer (Value delivery)**
Deploy AI agents that turn the clean, connected signals into planning decisions — proposed to human planners for review and approval.

### SenseAct Delivery Model

SenseAct brings pre-built canonical data models and pre-built agents to each client engagement. The architecture is:

```
SenseAct Pre-built Layer:
  ├── Canonical Data Models (consumer hub, planning hub, product hub, sales orders hub)
  ├── AI Agents (Demand Sensing, Inventory Planning, Promotion Optimisation, Store Execution)
  └── MCP Servers (data interface layer between canonical models and agents)

Client-Specific Layer (adapter only):
  └── Adapters that translate client source system format → canonical schema
      (e.g. SAP ERP → canonical PurchaseOrder, Shopify → canonical Transaction)
```

The client does not need to rebuild SenseAct's pipeline. They connect their systems at the adapter layer. SenseAct's agents and models work off the canonical format and are already operational.

### Requirements

*Data Requirements and Data Quality SLAs are covered in the Assumptions section and in the companion Data Foundation document.*

#### Business Requirements

| ID | Requirement | FP |
|---|---|---|
| BR1 | Demand forecast must incorporate consumer intent signals (browse, search, wishlist) in addition to historical sales data | FP2 |
| BR2 | Planners must be able to see member-attributed demand separately from total aggregate demand | FP7 |
| BR3 | Forecast signal must be separable into genuine demand vs. promotion-induced demand after any promotional event | FP4 |
| BR4 | Data Science outputs (CLV, category affinity, demand signals) must be routable to Planning — not only to Marketing | FP5 |
| BR5 | All consumer signals reaching Planning must be tied to a single resolved customer identity | FP1 |
| BR6 | Demand analysis must include guest customers, not only loyalty members | FP6 |
| BR7 | Repeat-purchase categories must have a modeled replacement cadence signal available to Planning | FP3 |

#### Integration Requirements

| ID | Requirement | From | To | FP |
|---|---|---|---|---|
| IR1 | .com analytics events streamed in near real-time to central data lake | .com platform (Adobe / GA4) | Data lake | FP2 |
| IR2 | All customer IDs resolved into a single `master_id` via Identity Graph | POS / .com / Loyalty / CRM | Identity Graph | FP1 |
| IR3 | Sales transactions joined to `master_id` before being delivered to Planning system | Identity Graph | Planning data product | FP7 |
| IR4 | Data Science model outputs routed to Planning data products (not only to CRM/Marketing) | DS platform | Planning system | FP5 |
| IR5 | Client source systems connected to SenseAct canonical data model via adapters | Client ERP / .com / Loyalty | MCP Server (canonical layer) | All |

#### Non-Functional Requirements

| ID | Requirement |
|---|---|
| NFR1 | **Human-in-the-loop:** Every agent recommendation must be reviewable and approvable by a planner or buyer before any action is taken. No autonomous planning decisions. |
| NFR2 | **Planning language:** All consumer signals must be translated into planning-native units — units, SKUs, weeks of supply, region — not marketing metrics (CLV score, churn probability). |
| NFR3 | **Access control:** Planning receives aggregated member views only. Individual PII does not flow into Planning systems. |
| NFR4 | **Extensibility:** The canonical data model must be designed as key-value extensible so client-specific attributes can be added without rebuilding the agent pipeline. |
| NFR5 | **Audit trail:** Every agent recommendation must log the signal source, confidence score, and whether it was approved or overridden by the planner. |

### Part 2 — Agentic Layer Requirements

With clean data flowing, four agents are deployed:

#### Demand Sensing Agent (Anchor — Phase 2 start)
**FPs addressed:** FP2, FP3, FP4, FP5, FP6, FP7

- Ingests Forward Demand Signal (from clickstream + replacement cycle model)
- Ingests member segment affinity and Data Science outputs routed from Marketing
- Detects shifts in customer preference 4–8 weeks before they appear in sales data
- Outputs: SKU-level demand probability score with confidence band
- Feeds directly into demand forecast as an additional input layer (`units_intent_adjusted`)
- All recommendations reviewed and approvable by planner (human-in-the-loop)

#### Inventory Planning Agent
**FPs addressed:** FP2, FP5, FP7

- Translates demand signals into buy quantity recommendations and size-specific buy adjustments
- Routes stock toward geographies where high-CLV member concentration is highest
- Proposes actions within human-in-the-loop workflow — every recommendation is reviewable by a buyer or planner

#### Promotion Optimisation Agent
**FPs addressed:** FP4

- Predicts promotion impact by member segment and price sensitivity tier
- Routes promotion response signals back to demand forecast to clean the signal after promotional events
- Separates genuine demand from discount-driven pull-forward in the forecast model

### Output Data Model (Aggregated KPI Tables — Agent Consumption Layer)

The agents do not query raw tables. They query two pre-aggregated output tables built by the data pipeline:

**Table 1 — Demand Signal**
`product_id | region | week | forecast_units_base | forecast_units_enriched | delta | confidence_score | forecast_source`

- `forecast_units_base` = historical sales + promo calendar only (today's state)
- `forecast_units_enriched` = base + intent signal adjustment + member affinity + DS output
- `delta` = the B-test number — this is what SenseAct demonstrates in Show & Tell

**Table 2 — Consumer Affinity**
`product_id | region | segment | browse_score | buy_score | gap_score | clv_tier | member_count`

- `gap_score` = browse_score − buy_score → unmet demand indicator
- High gap = customers want it but aren't finding it or buying it → signals a buy or allocation opportunity

---

## 8. In Scope

- **Use Case 1 only:** Consumer loop + Planning loop connection. UC2 (Inventory Planning) and UC3 (Replenishment) are out of scope for this document.
- **Demand forecasting** as the anchor use case and Show & Tell POC. The 5 planning swim lanes (demand forecasting, inventory planning, supply planning, costing, material planning) are SenseAct's full positioning — the starting point is demand forecasting.
- **Consumer hub and Planning hub** data definitions at the aggregated / hub level. Not individual upstream source tables (45–50 source tables upstream of the hub are out of scope for initial definition).
- **Mid-market retail target** ($100M–$500M revenue): companies that have ERP, loyalty/CRM, and .com systems but have not integrated them. Nike-scale architecture is the reference model; mid-market is the target client profile.
- **Three AI agents:** Demand Sensing (anchor), Inventory Planning, Promotion Optimisation.
- **SenseAct canonical data model** — consumer hub, planning hub, product hub, sales orders hub — with adapter-layer approach for client system integration.
- **Data governance framework** as a deliverable of Phase 1 — ontology, taxonomy, data quality SLAs, ownership RACI.

---

## 9. Out of Scope

- **UC2 — Inventory Planning (monthly):** Stock levels across DCs and stores, allocation engine, POS batch signals to Planning, DC capacity blind spot. Separate document.
- **UC3 — Replenishment (weekly):** DC-to-store / store-to-store restocking, min/max rules, real-time inventory lag. Separate document.
- **Costing loop (future — not a numbered UC):** Landed cost calculation, PLM ↔ Planning cost negotiation, tariff real-time updates. Separate document when scoped.
- **Deferred FPs (UC2/UC3+):** Inventory-triggered markdown activation, loyalty operationalisation — numbered FP8 onwards in UC2/UC3 documents. PLM feedback FPs (returns, post-purchase → line plan) are future scope.
- **Full upstream source system build:** The 45–50 upstream tables that feed the planning hub (individual ERP tables, WMS tables, etc.) are not in scope. SenseAct works at the hub / aggregated level and builds adapters to accept client data at that level.
- **UI / front-end build:** Planning interfaces, dashboards, and merchant-facing UI are not built by SenseAct in Phase 1 or 2. Agents surface recommendations through existing planning tools, email, or Teams/WhatsApp channels. Custom UI is a Phase 3+ consideration.
- **Data science model build (from scratch):** SenseAct assumes client Data Science models exist (CLV, churn, affinity). Phase 2 routes existing outputs to Planning — it does not rebuild Data Science models. If models do not exist, this is a separate scoping conversation.
- **Model fine-tuning and drift management:** Academic knowledge area; not committed to Phase 2 scope. Gray area — to be addressed as the engagement progresses.
- **Full loyalty program redesign:** FP6 and FP12 are addressed at the data routing and agent layer. Redesign of the loyalty program itself (points structure, earn/burn, partner programme) is not in scope.

---

## 10. Assumptions

### Business & Engagement Assumptions

| # | Assumption |
|---|---|
| A1 | Client operates in retail — footwear, apparel, or adjacent category — with a planning function that produces seasonal demand forecasts. |
| A2 | Client has at least one ERP system (SAP, NetSuite, or equivalent), a loyalty/CRM system, and a .com platform. These do not need to be integrated — SenseAct builds the integration. |
| A3 | Consumer data (loyalty, .com analytics, CRM) exists but is siloed. SenseAct builds the pipeline to connect it to Planning — but the data must exist. |
| A4 | Client does not have a master identity graph today. Identity resolution is a Phase 1 build, not an assumption of pre-existing capability. |
| A5 | Client Data Science models (CLV, churn, affinity) exist in some form. If they do not, Phase 2 agent deployment is blocked pending model development — this requires separate scoping. |
| A6 | Planners will participate in a weekly demand signal review session (cross-functional: demand planner + allocation analyst + CRM analyst + buyer). The human-in-the-loop model requires planner engagement. Without it, agent recommendations will not be actioned. |
| A7 | Client can provide data at the hub / aggregated level — either via API access to their data warehouse (e.g. Snowflake) or via a daily file export to a defined location. SenseAct does not require access to raw transactional source systems. |
| A8 | Planning cycle is seasonal (minimum 6-month lead time). Mid-market clients with shorter lead times than Nike's 18-month cycle will see faster time-to-value from the connected signal. |
| A9 | The engagement will have executive sponsorship from both the Planning function and the Marketing/CRM function. The consumer-planning connection is an organisational change as much as a technical one — it requires both sides to participate. |

### Data Requirements

*These define what data must exist and be accessible for the solution to work. Full detail in the companion Data Foundation document.*

| ID | Requirement | Source | FP |
|---|---|---|---|
| DR1 | Resolved `master_id` per customer across POS, .com, loyalty, CRM | Identity Graph | FP1 |
| DR2 | Clickstream events from .com scored by intent weight: search / PDP view / wishlist / cart add / cart abandon | .com analytics → data lake | FP2 |
| DR3 | Forward Demand Signal aggregated per (product × region × week) from intent events | Pipeline output | FP2 |
| DR4 | All sales transactions joined to `master_id` before reaching Planning | Member Sales View | FP7 |
| DR5 | Member sales broken down by loyalty segment and geography | Member Sales View | FP7 |
| DR6 | Replacement cadence model output per product category | Purchase history model | FP3 |
| DR7 | Data Science model outputs (CLV score, category affinity, churn risk) available to Planning data products | DS platform → Planning | FP5 |
| DR8 | Guest transactions probabilistically resolved to `master_id` where possible | Identity Graph | FP6 |

### Data Quality Requirements

*These are the minimum quality thresholds the data must meet before agents are deployed. Falling below alert thresholds pauses agent recommendations for the affected signal.*

| ID | Metric | Target SLA | Alert Threshold | FP |
|---|---|---|---|---|
| DQ1 | Identity match rate (transactions resolved to `master_id`) | >80% | <70% triggers alert | FP1 |
| DQ2 | Guest resolution rate (probabilistic matches) | >50% | <40% triggers alert | FP6 |
| DQ3 | Clickstream event lag (event time → data lake) | <1 hour | >2 hours triggers alert | FP2 |
| DQ4 | Forward Demand Signal coverage (% of active SKUs with a forward signal) | >70% | <50% triggers alert | FP2 |
| DQ5 | Member sales attribution rate | >75% | <65% triggers alert | FP7 |

---

## 11. Implementation Approach

### Methodology: 4A Framework

SenseAct uses the 4A engagement methodology — Assess, Architect, Activate, Accelerate — with a 9-week path to first live use case.

| Phase | Weeks | What Happens |
|---|---|---|
| **Assess** | 1–3 | Map friction across the consumer-planning workflow. Score AI maturity. Confirm which FPs are highest priority for this client. Assess data availability and system landscape. |
| **Architect** | 4–6 | Design the Business Ontology for this client. Map canonical data models to client source systems. Define adapter requirements. Build vs. Buy decisions confirmed. Governance framework designed. |
| **Activate** | 7–12 | Phase 1 (Data Foundation) + Phase 2 (Agentic Layer) builds. Ship 2–3 live use cases in production with demonstrated ROI. Show & Tell POC delivered in Week 7. |
| **Accelerate** | 13+ | Scale what works. Kill what doesn't. Expand to additional planning swim lanes. Build client self-sufficiency and Centre of Excellence. |

### Phase 1 — Fix the Data Foundation (Weeks 4–9)

Priority sequence based on dependency chains — later work builds on earlier:

| Step | Build | FPs Fixed | Dependency |
|---|---|---|---|
| 1 | **Identity Graph** — resolve all customer IDs to `master_id` | FP1, FP6 | None — must be first |
| 2 | **Member Sales Attribution** — join transactions to `master_id` before Planning receives them | FP7 | Identity Graph live |
| 3 | **Clickstream / Intent Signal Pipeline** — .com events → data lake → Forward Demand Signal per SKU | FP2 | Identity Graph live |
| 4 | **Replacement Cycle Model** — mine purchase history for repeat cadence signals per category | FP3 | Member Sales Attribution live |
| 5 | **Data Governance Framework** — canonical definitions, data quality SLAs, ownership RACI, change control | All | Runs in parallel with Steps 1–4 |

### Phase 2 — Build the Agentic Layer (Weeks 8–12)

Agents are deployed as Phase 1 pipelines come online. Demand Sensing Agent is first (the Show & Tell anchor).

| Step | Agent | FPs Addressed | Trigger to Start |
|---|---|---|---|
| 1 | **Demand Sensing Agent** | FP2, FP3, FP4, FP5, FP6, FP7 | Forward Demand Signal live (Step 3 above) |
| 2 | **Inventory Planning Agent** | FP2, FP5, FP7 | Demand Sensing Agent live + Member Sales View live |
| 3 | **Promotion Optimisation Agent** | FP4 | Member Sales Attribution live |

### Show & Tell POC (Week 7 target)

Before full production deployment, SenseAct delivers a working proof of concept that demonstrates the value of the connected loop to the client:

**Format:**
- Simulated retail pipeline with realistic data (product × region × week grain)
- Run 1: Demand forecast without consumer signals (baseline only)
- Run 2: Demand forecast with consumer signals turned on (browse intent + member affinity)
- Delta output shows: forecast adjustment by SKU, regional reallocation, markdown risk flags surfaced

**Purpose:** Give the client a tangible, reviewable output — not a slide — within the first month of the engagement. This is the decision point for production go-ahead.

### Cross-Functional Requirements

The technical build is necessary but insufficient. Three organisational fixes must run alongside the data build:

1. **Shared demand signal in planning language:** Consumer data translated into units, SKUs, weeks of supply — not marketing metrics. Planners cannot action a CLV score; they can action "allocate 200 additional units of style X to Chicago stores."

2. **Weekly demand signal review:** A standing cross-functional meeting (demand planner + allocation analyst + CRM analyst + buyer) to review intent signals against planning position and make decisions together.

3. **Bridge KPI owned by both teams:** One metric that only improves when both Planning and Marketing work together — e.g. member-driven demand accuracy, member stockout rate, or loyalty-driven full-price sell-through. Without a shared KPI, the organisational incentive to maintain the connection degrades over time.

---

*Forward Deploy Consulting · Use Case 1 · May 2026 · Confidential*
*Next sections: Business Glossary + Data Standards, Taxonomy, Data Dictionary, Ontology, Semantic Layer — covered in companion Excel workbook*
