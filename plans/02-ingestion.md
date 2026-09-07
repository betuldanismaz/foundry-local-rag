# Step 2 — SQLite Schema + Ingestion Script

## Goal

Build the data pipeline: take a folder of short documents, chunk them into
passages, embed each chunk using Foundry Local's embedding model, and store
everything in a SQLite database.

## Depends On

Step 1 complete — Foundry Local SDK working, can get completions.

## Tasks

### 2.1 Create `documents/` folder with sample content

Populate with 5-10 short text or markdown files on a focused topic.
Good choices for a teaching project:
- Facts about a specific subject (e.g., solar system, world capitals,
  a fictional company handbook)
- Keep each file 1-3 paragraphs — short enough to inspect manually
- Include some overlap between docs (tests retrieval quality)
- Include at least one doc on a distinct topic (tests "I don't know"
  fallback for unrelated questions)

Example files:
```
documents/
├── earth.txt          # Facts about Earth
├── mars.txt           # Facts about Mars
├── jupiter.txt        # Facts about Jupiter
├── solar_system.txt   # General solar system overview
├── moon.txt           # Earth's moon
├── sun.txt            # The Sun
├── venus.txt          # Facts about Venus
├── saturn.txt         # Facts about Saturn
└── company_policy.txt # Unrelated doc (for "I don't know" testing)
```

### 2.2 Design the SQLite schema

Single table, simple as possible:

```sql
CREATE TABLE IF NOT EXISTS chunks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL,        -- filename the chunk came from
    chunk_text TEXT NOT NULL,    -- the actual text passage
    embedding TEXT NOT NULL      -- JSON-serialized list of floats
);
```

Notes:
- Embedding stored as JSON text (not blob) — easier to inspect and debug
  for beginners. Performance is irrelevant at this scale.
- No unique constraint needed if we clear-and-rebuild on each ingest run.

### 2.3 Write `ingest.py`

The script should do these things in order:

**a) Chunking function**
```python
def chunk_text(text: str, chunk_size: int = 500) -> list[str]:
```
- Split text into chunks of roughly `chunk_size` characters
- Split on paragraph boundaries (double newline) first, then sentence
  boundaries if a paragraph is too long
- Keep it simple — no sliding window, no overlap. Beginners need to see
  what a chunk is.
- Return a list of non-empty strings

**b) Embedding function**
```python
def get_embedding(text: str, client, model_name: str) -> list[float]:
```
- Use the OpenAI-compatible embeddings endpoint:
  ```python
  response = client.embeddings.create(input=text, model=model_name)
  return response.data[0].embedding
  ```
- The embedding model must be loaded through FoundryLocalManager

**c) Main ingestion flow**
1. Initialize FoundryLocalManager with the **embedding model**
   (e.g., `qwen3-embedding-0.6b`)
2. Create OpenAI client pointed at `manager.endpoint`
3. Connect to SQLite database (`rag_data.db`)
4. Drop and recreate the `chunks` table (idempotent — safe to re-run)
5. For each file in `documents/`:
   - Read the file content
   - Chunk it
   - For each chunk: get embedding, insert row into SQLite
   - Print progress (e.g., "Ingested earth.txt: 3 chunks")
6. Print summary (total chunks ingested)
7. Close database connection

### 2.4 Run and verify

```bash
python ingest.py
```

Verification:
- Script completes without errors
- `rag_data.db` file is created
- Inspect the database to confirm data:
  ```bash
  python -c "
  import sqlite3, json
  conn = sqlite3.connect('rag_data.db')
  rows = conn.execute('SELECT source, length(chunk_text), length(embedding) FROM chunks').fetchall()
  for r in rows:
      print(f'{r[0]}: text={r[1]} chars, embedding={r[2]} chars')
  print(f'Total chunks: {len(rows)}')
  conn.close()
  "
  ```
- Each row should have a non-empty embedding (JSON list of floats)
- Total chunk count should be reasonable (roughly 15-40 for 8-10 short docs)

## Done When

- [ ] `documents/` folder has 5-10 sample text files
- [ ] `ingest.py` runs without errors
- [ ] `rag_data.db` is created with populated `chunks` table
- [ ] Each chunk has a source, text, and valid embedding
- [ ] Re-running `ingest.py` works cleanly (idempotent)

## Important Notes

- **Remember the embedding model name** — Step 3 must use the exact same
  model for query embedding. Consider defining it as a constant in a
  shared config or at the top of both files.
- The embedding model is different from the chat model. Don't mix them up.
- `qwen3-embedding-0.6b` is the recommended embedding model. Check
  `foundry model list` for available embedding models if it's not there.

## Troubleshooting

- **Embedding model not found**: Run `foundry model list` and look for
  models with "embedding" in the name. The exact name may vary.
- **Very slow ingestion**: Embedding 30-40 chunks should take under a
  minute on most hardware. If much slower, the model may be swapping.
  Try fewer/shorter documents.
- **JSON serialization of embeddings**: Use `json.dumps(embedding)` to
  store, `json.loads(row)` to load back. Standard library, no extras.
