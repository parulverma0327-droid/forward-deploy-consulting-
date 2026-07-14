# Meeting Summary — May 14, 2026

**Participants:** Parul, Anil, Basu  
**Purpose:** Onboard Basu to the retail AI consulting initiative; align on use cases, architecture, and go-to-market direction

---

## 1. Startup Strategy

- **Focus:** Retail only — "inch wide, mile deep" to avoid being generic in a crowded AI market
- **Target customers:** Mid-segment retailers (not large global brands like Nike)
- **Positioning:** Must have a niche wedge. Being a generalist "agentic AI" firm will not earn a seat at the table

---

## 2. Core Problem: Two Disconnected Loops

The central insight driving the use case:

- **Planning Loop** — Upstream systems (line plan, PLM, pricing) → Product Data Hub → Downstream systems (WMS, SAP/ERP, POS, e-commerce) → Demand Planning → feeds back to Line Plan
- **Consumer Loop** — Member activity, clickstream, loyalty, purchase history, returns → currently used only for personalization, promotions, and marketing campaigns

**The gap:** Consumer intelligence is never fed into the planning and forecasting systems. Local events (marathons, school events) and member behavior signals (cart abandonment, browsing patterns, churn) are invisible to demand planners.

Basu confirmed this from a different angle — his Nike supply chain project showed ~$1.4B in losses during COVID due to lack of visibility across contract manufacturers. Multi-tiered ingestion gateways were built to bridge that gap.

---

## 3. Standard Retail Architecture Walkthrough (for Basu)

Parul walked through the end-to-end flow:

1. **Upstream systems** — Line plan, PLM, pricing systems define the product catalog for upcoming seasons
2. **Product Data Hub** — Consolidates upstream product data
3. **Downstream systems** — WMS (inventory), SAP (purchase orders/ERP), POS, e-commerce, regional websites, catalog/label printing
4. **Sales orders** flow from customers through all channels
5. **Demand Planning Hub** — Ingests historical sales + other signals, builds forecasting models, recommends future season assortments back to Line Plan

Every function has its own data hub; regional data laws (e.g., China data staying in China) add complexity. Target clients are mid-market, so they won't have full enterprise stacks.

---

## 4. Consumer Loop Friction Points (Focused on 2 of 12)

**Friction Point 1 — Identity Fragmentation**
- Same customer shops online, in-store, logged in, as guest, across channels
- No unified identity = no unified consumer view
- Data issue + process issue (retailers don't always capture member info at checkout)
- Prerequisite fix before agents can work reliably

**Friction Point 2 — Siloed Clickstream Data**
- Clickstream (browsing, cart additions, abandonment, returns) is captured but only used for personalization/campaign engines
- Confirmed by Parul's conversations with industry contacts: this data does NOT flow into planning systems yet
- This is the core opportunity

---

## 5. Proposed Solution Architecture (High Level, Still Evolving)

- **Do not rebuild pipelines.** Instead, agents query aggregated insight tables (e.g., BigQuery) built on top of existing data
- A **predictive analytics model** sits on top of consolidated clickstream/consumer data
- Agents use **text-to-query** to pull targeted insights (e.g., cart abandonment by region, event-driven demand spikes, demographic trends)
- Insights are persisted (BigQuery, Firestore, or similar) in human- and agent-consumable format
- **Multi-agent architecture:** Sense → Detect → Act
  - Consumer Insights Agent pulls from aggregated clickstream model
  - Demand Planning Agent queries Consumer Insights Agent periodically or on demand
  - Potentially a Validation Agent to cross-check planner assumptions against consumer signals

---

## 6. Show & Tell / POC Design

- Build a **simulated retail pipeline** (line plan → data hub → orders → demand planning)
- Create a **separate simulated consumer loop** (synthetic clickstream, demographic, event data — generated via Python scripts, not raw AI output)
- Demo a **B-test scenario:** Show demand forecast without consumer signals vs. with consumer signals fed in
- Include a **local event trigger** to show real-time signal integration
- Human-in-the-loop: demand planner sees agent-generated insight with a checkbox to accept/ignore it (like autonomous driving with driver override)

---

## 7. North Star & Elevator Pitch Discussion

Three core value pillars identified (already in Parul's document):
1. **Customer Experience** — Right inventory, right channel, right store, based on real buying patterns
2. **Planning Accuracy** — Demand forecasts informed by consumer intelligence
3. **Returns Reduction** — Fewer wrong-size/wrong-product orders = fewer returns (ties back to planning accuracy)

**Pitch direction (Anil):** Lead with planning accuracy + customer data intelligence as a niche, not a generic "we do agentic AI" message. Land on the specific problem, then expand the conversation once in the door.

**Parul's alternative:** Go in as problem-solvers — use the consumer-planning demo as proof-of-capability, then adapt to what the client actually needs.

---

## 8. Future Vision

- Consumer loop → Planning → Inventory → Sourcing & Manufacturing = **fully integrated autonomous planning platform**
- Could evolve into a SaaS-like platform for mid/small retailers who currently plan on spreadsheets and can't afford enterprise tools
- Parul to connect with sourcing/manufacturing contacts to expand knowledge for future use cases

---

## 9. Data Governance & Ontology

- Parul raised: should we document data prerequisites (fixing identity fragmentation, standardizing clickstream schemas, etc.) as a supporting consulting artifact?
- **Decision:** Yes — this is part of the consulting engagement blueprint. Ontology and taxonomy documentation are week-1/2 deliverables in the consulting process model
- **Action for Parul:** Start drafting a data governance framework (ontology, taxonomy, data quality prerequisites) as a companion document to the main pitch

---

## 10. Action Items

| Owner | Action |
|-------|--------|
| Basu | Read through Parul's existing document; form architecture point of view; reconvene in ~1 week |
| Anil | Create WhatsApp group with all three; share Google Drive access with Basu; finish current process diagram by weekend |
| Parul | Add summary + transcript to Google Drive folder with today's date; rename use case to "Use Case 1 — Consumer Planning Loop"; start data governance/ontology draft; continue updating the main document |
| All | Think through North Star KPI — what % improvement in planning accuracy is a credible and compelling claim? |

---

## 11. Next Meeting

Basu to suggest a date after reviewing the document (estimated ~1 week out). Parul and Anil to continue meeting in the interim.
