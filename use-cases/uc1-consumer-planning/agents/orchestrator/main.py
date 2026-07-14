"""Cloud Run HTTP entrypoint for OrchestratorAgent."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from flask import Flask, jsonify

_AGENTS_DIR = Path(__file__).resolve().parent.parent
if str(_AGENTS_DIR) not in sys.path:
    sys.path.insert(0, str(_AGENTS_DIR))

from orchestrator.pipeline import run_orchestrator  # noqa: E402

app = Flask(__name__)


@app.route("/run", methods=["POST", "GET"])
def run():
    try:
        result = run_orchestrator()
        return jsonify(result.model_dump(mode="json")), 200
    except Exception as exc:
        return jsonify({"error": str(exc), "agent": "OrchestratorAgent"}), 500


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "agent": "OrchestratorAgent"}), 200


if __name__ == "__main__":
    import os

    port = int(os.environ.get("PORT", "8080"))
    app.run(host="0.0.0.0", port=port)
