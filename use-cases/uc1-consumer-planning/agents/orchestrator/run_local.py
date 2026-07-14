#!/usr/bin/env python3
"""Local CLI — run OrchestratorAgent."""

from __future__ import annotations

import json
import sys
from pathlib import Path

_AGENTS_DIR = Path(__file__).resolve().parent.parent
if str(_AGENTS_DIR) not in sys.path:
    sys.path.insert(0, str(_AGENTS_DIR))

from orchestrator.pipeline import run_orchestrator  # noqa: E402


def main() -> int:
    try:
        result = run_orchestrator()
    except Exception as exc:
        print(
            json.dumps(
                {
                    "error": str(exc),
                    "hint": (
                        "Run forecast_signal first, then orchestrator. "
                        "Ensure bq_orchestration_tables.sql is applied."
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
