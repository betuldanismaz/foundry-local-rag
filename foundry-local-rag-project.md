# Project: Local RAG Q&A Assistant with Microsoft Foundry Local

## Context

This is a teaching project for a one-month (4–6 week) beginner CS summer program.
The end deliverable is a **fully offline document Q&A chatbot**: it retrieves
relevant chunks from a small local document collection and feeds them to a
local LLM (via Microsoft Foundry Local) to generate grounded answers. Zero
cloud calls, zero internet dependency at inference time.

You (the coding agent) are being used to help build a **reference
implementation** of this project — the working app that the instructor will
demo, adapt into exercises, and that students will follow along with or
extend. Prioritize clarity and correctness over cleverness: every piece of
this needs to be explainable to a beginner.

## Reference material (use these, not memory)

The original plan cited an older Microsoft Tech Community blog post. That
post is somewhat stale on API shape. Prefer these current, actively
maintained sources when implementing:

- **microsoft-foundry/Foundry-Local-Lab** (GitHub) — official workshop repo.
  Part 1–4 map directly onto this project:
  - `labs/part1-getting-started.md` — CLI install, model listing
  - `labs/part2-foundry-local-sdk.md` — full SDK reference (Python/JS/C#)
  - `labs/part3-sdk-and-apis.md` — streaming chat completions, code in
    `python/foundry-local.py`
  - `labs/part4-rag-fundamentals.md` — in-memory knowledge base,
    keyword/embedding retrieval, grounded system prompts, code in
    `python/foundry-local-rag.py` ← **closest existing reference for this
    project's core pipeline**
- **Foundry Local SDK reference**: https://learn.microsoft.com/en-us/azure/foundry-local/reference/reference-sdk-current
- **Foundry Local GitHub**: https://github.com/microsoft/foundry-local
- PyPI package: `foundry-local-sdk` (cross-platform) — for Windows with
  hardware acceleration, `foundry-local-sdk-winml` is the alternative
  (mutually exclusive with the standard package, install only one)

## Prerequisites (must exist before any Python code runs)

1. Foundry Local **CLI** installed:
   - Windows: `winget install Microsoft.FoundryLocal`
   - macOS: `brew tap microsoft/foundrylocal && brew install foundrylocal`
   - This is a native binary install, separate from and prior to the pip package.
2. Python 3.11+ (SDK requires >=3.11)
3. Verify CLI works: `foundry model list` and `foundry model run phi-3.5-mini`
4. Hardware: 8GB RAM minimum, 16GB recommended; AVX2 CPU or supported GPU/NPU

## Architecture (single machine, all local)

```
User query (CLI or simple web UI)
        │
        ▼
Retrieval layer: embed query → cosine similarity search
against chunk embeddings stored in SQLite → top-K chunks
        │
        ▼
Prompt assembly: system prompt (answer only from context,
say "I don't know" if not found) + retrieved chunks + user question
        │
        ▼
Foundry Local chat client (on-device LLM, e.g. phi-3.5-mini)
        │
        ▼
Answer returned to user (offline, no network calls)
```

Data layer: SQLite, single file, table roughly `chunks(id, source, text,
embedding)` with embedding stored as JSON-serialized list or blob.

## Build order (mirrors the program's own phase structure)

### Step 1 — Environment & smoke test
- Install `foundry-local-sdk` via pip (`pip install foundry-local-sdk`)
- Write a minimal script that initializes `FoundryLocalManager`, loads a
  small model (e.g. `phi-3.5-mini` or `qwen2.5-0.5b` for speed), and gets one
  chat completion. This is the "Hello Model" milestone — get this working
  and verified before anything else.

### Step 2 — SQLite schema + ingestion script
- `documents/` folder holding 5–10 short source docs (txt/md).
- Script: chunk each doc into ~1–3 paragraph passages, embed each chunk
  using Foundry Local's embedding model (e.g. `qwen3-embedding-0.6b`), store
  `(source, chunk_text, embedding_json)` rows in SQLite.
- Idempotent: safe to re-run if documents change (clear + re-ingest, or
  upsert by source+chunk hash).

### Step 3 — Retrieval function
- `get_top_chunks(query: str, k: int = 3) -> list[Chunk]`
- Embed the query with the same embedding model used at ingestion time
  (critical — mismatched embedding models will silently produce garbage
  similarity scores).
- Load all stored embeddings into memory, compute cosine similarity, return
  top-K. (Brute-force is fine and correct at this scale — do not add a
  vector DB dependency.)

### Step 4 — Answer generation
- `answer_query(question: str) -> str`
- Calls `get_top_chunks`, assembles a system prompt instructing the model
  to answer only from the provided context and explicitly say when it
  doesn't know, then calls the Foundry Local chat client.
- Include source attribution in the prompt/output if feasible (nice-to-have
  per the plan, stretch goal otherwise).

### Step 5 — Interface
- Default to a CLI loop (`input()` → `answer_query()` → print). This is the
  fastest path to a working end-to-end demo and should be built first
  regardless of what final UI is chosen.
- Optional stretch: Streamlit/Gradio UI, or a minimal Flask/HTML+JS UI —
  only after the CLI path fully works.

### Step 6 — Test harness
- A small set of test questions: some answerable from the docs, some
  deliberately not. Verify correct answers cite plausible source content,
  and unanswerable ones trigger the "I don't know" fallback rather than a
  hallucinated answer.

## Key implementation constraints

- **No cloud calls anywhere** — no OpenAI API key usage, no external
  embedding APIs. Everything routes through the local Foundry Local
  endpoint (it exposes an OpenAI-compatible API, so the `openai` Python
  package can be pointed at `manager.endpoint` — but the backend must stay
  local).
- **Embedding consistency**: the same embedding model must be used for
  ingestion and for query-time embedding.
- **Keep the codebase beginner-legible**: this is teaching code. Prefer
  explicit, readable functions over abstraction. Students will read this
  code, not just run it.
- **Model choice**: prioritize small/fast models (phi-3.5-mini or smaller)
  over quality — the plan explicitly trades accuracy for fast iteration
  feedback during a summer program.

## Non-goals / explicitly out of scope

- No production vector database (SQLite brute-force cosine similarity is
  correct for this scale — 5-10 documents).
- No cloud fallback or hybrid cloud/local mode.
- No auth, no multi-user, no deployment concerns — this runs on a single
  student laptop.

## Deliverable checklist

- [ ] `requirements.txt`
- [ ] `main.py` or clear entry point
- [ ] `ingest.py` (or equivalent) — chunking + embedding + SQLite storage
- [ ] `retrieval.py` — `get_top_chunks()`
- [ ] `chat.py` / core loop — `answer_query()`
- [ ] `documents/` sample folder with 5–10 short docs
- [ ] CLI interface working end-to-end
- [ ] Test script with answerable + unanswerable sample questions
- [ ] README covering: prerequisites, setup (CLI + pip), how to run
      ingestion, how to run the chatbot
