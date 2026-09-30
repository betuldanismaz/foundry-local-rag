<div align="center">

# Local RAG Q&A Assistant

**A fully offline, document-grounded chatbot powered by [Microsoft Foundry Local](https://github.com/microsoft/foundry-local).**

Ask questions about your own documents and get cited answers — no cloud calls, no API keys, no internet required at runtime.

![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![Runtime](https://img.shields.io/badge/runtime-Foundry%20Local-0078D4)
![Storage](https://img.shields.io/badge/storage-SQLite-003B57)
![Offline](https://img.shields.io/badge/mode-100%25%20offline-success)

</div>

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Usage](#usage)
- [Project Structure](#project-structure)
- [Configuration](#configuration)
- [Adding Your Own Documents](#adding-your-own-documents)
- [Design Decisions](#design-decisions)
- [Troubleshooting](#troubleshooting)

## Overview

This project is a compact, readable reference implementation of **Retrieval-Augmented Generation (RAG)** that runs entirely on your machine. It was built as a teaching resource for a beginner CS summer program, so every stage of the pipeline lives in its own small, well-named module.

**Highlights**

- **Private by design** — documents, embeddings and model inference never leave your computer.
- **Grounded answers** — responses cite the source chunks, and the assistant says *"I don't know"* when the documents don't cover a question.
- **Minimal dependencies** — a single Python package (`openai`) and a SQLite file; no vector database to install.
- **Easy to follow** — one script per pipeline stage (ingest → retrieve → generate → interface).
- **Testable** — a built-in harness checks both answerable and unanswerable questions.

## Architecture

```
Your question
    │
    ▼
Embed query ──► search SQLite for similar chunks ──► top 3 matches
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

Every script talks to Foundry Local the same way: through its OpenAI-compatible HTTP API (`/v1/chat/completions`, `/v1/embeddings`) using the standard `openai` Python package. See [Design Decisions](#why-no-foundry-local-sdk) for why there is no Microsoft-specific SDK.

| Stage      | Module             | Responsibility                                      |
|------------|--------------------|-----------------------------------------------------|
| Ingest     | `ingest.py`        | Chunk documents, embed chunks, store in SQLite      |
| Retrieve   | `retrieval.py`     | Embed the query, rank chunks by cosine similarity   |
| Generate   | `chat.py`          | Build the grounded prompt and call the chat model   |
| Interface  | `main.py`          | Interactive command-line loop                       |

## Prerequisites

| Requirement        | Details                                                                  |
|--------------------|--------------------------------------------------------------------------|
| Foundry Local CLI  | Windows: `winget install Microsoft.FoundryLocal`                         |
|                    | macOS: `brew tap microsoft/foundrylocal && brew install foundrylocal`   |
| Python             | 3.11 or newer                                                            |
| Hardware           | 8 GB RAM minimum (16 GB recommended); AVX2-capable CPU or supported GPU/NPU |

Verify the CLI works before continuing:

```bash
foundry model list
```

> **Windows tip:** if `foundry` isn't recognized right after installing, open a **new** terminal window. The installer updates `PATH`, but terminals that were already open won't see the change.

## Installation

```bash
# 1. Get the project
cd foundrylocal

# 2. Create a virtual environment
python -m venv .venv

# 3. Activate it
#    Windows:
.venv\Scripts\activate
#    macOS / Linux:
source .venv/bin/activate

# 4. Install dependencies (just the `openai` package)
pip install -r requirements.txt
```

### Download and load the models

The scripts expect both models to be downloaded **and loaded** into the running Foundry Local daemon; they do not do this automatically. Run once per machine, and again after a restart:

```bash
foundry model download phi-3.5-mini
foundry model download qwen3-embedding-0.6b

foundry model load phi-3.5-mini
foundry model load qwen3-embedding-0.6b
```

`foundry model load` starts the local daemon if it isn't already running. The downloaded variant depends on your hardware (e.g. `phi-3.5-mini-instruct-trtrtx-gpu` on an NVIDIA GPU); the scripts resolve models by alias, so this doesn't matter.

Optionally confirm everything is wired up:

```bash
python smoke_test.py
```

## Usage

### 1. Ingest documents

Put `.txt` or `.md` files in `documents/` (sample documents are included), then run:

```bash
python ingest.py
```

This chunks each document, embeds the chunks with the local embedding model, and stores everything in `rag_data.db`. It is safe to re-run — the database is rebuilt from scratch each time.

### 2. Start the chatbot

```bash
python main.py
```

Type your question at the prompt. Type `quit` or `exit` to leave.

### 3. Run the tests (optional)

```bash
python test_rag.py
```

Runs a set of predefined questions — some answerable, some deliberately not — and checks that answers are grounded or correctly refused.

## Project Structure

```
foundrylocal/
├── documents/          Sample documents the chatbot answers from
├── plans/              Step-by-step build plans used for the course
├── prep/               Presentation materials (plan, script, technical doc)
├── config.py           Shared model names (CHAT_MODEL, EMBEDDING_MODEL)
├── foundry_client.py   Discovers the local daemon and builds an OpenAI client
├── smoke_test.py       Verifies Foundry Local is working
├── ingest.py           Chunk + embed documents → SQLite
├── retrieval.py        Query embedding + cosine-similarity search
├── chat.py             Prompt assembly + LLM answer generation
├── main.py             CLI entry point
├── test_rag.py         Automated test harness
├── requirements.txt    Python dependencies (just `openai`)
└── rag_data.db         Generated database (not checked in)
```

## Configuration

Models are defined in `config.py`. **Both must be loaded at the same time** — retrieval needs the embedding model and generation needs the chat model, and a typical question uses both.

| Purpose    | Model                  | Notes                              |
|------------|------------------------|------------------------------------|
| Chat       | `phi-3.5-mini`         | Small and fast; good for teaching  |
| Embeddings | `qwen3-embedding-0.6b` | Converts text to vectors           |

On a memory-constrained machine, switch `CHAT_MODEL` to a smaller model such as `qwen2.5-0.5b`, then download and load it.

## Adding Your Own Documents

1. Add `.txt` or `.md` files to `documents/`.
2. Re-run `python ingest.py`.
3. Start the chatbot with `python main.py`.

The assistant answers only from what is in your documents. If you ask about something not covered, it will say so.

## Design Decisions

### Why no `foundry-local-sdk`?

The original plan assumed the `foundry-local-sdk` pip package (its `FoundryLocalManager` pattern for auto-downloading and loading models). During development, the HTTP management routes that package relies on no longer existed in current Foundry Local daemon versions. Only pip package `0.5.1` and earlier matched the installable CLI/daemon, and even then only after working around a CLI rename (`service` → `server`).

Instead of pinning to an old, unmaintained package, this project:

- uses the **`foundry` CLI** for model management (`foundry model download`, `foundry model load`); `foundry_client.py` discovers the daemon URL via `foundry server status`;
- uses the plain **`openai` package** for inference, pointed at Foundry Local's OpenAI-compatible `/v1` endpoint.

This is also simpler for students: one well-known package instead of a vendor-specific one, and every CLI command (`foundry model list`, `foundry server status`) can be run and debugged on its own.

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| `Model not found` / `RuntimeError: Model '...' is not loaded` | Run `foundry model load <alias>` (see [Download and load the models](#download-and-load-the-models)). `foundry model list` shows what is available and cached. |
| `foundry` not recognized | Open a new terminal after installing. On Windows the CLI lives under `%LOCALAPPDATA%\Microsoft\WindowsApps`; make sure that folder is on your `PATH`. |
| Slow first run | Normal — models are downloading (≈2.1 GB for phi-3.5-mini, ≈500 MB for the embedding model). Later runs are fast. |
| Out of memory | Use a smaller chat model (e.g. `qwen2.5-0.5b`): update `CHAT_MODEL` in `config.py`, then download and load it. |
| Wrong or irrelevant answers | Re-run `python ingest.py` so the database matches your current documents. |
| `[WinError 2] The system cannot find the file specified` when piping input to `main.py` in Git Bash (e.g. `printf "..." \| python main.py`) | A Git-Bash/MSYS pipe quirk, not a bug. Use redirection from a real file (`python main.py < input.txt`) or run interactively. |
