# UC1 — Agent Architecture

Mermaid versions (paste into Miro, Notion, or GitHub).  
Source: `Retail _ Consumer - Planner Loop.pdf` §4 (agents) + §8.2 (deployment topology).

---

## 1. End-to-end deployment topology

```mermaid
flowchart TB
  subgraph SRC["External sources (SFTP → GCS landing)"]
    ECOM[E-com clickstream<br/>hourly]
    CRM[CRM / Loyalty<br/>hourly]
    CAMP[Campaign platform<br/>hourly]
    POS[POS transactions<br/>hourly]
    OMS[OMS orders<br/>hourly]
    ERP[ERP inventory<br/>daily]
    WMS[WMS stock<br/>daily]
    PIM[PIM catalog<br/>daily]
    MDM[MDM keys<br/>daily]
    PLAN[Planning baseline<br/>weekly]
  end

  subgraph GCS["GCS buckets"]
    LAND[landing/]
    PROC[processed/]
    ARCH[archive/]
  end

  subgraph BQ["BigQuery datasets"]
    BRZ[bronze.*]
    SLV[silver.*]
    GLD[gold.*]
    ML[ml.*]
    AUD[audit.*]
  end

  subgraph CR["Cloud Run — 7 agents"]
    ORCH[OrchestratorAgent]
    DS[DemandSensingAgent]
    RC[ReplacementCycleAgent]
    IP[InventoryPolicyAgent]
    TR[TraceabilityAgent]
    PUB[PublisherAgent]
    INQ[InquiryAgent]
  end

  subgraph MSG["Pub/Sub topics"]
    T1[agent-orchestration-hourly]
    T2[recommendations-emitted]
    T3[approval-events]
    T4[model-drift-alerts]
    T5[pipeline-failure-alerts]
  end

  subgraph API["APIs + UI"]
    INS[Insight API]
    INQAPI[Inquiry API]
    UI[Planning Workbench WebUI]
  end

  subgraph DOWN["Downstream (read-only in Phase 1)"]
    PSYS[Client planning system]
  end

  ECOM & CRM & CAMP & POS & OMS & ERP & WMS & PIM & MDM & PLAN --> LAND
  LAND --> BRZ
  BRZ --> SLV --> GLD
  GLD --> ML
  ML --> ORCH

  CRON[Cloud Scheduler<br/>hourly] --> T1 --> ORCH
  ORCH --> DS & RC
  DS & RC --> IP --> TR --> PUB
  PUB --> T2 --> INS --> UI
  INQ --> INQAPI --> UI

  UI -->|approve / reject / override| T3
  T3 --> AUD
  UI -->|write approved| GLD
  GLD --> PSYS

  ORCH -.->|fail| T5
  ML -.->|drift| T4
```

**Gold tables agents consume:** `intent_signal_hourly`, `member_sales_attributed`, `forecast_baseline`, `customer_segment`, `replacement_scores`.

**Gold tables planner writes:** `forecast_adjustments`, `approval_audit`.

---

## 2. Hourly agent orchestration (Sense → Reason → Act)

```mermaid
flowchart TB
  subgraph GATES["Orchestrator — Bucket 1: Gates (fail = skip run)"]
    G1[Gold freshness &lt; 2h]
    G2[Identity match &gt; 80%]
    G3[Schema validation 100%]
    G4[BQML model version current]
  end

  subgraph DELTA["Bucket 2: Signal delta"]
    SD[Read scopes where intent / loyalty / campaign moved]
  end

  subgraph DEDUP["Bucket 3: Dedup"]
    DD[Skip if pending rec for same SKU × region × week]
  end

  subgraph PAR["Specialists — parallel"]
    DS[DemandSensingAgent<br/>ClickstreamIntent · LoyaltySegment · CampaignResponse]
    RC[ReplacementCycleAgent<br/>repurchase cadence by segment × SKU]
  end

  subgraph SEQ["Sequential"]
    IP[InventoryPolicyAgent<br/>safety stock from demand + replacement]
    TR[TraceabilityAgent<br/>recommendation envelope + lineage]
    PUB[PublisherAgent<br/>RecommendationEmitted → Pub/Sub + Insight API]
  end

  SCH[Cloud Scheduler] --> ORCH[OrchestratorAgent]
  ORCH --> GATES --> DELTA --> DEDUP
  DEDUP --> DS & RC
  DS & RC --> IP --> TR --> PUB
  PUB --> UI[Planner Workbench<br/>Insight feed]
```

**Demo mode:** static Gold breaks freshness gates — use `DEMO_MODE=true` or UI toggle reading pre-staged Run 1 / Run 2 (see Agent Build Handover §7).

---

## 3. Planner interaction paths

```mermaid
flowchart LR
  subgraph PUSH["Insight API — push"]
    PUB[PublisherAgent] --> INS[Insight API store]
    INS --> FEED[Insight feed in WebUI]
    FEED --> HITL[Approve · Reject · Override]
  end

  subgraph PULL["Inquiry API — pull"]
    Q[Planner NL question] --> INQ[InquiryAgent]
    INQ --> MET[Structured metrics API]
    INQ --> NAR[Semantic explanation + trace refs]
    MET & NAR --> CARD[Optional recommendation card]
  end

  HITL --> AUD[gold.approval_audit]
  HITL -->|on approve| ADJ[gold.forecast_adjustments]
  HITL --> PS[Pub/Sub approval-events]
```

**Rule:** recommend-only in Phase 1 — nothing auto-applies to client planning systems.

---

## 4. Agent inventory (quick reference)

| Agent | Role | Trigger |
|-------|------|---------|
| OrchestratorAgent | Gates + signal delta + routing | Hourly (Scheduler → Pub/Sub) |
| DemandSensingAgent | Intent + loyalty + campaign → `units_intent_adjusted` | Routed by Orchestrator |
| ReplacementCycleAgent | Repurchase likelihood by segment × SKU | Parallel with Demand Sensing |
| InventoryPolicyAgent | Safety stock from demand + replacement | After specialists |
| TraceabilityAgent | Recommendation envelope + lineage | Before publish |
| PublisherAgent | `RecommendationEmitted` → Pub/Sub + Insight API | Last in hourly loop |
| InquiryAgent | On-demand planner Q&A | Planner request |

Phase 2 (out of scope): Promotion Optimization Agent, Store Execution Agent.

---

*Forward Deploy Consulting · UC1 · Jun 2026*
