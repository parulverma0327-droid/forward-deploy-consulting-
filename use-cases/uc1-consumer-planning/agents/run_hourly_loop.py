#!/usr/bin/env python3
"""Run UC1 BQ agent → Orchestrator only (no DS/RC/IP)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_AGENTS_DIR = Path(__file__).resolve().parent
if str(_AGENTS_DIR) not in sys.path:
    sys.path.insert(0, str(_AGENTS_DIR))

from forecast_signal.pipeline import run_forecast_signal  # noqa: E402
from orchestrator.pipeline import run_orchestrator  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description="ForecastSignalBQAgent → OrchestratorAgent"
    )
    parser.add_argument(
        "--skip-bq",
        action="store_true",
        help="Skip BQ agent (use existing signal_delta)",
    )
    args = parser.parse_args()

    out: dict = {"steps": []}

    try:
        if not args.skip_bq:
            out["forecast_signal"] = run_forecast_signal().model_dump(mode="json")
            out["steps"].append("ForecastSignalBQAgent")

        out["orchestrator"] = run_orchestrator().model_dump(mode="json")
        out["steps"].append("OrchestratorAgent")

    except Exception as exc:
        out["error"] = str(exc)
        out["hint"] = (
            "Run glossary/bq_orchestration_tables.sql in BigQuery, then "
            "gcloud auth application-default login"
        )
        print(json.dumps(out, indent=2))
        return 1

    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
