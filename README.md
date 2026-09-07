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

## Prerequisites

1. **Foundry Local CLI** (installed separately from the Python package):

   - Windows: `winget install Microsoft.FoundryLocal`
   - macOS: `brew tap microsoft/foundrylocal && brew install foundrylocal`

2. **Python 3.11+**

3. **Hardware**: 8 GB RAM minimum, 16 GB recommended. AVX2-capable CPU or a supported GPU/NPU.

4. **Verify the CLI works** before continuing:

   ```
   foundry model list
   ```

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

# Install dependencies
pip install -r requirements.txt
```

## Running the Project

### 1. Ingest documents

Place your text or markdown files in the `documents/` folder (sample docs are included), then run:

```bash
python ingest.py
```

This chunks each document, embeds the chunks using a local embedding model, and stores everything in `rag_data.db`. Safe to re-run — it rebuilds the database from scratch each time.

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
├── documents/       Sample documents the chatbot answers from
├── requirements.txt Python dependencies
├── smoke_test.py    Verify Foundry Local is working
├── ingest.py        Chunk + embed documents → SQLite
├── retrieval.py     Query embedding + cosine similarity search
├── chat.py          Prompt assembly + LLM answer generation
├── main.py          CLI entry point
├── test_rag.py      Automated test harness
└── rag_data.db      Generated database (not checked in)
```

## Adding Your Own Documents

1. Add `.txt` or `.md` files to the `documents/` folder
2. Re-run `python ingest.py`
3. Start the chatbot with `python main.py`

The chatbot will only answer based on what's in the documents. If you ask about something not covered, it will say so.

## Models Used

| Purpose    | Model                  | Notes                          |
|------------|------------------------|--------------------------------|
| Chat       | `phi-3.5-mini`         | Small, fast, good for teaching |
| Embeddings | `qwen3-embedding-0.6b` | Converts text to vectors       |

Models are downloaded automatically on first use. The first run will be slower while models are pulled.

## Troubleshooting

- **"Model not found"** — Run `foundry model list` to see available models. The exact model names may vary by platform.
- **Import errors** — Make sure you installed the pip package (`pip install foundry-local-sdk`), not just the CLI. They are separate.
- **Slow first run** — Normal. The model binary is being downloaded. Subsequent runs are fast.
- **Out of memory** — Try a smaller chat model like `qwen2.5-0.5b`.
- **Wrong or irrelevant answers** — Re-run `python ingest.py` to make sure the database matches your current documents.
