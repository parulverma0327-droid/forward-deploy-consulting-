# Meeting Summary — June 26, 2026

**Meeting Title:** Use case 1 synch up  
**Participants:** Parul Verma, Prasad, Basu  
**Purpose:** Onboard Prasad (data engineer) to agent build; review canonical data model progress; major architecture update on BQ agents

---

## 1. Context & Updates

- **Prasad onboarded** — ex-Nike data engineer (Parul's former team); strong on data pipelines, newer to AI/agent work.
- **Anil / Anuj** — Anuj replied; Anil returning today; Parul and Anil plan to meet Anuj.
- **Current focus** — data model largely done; this week shifting to **OrchestratorAgent** and **DemandSensingAgent**.

---

## 2. Data Model Status (Parul)

**Foundational Gold tables built (~15–16 tables):**

| Domain | Tables |
|--------|--------|
| Product | Product master + related |
| Orders | Sales / transaction data |
| Member / Consumer | Member profile + member KPIs |
| Clickstream | Events + clickstream KPIs |
| Reference | Retail calendar, geo, region, season |
| Forecast | Base demand forecast (no consumer signals) |
| Enriched forecast | Two tables with consumer/clickstream/member-enriched units + revenue impact |

**Still needed:** 3–4 simple tables for web UI (sessions, planner state).

**Key decision — demo starts at Gold:**
- Synthetic data populated directly into **canonical Gold format** (not Bronze/Silver for show & tell).
- Parul's Gold tables **are** the prescribed canonical format for downstream (agents, PDH, UI).
- Bronze/Silver remain in the **blueprint** for client engagements where data massage is needed — but demo should showcase **agentic value**, not ETL skills.

**Parul deliverables:**
- Data strategy document (definitions, how to map client data → canonical format)
- Update Miro board entity definitions (replace placeholder entities with Parul's naming; version-controlled)

---

## 3. Architecture Change — BigQuery Agents (Basu)

**Major update from May 28 design:** Basu learned BigQuery now supports **out-of-the-box BQ agents** built directly on data sources.

### Old design (crossed out)
```
Gold data → separate forecast/signal BQML models → Python/LangGraph/ADK agents on top
```

### New design
```
Gold data → Forecast & Signal BQ Agent (NL → SQL → results)
         → OrchestratorAgent (subscribes to BQ agent signals)
         → marries Inventory Policy + Replacement Cycle + Demand Sensing
         → Traceability → Publisher → Insight API + Pub/Sub
```

**What changed:**

| Component | Before | After |
|-----------|--------|-------|
| Forecast & signal model | Separate BQML layer | **Forecast & Signal BQ Agent** on Gold tables |
| Agent build | Python + ADK/LangGraph required for core logic | **BQ agent** handles NL queries on data; less custom model code |
| InquiryAgent | Routed to medallion layer | Routes to **BQ agent on Gold** — chatbot queries Gold directly |
| Orchestrator | Gate checks + route to 3 specialist agents | Subscribes to signal from BQ agent; decides process/skip; marries all three signal types for traceability |

**Orchestrator role (clarified):**
1. Subscribed to signals from Forecast & Signal BQ Agent
2. Decides whether to process or skip (data quality / signal change — Parul's original understanding still valid)
3. If processing: runs through Inventory Policy, Replacement Cycle, Demand Sensing
4. Marries signals → traceability reasoning → publishes to Insight API + Pub/Sub

**On-demand planner queries:** Planner workbench chatbot → BQ agent on Gold (NL conversation, auto-generates SQL).

---

## 4. Medallion Architecture (Client vs Demo)

**Ideal state (client deployment):**

| Layer | Purpose |
|-------|---------|
| Raw / GCS landing | Client data arrives (SFTP, events, XML, flat files, Snowflake export, etc.) |
| Bronze | Minimum validation — data is workable (Tableau Prep equivalent) |
| Silver | Normalization + canonicalization (address dedup, product dictionary resolution) |
| Gold | Planning-ready marts — agents and UI consume here |

**Client flexibility ("meet them where they are"):**
- Have data in canonical format already → plug in at Gold, start day one
- Have messy/multi-format sources → land in GCS/SFTP; SenseAct builds Bronze/Silver pipeline as **software services**
- Have Snowflake instead of BQ → small conversion layer to canonical format
- Nike example: events, XML, flat files, materialized views from different systems

**Demo approach:** Skip Bronze/Silver population — synthetic Gold only. If client asks "how do we get our data in?" → Prasad builds adapter pipeline (post-sale services).

---

## 5. Tech Stack (Confirmed)

| Layer | Choice |
|-------|--------|
| Cloud | **Google Cloud** (Anil direction — single cloud target) |
| Data | BigQuery, GCS landing, Eventarc/Cloud Run pipelines |
| Agents | **Google ADK** (Basu preference — open source, Vertex-ready, skills/sub-agents/workflows) |
| Alternative | LangGraph / LangChain + Python — acceptable |
| BQ agents | New — build agents directly on Gold data sources |
| LLM | Any model via config (Gemini, Claude, OpenAI) — brain chosen at runtime |

ADK = plumbing + business logic layer; model is configurable.

---

## 6. Planner UI & APIs (Reconfirmed)

- **Insight API** — push recommendations to planner workbench UI (approve/reject workflow)
- **Inquiry API / chatbot** — planner asks follow-up questions → now routes to **BQ agent on Gold**
- Insights shown proactively on UI; chatbot for deeper inquiry

---

## 7. Prasad — Starting Point & Questions

**Consume from Gold (for now):**
1. Base demand forecast table (Run 1 — no consumer signals)
2. Two enriched forecast tables (Run 2 — with clickstream/member signals)
3. Join hub final tables (product, member, clickstream, orders) — **not** staging/Bronze/Silver

**Prasad action items:**
- Review Miro board workflow layer + notes on each section
- Research **BigQuery agents** (new to him)
- Add questions as Miro comments (@Basu) or WhatsApp group
- Revisit architecture given BQ agent change
- Explore ADK / GCP integration path

**Example data request:** Prasad asked for 2–3 product end-to-end examples (Bronze → Silver → Gold). **Answer for demo:** Gold data already exists in consumable format; ideal-state Bronze/Silver examples are future/assessment work, not blocking agent build.

**Data plugins:** Basu mentioned adapter/conversion as separate service — not fully defined; parked for now.

---

## 8. Client Artifacts

**Pre-engagement (show & tell):**
- Architecture diagram (Miro)
- Show & tell story + web UI
- PRD (UC1)
- Business glossary
- Data strategy doc (Parul — in progress)

**Post-engagement (after signed):**
- Deployment architecture (GCP services list)
- Detailed agent documentation (signals, sense → reason → act → unlearn) — treated as "secret sauce"

---

## 9. Communication & Cadence

- **WhatsApp group** — Parul, Basu, Prasad (async questions; no need for Parul to relay)
- **Miro comments** — architecture design record; tag @Basu
- **Sunday sync** — available for 30-min follow-up if needed (Saturday not reliable for Basu)

---

## 10. Action Items

| Owner | Action |
|-------|--------|
| Parul | Create data strategy document (canonical definitions + client mapping guide) |
| Parul | Update Miro board with refined entity/table definitions |
| Parul | Create WhatsApp group (Parul, Basu, Prasad) |
| Parul | Meet Anil → Anuj when Anil returns |
| Prasad | Review Miro board + BQ agents documentation |
| Prasad | Build agent layer starting from Gold forecast tables |
| Prasad | Call Parul next day with follow-up questions |
| Basu | Answer Miro comments / WhatsApp async |
| Basu | Updated Miro diagram (BQ agent layer, crossed-out old model path) |

---

## 11. Key Decisions

1. **Demo = Gold-first** — synthetic canonical data; no Bronze/Silver for show & tell
2. **Parul's Gold schema = prescribed format** — downstream contract for agents and UI
3. **BQ agents replace separate model + custom agent stack** for core forecast/signal/inquiry path
4. **Orchestrator still gates and marries** specialist agent outputs before publish
5. **Google ADK + GCP** remain primary stack; BQ agents are additive simplification
6. **Client adapter pipelines** = Prasad's domain post-engagement; not demo scope
