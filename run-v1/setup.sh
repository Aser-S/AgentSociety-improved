#!/usr/bin/env bash
# One-time setup for AgentSociety v1 (legacy package) on Linux x86_64.
# Creates two venvs (v1 needs numpy<2 and Python <=3.12), downloads the city
# simulator binary and the bm25 embedding model, and builds a small grid map.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
cd "$HERE"
INDEX="${UV_INDEX:-https://pypi.org/simple}"
command -v uv >/dev/null || { echo "Install uv first: https://docs.astral.sh/uv/"; exit 1; }

# 1. AgentSociety v1 runtime
[ -d .venv-v1 ] || uv venv -p 3.12 .venv-v1
VIRTUAL_ENV=.venv-v1 uv pip install --index-url "$INDEX" -r requirements-v1.txt \
  -e "$ROOT/packages/agentsociety"
VIRTUAL_ENV=.venv-v1 uv pip install --index-url "$INDEX" --no-deps -e "$ROOT/packages/agentsociety-community"

# 2. mosstool (map builder) in its own venv: it otherwise pulls numpy 2
[ -d .venv-moss ] || uv venv -p 3.12 .venv-moss
VIRTUAL_ENV=.venv-moss uv pip install --index-url "$INDEX" -r requirements-mosstool.txt --override overrides-mosstool.txt

# 3. Simulator binary + embedding model into ./agentsociety_data
mkdir -p agentsociety_data
if [ ! -x agentsociety_data/agentsociety-sim-oss ]; then
  curl -fL -o agentsociety_data/agentsociety-sim-oss \
    https://tsinghua-agentsociety.oss-cn-beijing.aliyuncs.com/agentsociety-sim-oss/v0.2.2/agentsociety-sim-oss-linux-amd64
  chmod +x agentsociety_data/agentsociety-sim-oss
fi
HF_ENDPOINT="${HF_ENDPOINT:-https://huggingface.co}" .venv-v1/bin/python -c "
from fastembed import SparseTextEmbedding
SparseTextEmbedding('Qdrant/bm25', cache_dir='agentsociety_data/huggingface_cache')"

# 4. Synthetic map (official maps need a login at agentsociety.fiblab.net)
[ -f grid_map.pb ] || .venv-moss/bin/python scripts/build_grid_map.py grid_map.pb 4 400
echo "Setup done. Next: ./run.sh            (mock LLM smoke test)"
echo "            or: ./run.sh my_config.yaml (your own LLM config)"
