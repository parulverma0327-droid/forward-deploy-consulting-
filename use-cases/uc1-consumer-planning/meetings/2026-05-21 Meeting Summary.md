# Meeting Summary — May 21, 2026

**Participants:** Parul, Anil, Basu  
**Purpose:** Architecture alignment, accelerator/go-to-market strategy, technology stack decisions, next steps toward POC

---

## 1. Document Review & Status

- Basu reviewed Parul's document; had **qualifier questions only, no blockers** (annotated in blue in the BRD doc)
- Parul and Anil met that morning; Parul has been talking to Nike contacts to fill in use case gaps
- Anil has been coaching Parul on what additional information to extract from her Nike network

---

## 2. Parul's Wednesday Deliverable

An integrated workflow diagram covering:
- **Consumer loop + Planning loop connected** — detailed data flow, not just high-level boxes
- **Data dictionary / business glossary** — what fields/entities are needed from each system (product, planning, sales orders, consumer/member)
- **Friction points** called out within the integrated workflow
- Converted from Word doc boxes into a **Miro visual**
- Parul to provide **data hub schemas** for each domain (consumer, planning, product, sales orders) as a starting point — aggregated/hub-level first, can drill into upstream later

---

## 3. Go-to-Market & Accelerator Strategy (Key Alignment)

The team reached full alignment on positioning:

**What we bring to a client:**
1. **Thought leadership** — a pre-built, opinionated point of view on how a connected retail planning system should work (the "palace blueprint")
2. **Pre-built canonical data models** — standardized schemas for Customer 360, clickstream, line plan, demand planning, etc. (not tied to any specific ERP/platform)
3. **Pre-built agents with skills** — agents already programmed to the canonical interface; only the **adapter layer** gets customized per client
4. **Assessment & readiness framework** — weeks 1–3: assess data availability, AI maturity, system integrations; weeks 4–6: understand business ontology and data-to-decision mapping

**The plumbing metaphor:**
- Canonical pipeline is already built. Client just needs to deliver data at the "front door"
- If they have SAP → adapter translates SAP data to canonical format → our pipeline runs as-is
- If they can only give an Excel file at 7am daily → we build a connector to ingest that → MCP server makes it available as a pandas DataFrame → agent consumes it
- Adapter logic lives in the **MCP server layer only** — agent logic stays untouched

**The "air conditioner" analogy (Anil):** We bring it pre-fabricated. You just plug it into your electrical system and output systems.

---

## 4. Technology Stack (Basu's Input)

- **Orchestration framework:** Google ADK (open source) + A2A protocol, or LangChain/LangGraph
- **Agent architecture:** Skills-based approach — each skill has a 4-line "business card" header; agent loads skill metadata into memory and routes commands to the right skill without full round-trips → minimizes token cost
- **Data processing:** Jupyter notebooks / Python scripts do the heavy lifting (not agents); results made available as pandas DataFrames via MCP server to agents
- **Data format:** Parquet for high-volume, low-memory-footprint data storage
- **Agents are for reasoning only** — Basu is "stingy": if it's a pandas computation, it's a Python script; agents only when genuine reasoning is needed
- **Semantic layer / UI:** Solvable problem; chatbot-style interface for demand planner to query on demand; audit trail linking planner decisions back to the insights presented at time of decision
- **Model concerns (gray area):** Fine-tuning predictive models, preventing overfitting/underfitting, monitoring model drift — acknowledged as needing more exploration; 80% accuracy good enough for first demo

---

## 5. Planner Persona & Planning Context

- Nike's lead time: **18 months** from concept to store launch (Parul)
- Planners work by **product × region × DC × store**
- Planning horizons: currently Spring 2027 being planned now
- **Why 18-month lead time matters less for mid-market targets:** Smaller retailers don't manufacture in Asia with 10-month lead times — their cycles are shorter, making consumer signals more immediately actionable
- Demand planning (seasonal forecasting) = 24-hour data lag is not critical; but for **replenishment and inventory planning**, 24-hour lag IS a problem
- Different planning layers need different data freshness: demand forecasting (seasonal) vs. inventory/replenishment (near real-time)

---

## 6. Planning Value Stream — 5 Swim Lanes

The consulting positioning is **"planning experts"** with coverage across:
1. Demand Forecasting ← **anchor use case / show & tell**
2. Inventory Planning
3. Supply Planning
4. Costing
5. Material Planning

POV covers all five; working demo focuses on demand forecasting first.

---

## 7. BRD / Document Questions (Basu)

- Basu added ~10 qualifier questions to the BRD document (annotated; not blockers)
- Key question raised: **"What is the % accuracy impact of missing consumer data?"** — need to quantify the size of the prize
- Parul to answer BRD questions by end of Friday / Saturday morning (unavailable Sat–Sun)
- Most questions are business questions, not technical

---

## 8. Company Name — "SenseAct"

- Name origin: Sense → Detect → Act (DNA of an AI agent), condensed to SenseAct
- Considered "OmniSense" but rejected (too common; OmniScience already exists as a cloud observability company)
- **SenseAct** — unique, domain available (except a Mexican company), Parul's husband voted for it
- Google Drive folder to be named **"SenseAct"**

---

## 9. Show & Tell Demo Design (Refined)

- Run a simulation with **all consumer/marketing signals unchecked** → show baseline planning accuracy
- Switch to second tab, **turn on consumer insight channel** → show improved forecast
- Demonstrates the B-test concept without needing a fully productionized system
- Must use Parul's institutional knowledge to make data models realistic and relevant to a retail client (not generic synthetic data)
- Target: get **Keen Footwear** (Portland-based, ~$500M), Decker, or similar mid-market footwear brand into first meeting

---

## 10. Availability & Timeline Constraints

| Person | Constraint | Impact |
|--------|-----------|--------|
| Basu | Weekdays consumed by Philippines team takeover at day job | Can only work weekends (1–2 hrs) |
| Anil | Traveling to India June 8, cataract surgery, ~2 weeks unavailable | Must accelerate before June 8 |
| Parul | Not available Saturday–Sunday this week | Answering BRD questions today/tomorrow/Sat AM |

**Target:** End of June — first prototype ready, outreach campaign launched (email + LinkedIn)

---

## 11. Action Items

| Owner | Action | Due |
|-------|--------|-----|
| Parul | Integrated workflow diagram (consumer + planning loop) with data dictionary in Miro | Wednesday |
| Parul | Answer ~10 BRD qualifier questions Basu added to the document | By Sat AM |
| Parul | Start working on data hub schemas for consumer, planning, product, sales orders | Ongoing |
| Basu | Technology architecture diagram in Miro (MCP, skills, agents, LLM layer) | Sunday |
| Basu | Create Miro team/board, add all three Gmail accounts, share board link | This weekend |
| Anil | Create new "SenseAct" Google Drive folder (restricted to 3 people), migrate documents | Today |
| All | Mid-next-week sync once Basu's Miro + Parul's workflow are ready | Next week |

---

## 12. Tools & Collaboration

- **Miro** — single source of truth for visual artifacts (diagrams, architecture, process flows); can export docs
- **Google Drive (SenseAct folder)** — shared documents, BRD, data dictionaries
- **WhatsApp** — async updates and progress notifications between meetings
- **Nextcloud** — flagged by Basu as a potential future tool for startups (open source, infinite canvas, chat, mobile); evaluate later when more formalized
