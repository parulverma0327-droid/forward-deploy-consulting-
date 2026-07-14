#!/usr/bin/env python3
"""Local CLI — run ForecastSignalBQAgent."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_AGENTS_DIR = Path(__file__).resolve().parent.parent
if str(_AGENTS_DIR) not in sys.path:
    sys.path.insert(0, str(_AGENTS_DIR))

from forecast_signal.pipeline import run_forecast_signal  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Run ForecastSignalBQAgent")
    parser.add_argument(
        "--demo-perturb",
        metavar="PRODUCT_CD",
        default=None,
        help="Lower snapshot intent for product_cd to simulate spike (demo)",
    )
    args = parser.parse_args()

    try:
        if args.demo_perturb:
            from forecast_signal.bq_io import get_client
            from forecast_signal.demo import perturb_snapshot_for_demo

            n = perturb_snapshot_for_demo(get_client(), args.demo_perturb)
            print(json.dumps({"demo_perturb_rows": n, "product_cd": args.demo_perturb}, indent=2))

        result = run_forecast_signal()
    except Exception as exc:
        print(
            json.dumps(
                {
                    "error": str(exc),
                    "hint": (
                        "Run glossary/bq_orchestration_tables.sql then "
                        "gcloud auth application-default login"
                    ),
                },
                indent=2,
            )
        )
        return 1
    print(json.dumps(result.model_dump(mode="json"), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
