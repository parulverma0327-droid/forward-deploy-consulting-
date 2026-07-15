#!/usr/bin/env python3
"""Local runner for InventoryPolicyAgent."""

from __future__ import annotations

import json
import sys
from pathlib import Path

_AGENTS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_AGENTS_DIR))

from inventory_policy.pipeline import run_inventory_policy  # noqa: E402


def main() -> None:
    run_id = sys.argv[1] if len(sys.argv) > 1 else None
    result = run_inventory_policy(run_id=run_id)
    print(json.dumps(result.model_dump(mode="json"), indent=2))


if __name__ == "__main__":
    main()
