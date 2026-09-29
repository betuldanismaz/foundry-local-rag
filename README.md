# Local RAG Q&A Assistant

A fully offline document Q&A chatbot powered by [Microsoft Foundry Local](https://github.com/microsoft/foundry-local). Ask questions about your documents and get grounded answers — no cloud calls, no internet required at runtime.

Built as a teaching reference for a beginner CS summer program.

## How It Works

```
Your question
    │
    ▼
Embed query → search SQLite for similar chunks → top 3 matches
    │
    ▼
Assemble prompt: system instructions + retrieved chunks + your question
    │
    ▼
Local LLM (phi-3.5-mini via Foundry Local) generates an answer
    │
    ▼
Answer with source citations (or "I don't know" if not in the docs)
```

Every script talks to Foundry Local the same way: through its OpenAI-compatible local HTTP API (`/v1/chat/completions`, `/v1/embeddings`), using the standard `openai` Python package. There is no Microsoft Python SDK dependency — see [Why no `foundry-local-sdk`?](#why-no-foundry-local-sdk) below.

## Prerequisites

1. **Foundry Local CLI**:

   - Windows: `winget install Microsoft.FoundryLocal`
   - macOS: `brew tap microsoft/foundrylocal && brew install foundrylocal`

2. **Python 3.11+**

3. **Hardware**: 8 GB RAM minimum, 16 GB recommended. AVX2-capable CPU or a supported GPU/NPU.

4. **Verify the CLI works** before continuing:

   ```
   foundry model list
   ```

   If `foundry` isn't recognized on Windows right after installing, open a **new** terminal window — the installer updates your PATH, but already-open terminals won't see the change.

## Setup

```bash
# Clone or download this project, then:
cd foundrylocal

# Create a virtual environment
python -m venv .venv

# Activate it
# Windows:
.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate

# Install dependencies (just the `openai` package — see note above)
pip install -r requirements.txt
```

### Download and load the models

This project's scripts expect both models to already be downloaded and loaded into the running Foundry Local daemon — they don't do this automatically. Run once per machine (and again any time you restart and want them ready):

```bash
foundry model download phi-3.5-mini
foundry model download qwen3-embedding-0.6b

foundry model load phi-3.5-mini
foundry model load qwen3-embedding-0.6b
```

`foundry model load` starts the local daemon automatically if it isn't already running. The exact downloaded variant name depends on your hardware (e.g. `phi-3.5-mini-instruct-trtrtx-gpu` on an NVIDIA GPU) — the scripts look models up by alias, so this doesn't matter.

## Running the Project

### 1. Ingest documents

Place your text or markdown files in the `documents/` folder (sample docs are included), then run:

```bash
python ingest.py
```

This chunks each document, embeds the chunks using the local embedding model, and stores everything in `rag_data.db`. Safe to re-run — it rebuilds the database from scratch each time.

### 2. Start the chatbot

```bash
python main.py
```

Type your questions at the prompt. Type `quit` or `exit` to stop.

### 3. Run tests (optional)

```bash
python test_rag.py
```

Runs a set of predefined questions (some answerable, some not) and checks whether the answers are grounded or correctly refused.

## Project Structure

```
foundrylocal/
├── documents/         Sample documents the chatbot answers from
├── requirements.txt   Python dependencies (just `openai`)
├── config.py          Shared model names (CHAT_MODEL, EMBEDDING_MODEL)
├── foundry_client.py  Shared helper: finds the local daemon and builds an OpenAI client
├── smoke_test.py      Verify Foundry Local is working
├── ingest.py          Chunk + embed documents → SQLite
├── retrieval.py       Query embedding + cosine similarity search
├── chat.py            Prompt assembly + LLM answer generation
├── main.py            CLI entry point
├── test_rag.py        Automated test harness
└── rag_data.db        Generated database (not checked in)
```

## Adding Your Own Documents

1. Add `.txt` or `.md` files to the `documents/` folder
2. Re-run `python ingest.py`
3. Start the chatbot with `python main.py`

The chatbot will only answer based on what's in the documents. If you ask about something not covered, it will say so.

## Models Used

| Purpose    | Model                  | Notes                          |
|------------|------------------------|---------------------------------|
| Chat       | `phi-3.5-mini`         | Small, fast, good for teaching |
| Embeddings | `qwen3-embedding-0.6b` | Converts text to vectors       |

Both are set in `config.py`. **They must both be loaded at the same time** — retrieval needs the embedding model, generation needs the chat model, and a typical question uses both. If your machine is memory-constrained, see Troubleshooting below.

## Why no `foundry-local-sdk`?

The original plan for this project assumed the `foundry-local-sdk` pip package (specifically its `manager.endpoint` / `FoundryLocalManager(...)` pattern for auto-downloading and loading models). While building this, that package's management API (the HTTP routes it uses internally to download, load, and list models) turned out to no longer exist on current Foundry Local daemon versions — only version `0.5.1` and earlier of the pip package matches the currently-installable CLI/daemon, and even then only after also working around a CLI command rename (`service` → `server`) between versions.

Rather than pin to an old, unmaintained pip package, this project instead:
- Uses the `foundry` **CLI** directly for model management (`foundry model download`, `foundry model load`) — see `foundry_client.py` for how scripts discover the daemon's URL via `foundry server status`.
- Uses the plain `openai` package for inference, pointed at Foundry Local's `/v1` OpenAI-compatible endpoint — the same pattern the plan always intended, just without the extra SDK layer in between.

This is arguably simpler for students anyway: one well-known package (`openai`) instead of a Microsoft-specific one, and the CLI commands are visible and debuggable on their own (`foundry model list`, `foundry server status`).

## Troubleshooting

- **"Model not found" / `RuntimeError: Model '...' is not loaded`** — Run `foundry model load <alias>` (see [Download and load the models](#download-and-load-the-models)). Run `foundry model list` to see what's available and what's already cached.
- **`foundry` not recognized in the terminal** — Open a new terminal window after installing (PATH changes don't apply to already-open ones). On Windows, this project's CLI lives under `%LOCALAPPDATA%\Microsoft\WindowsApps`; if a shell still can't find it after reopening, confirm that folder is on your `PATH`.
- **Slow first run** — Normal. The model files are being downloaded (2.1 GB for phi-3.5-mini, ~500 MB for the embedding model). Subsequent runs are fast.
- **Out of memory** — Try a smaller chat model, e.g. `qwen2.5-0.5b` — update `CHAT_MODEL` in `config.py` and re-download/load it.
- **Wrong or irrelevant answers** — Re-run `python ingest.py` to make sure the database matches your current documents.
- **`[WinError 2] The system cannot find the file specified`** when testing `main.py` by piping input through Bash (e.g. `printf "..." | python main.py`) — this is a Git-Bash/MSYS pipe quirk, not a bug in the code. Use input redirection from a real file instead (`python main.py < input.txt`), or just run it interactively.
