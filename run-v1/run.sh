#!/usr/bin/env bash
# Run AgentSociety v1. With no argument, starts the local mock LLM and runs
# config_mock.yaml as a smoke test. Pass a config path to use a real LLM.
set -euo pipefail
cd "$(dirname "$0")"
export HF_ENDPOINT="${HF_ENDPOINT:-https://huggingface.co}"
CONFIG="${1:-config_mock.yaml}"
if [ "$CONFIG" = "config_mock.yaml" ]; then
  .venv-v1/bin/python scripts/mock_llm.py > mock_server.out 2>&1 &
  MOCK=$!; trap 'kill $MOCK 2>/dev/null || true' EXIT
  for _ in $(seq 30); do curl -s -o /dev/null http://127.0.0.1:8765/docs && break; sleep 0.5; done
fi
.venv-v1/bin/agentsociety check -c "$CONFIG"
.venv-v1/bin/agentsociety run -c "$CONFIG"
