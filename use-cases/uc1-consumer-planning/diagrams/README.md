# UC1 — Diagrams & reference PDFs

| File | Type | What it shows |
|------|------|---------------|
| **Data FLow.pdf** | Miro export (7 pp) | As-Is consumer loop, As-Is planning loop, To-Be connected loop with SenseAct data + agentic layer |
| **Retail _ Consumer - Planner Loop.pdf** | Basu spec (41 pp) | Full UC1 agent architecture: 7 agents, entity contracts, SFTP sources, deployment topology, KPIs, delivery plan |
| **agent_architecture.md** | Mermaid | Generated architecture: deployment topology, hourly orchestration, planner push/pull paths |
| `../../../diagrams/consumer_loop_asis_dataflow.png` | PNG | As-Is consumer loop (same as Data FLow.pdf swimlane 1) |
| `../../../diagrams/consumer_loop_tobe_dataflow.png` | PNG | To-Be connected loop (same as Data FLow.pdf swimlane 3) |
| `../../../diagrams/connected_loop_tobe_dataflow.md` | Mermaid | Hub-layer data flow (Product, OMS, Clickstream, Member → PDH → agents) |
| `../../../diagrams/senseact_delivery_model.png` | PNG | Canonical models + adapters + MCP + pre-built agents |

**When to use which:**
- **Business / Show & Tell story** → Data FLow.pdf or consumer_loop PNGs
- **Engineering build** → Planner Loop PDF + `agent_architecture.md`
- **Hub + translate layer** → `connected_loop_tobe_dataflow.md`
