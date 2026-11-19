# Run AgentSociety v1 on your machine (2 agents, free, local)

Works on **Linux x86_64** and **macOS on Apple Silicon (M1–M4)**, because the city simulator
binary only exists for those. On Windows, use WSL (Ubuntu) and run everything inside it.

## 1. One-time install

```bash
# prerequisites: git, curl, uv (https://docs.astral.sh/uv/), Ollama (https://ollama.com)
git clone -b claude/run-agentsociety-v1 https://github.com/Aser-S/agentsociety-improved
cd agentsociety-improved/run-v1
./setup.sh                 # ~5 min: Python 3.12 envs, simulator, memory model, map
ollama pull qwen2.5:3b     # ~2 GB local model (free)
```

## 2. Press run

```bash
./run.sh config_ollama.yaml    # 2 agents, 08:00 -> 09:00 simulated, uses your Ollama
```

No Ollama yet? `./run.sh` runs the same pipeline against a fake model to check the install.

Results are saved to `agentsociety_data/sqlite.db`. To look at them:

```bash
.venv-v1/bin/python - <<'PY'
import sqlite3; c = sqlite3.connect("agentsociety_data/sqlite.db")
for (t,) in c.execute("select name from sqlite_master where type='table'"):
    print(t, c.execute(f'select count(*) from "{t}"').fetchone()[0])
PY
```

To change things, edit `config_ollama.yaml`: `number` (agents), `steps`, `ticks_per_step`
(seconds per step) and `model` (any model you've pulled in Ollama).

## 3. How it works

```
config_ollama.yaml ──► agentsociety run (CLI)
                         │
                         ├─ starts agentsociety-sim-oss  ← city simulator (roads, buildings,
                         │     (gRPC, separate process)     people moving, clock)
                         ├─ creates agents (Ray)          ← 2 citizens + bank/firm/government/NBS
                         │     each step, every citizen:
                         │       observe → update needs → plan → act (move/talk/work)
                         │       every decision = a prompt to the LLM (your Ollama)
                         ├─ memory: per-agent vector store (Qdrant + bm25 model)
                         └─ writes everything to SQLite (profiles, status per step, dialogs)
```

Where to read the original code (`packages/agentsociety/agentsociety/`):

| What | File |
|---|---|
| CLI entry point (`agentsociety run`) | `cli/cli.py` |
| Main loop: start sim, build agents, run workflow | `simulation/simulationengine.py` |
| The citizen agent and its "brain" blocks | `cityagent/societyagent.py`, `cityagent/blocks/` (needs, plan, mobility, social, economy) |
| Agent base class | `agent/agent.py` |
| Memory | `memory/memory.py`, `vectorstore/vectorstore.py` |
| Talking to the city simulator | `environment/environment.py` |
| LLM client (OpenAI-compatible) | `llm/llm.py` |
| All config fields | `configs/` |

## What the scripts in this folder do

- `setup.sh`: creates `.venv-v1` (Python 3.12 + `numpy<2`, which v1 requires), pins
  `qdrant-client==1.14.3` (newer versions crash on start), downloads the simulator binary and the
  memory model, and builds `grid_map.pb` (a small 4x4 street grid with 36 buildings) with
  `scripts/build_grid_map.py` in a separate `.venv-moss`. The official city maps need a login at
  agentsociety.fiblab.net; to use one, download it and set `map.file_path`.
- `run.sh [config]`: runs `agentsociety check` and then `agentsociety run`. With no argument it
  also starts `scripts/mock_llm.py` (fake answers, for testing only).
