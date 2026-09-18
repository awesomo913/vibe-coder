# Vibe Coder

> Describe an app in plain English; three local AI agents plan it, write it, and review it for you.

Vibe Coder is a small Streamlit app that runs a multi-agent pipeline — a Planner, a Coder, and a Reviewer, each a separate call to a locally-running Ollama model — to turn a plain-language feature request into generated code, entirely on local hardware.

## Features
- **Streamlit UI** — a single text box for describing what to build, plus a "Build It" button.
- **Three-stage agent pipeline** (Planner → Coder → Reviewer), each a distinct Ollama model call, chained via `agents.py`.
- **Local-only inference** — runs against whatever models are already pulled in a local Ollama install; the sidebar lists which ones are available.
- **Run history** — past runs are saved as JSON under `outputs/` and browsable from the sidebar.
- **Packaged Windows build** (`VibeCoder.spec`, `start.bat`) for running without a manual `streamlit run`.

## Stack
Python, Streamlit, local Ollama (via its HTTP API).

## Getting started
**Requirements**
- Python 3.11+, a running local Ollama install with at least one model pulled (e.g. `ollama pull mistral`)

**Run**
```bash
pip install -r requirements.txt
streamlit run app.py
# or on Windows:
start.bat
```

## Status
**Unmaintained / archived.** Personal project, published as-is — fork it, adapt it, take it over. No support or guarantees.

## License
[MIT](LICENSE) — free to use, fork, and build on.
