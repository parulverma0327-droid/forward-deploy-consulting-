#!/usr/bin/env python3
"""Local CLI — run Demand Sensing pipeline and print recommendation envelope JSON."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Support: python run_local.py (from this directory)
_AGENTS_DIR = Path(__file__).resolve().parent.parent
if str(_AGENTS_DIR) not in sys.path:
    sys.path.insert(0, str(_AGENTS_DIR))

from demand_sensing.config import HERO_REGION, HERO_WEEKS  # noqa: E402
from demand_sensing.models import RunScope  # noqa: E402
from demand_sensing.pipeline import run_demand_sensing  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Run UC1 Demand Sensing agent locally")
    parser.add_argument("--region", default=HERO_REGION, help="Enterprise region (default: Pacific NW)")
    parser.add_argument(
        "--weeks",
        default=",".join(HERO_WEEKS),
        help="Comma-separated retail weeks (default: hero W42–W48)",
    )
    parser.add_argument("--style", default="%targhee%", help="Style name LIKE pattern")
    parser.add_argument("--product-cd", default=None, help="Explicit product_cd (skips style lookup)")
    parser.add_argument("--run-id", default=None, help="Optional run_id for traceability")
    args = parser.parse_args()

    weeks = tuple(w.strip() for w in args.weeks.split(",") if w.strip())

    scope = RunScope(
        product_cd=args.product_cd,
        style_name_pattern=args.style,
        region=args.region,
        weeks=weeks,
    )

    try:
        envelope = run_demand_sensing(scope=scope, run_id=args.run_id)
    except Exception as exc:
        print(
            json.dumps(
                {
                    "error": str(exc),
                    "hint": (
                        "gcloud auth application-default login && "
                        "gcloud config set project demandsensinglayer"
                    ),
                },
                indent=2,
            )
        )
        return 1

    print(json.dumps(envelope.model_dump(mode="json"), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
