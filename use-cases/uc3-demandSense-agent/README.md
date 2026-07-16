# Demand Sensing Agent

Flask service that joins demand forecast and clickstream data in BigQuery,
computes an intent-adjusted forecast, and writes results back to
`demandsensinglayer.dsl_dataset.demand_forecast_recommendation`.

## Local development

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export PORT=8080
python main.py
```

## Deploying to Cloud Run via GitHub

See the setup steps in the team deployment guide. In short:

1. Push this repo to GitHub.
2. In Cloud Run, create a service and connect it to this GitHub repo
   using "Continuously deploy from a repository".
3. Cloud Build will detect the `Dockerfile` and build/deploy automatically
   on every push to the configured branch.
