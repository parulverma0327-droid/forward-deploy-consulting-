# UC1 BQ + Orchestrator — deployment

**Project:** `demandsensinglayer`  
**Dataset:** `dsl_dataset`  
**Team:** shared GCP project + IAM

---

## Architecture

| Component | Type | Writes | Runs |
|-----------|------|--------|------|
| **Forecast Signal — chat** | BQ Agent catalog | — (read-only NL→SQL) | On demand |
| **Forecast Signal — detection** | BQ scheduled query | `signal_delta`, `signal_delta_snapshot` | Hourly |
| **Orchestrator** | **Agent (Cloud Run / Python)** | `agent_run_history` | Hourly — triggered after signal_delta |
| **DS / RC** | **Agent (Cloud Run / Python)** | forecast + replacement tables | Triggered by Orchestrator `scope_json` |

Orchestrator is **not** a scheduled query. Same agent pattern as DS and RC.

---

## BigQuery (done)

### Tables
Run once: `glossary/bq_orchestration_tables.sql`

### Scheduled query — detection only
- **Name:** `UC1 – refresh signal_delta`
- **SQL:** `glossary/bq_refresh_signal_delta.sql`
- **Destination:** None
- **Schedule:** hourly (e.g. `:00`)

### BQ Agent catalog — Inquiry
- **Name:** `UC1 Forecast Signal Agent`
- **Sources:** `clickstream_agg`, `demand_forecast_base`, `signal_delta`

---

## Orchestrator agent (Cloud Run)

**Code:** `agents/orchestrator/`  
**Entrypoint:** `agents/orchestrator/main.py` → `POST /run`

### Deploy (once)

```bash
cd use-cases/uc1-consumer-planning/agents
gcloud run deploy uc1-orchestrator \
  --source . \
  --region us-central1 \
  --project demandsensinglayer \
  --service-account <SA with BigQuery Data Editor + Job User> \
  --no-allow-unauthenticated
```

### Schedule

Cloud Scheduler → HTTP POST to Orchestrator `/run`  
**Timing:** 5–10 min **after** `refresh signal_delta` (e.g. `:10`)

Orchestrator reads `signal_delta`, runs gates, writes `agent_run_history` + `scope_json`.

---

## Hourly loop

```
:00  BQ scheduled query  →  signal_delta
:10  Orchestrator agent  →  agent_run_history + scope_json
     (later) DS + RC agents  →  read scope_json, same run_id
```

---

## Verify

```sql
SELECT * FROM `demandsensinglayer.dsl_dataset.signal_delta`
ORDER BY detected_at DESC LIMIT 10;

SELECT run_id, run_status, scope_json FROM `demandsensinglayer.dsl_dataset.agent_run_history`
ORDER BY started_at DESC LIMIT 5;
```

---

## DS owner handoff

Latest completed run → `run_id` + `scope_json` from `agent_run_history`.

**Do not use** `glossary/bq_orchestrator_scheduled_query.sql` — SQL fallback only; production Orchestrator is the agent.
