# Running AgentSociety v1 (legacy)

A tested, one-command way to install and run **AgentSociety v1** (`packages/agentsociety`)
on Linux x86_64. This does not use AgentSociety 2.

```bash
cd run-v1
./setup.sh                 # venvs, simulator binary, embedding model, map
./run.sh                   # smoke test with a local mock LLM (no API key needed)
cp config_llm.example.yaml my_config.yaml   # add your LLM provider + key
./run.sh my_config.yaml    # real run
```

Requires [`uv`](https://docs.astral.sh/uv/) (it fetches Python 3.12 if needed).
Results go to `agentsociety_data/sqlite.db` (agent profiles, status per step, dialogs, metrics).

## What `setup.sh` does

| Step | Why |
|---|---|
| Python **3.12** venv `.venv-v1` with `agentsociety` + `agentsociety-community` (editable) | v1 pins `numpy<2`, which has no Python 3.13 wheels. `agentsociety run` imports `agentsociety_community`. |
| `qdrant-client==1.14.3` | Newer versions raise `ValueError: Empty update request` during agent memory init. |
| Separate `.venv-moss` with `mosstool` (numpy-1 stack forced via `overrides-mosstool.txt`) | mosstool is only used to build the map; it declares numpy 2 but breaks on it, and would also break v1's numpy pin. |
| Downloads `agentsociety-sim-oss` v0.2.2 into `agentsociety_data/` | The city simulator binary v1 drives over gRPC. |
| Downloads the `Qdrant/bm25` embedding model | Used by agent memory. Set `HF_ENDPOINT` to use a mirror. |
| Builds `grid_map.pb` via `scripts/build_grid_map.py` | The official city maps need a login at agentsociety.fiblab.net. This builds a 4x4 road grid with 36 buildings (args: `out.pb N spacing_m`). Use a real map by changing `map.file_path`. |

Network hosts needed: PyPI, `tsinghua-agentsociety.oss-cn-beijing.aliyuncs.com`, `huggingface.co` (+ its CDN), and your LLM provider.

## Mock LLM

`scripts/mock_llm.py` is an OpenAI-compatible server on `127.0.0.1:8765` that returns canned
answers. It only proves the pipeline works end to end; agent behaviour is meaningless and you
will see `Error parsing ... response` warnings. Use a real model for experiments.
