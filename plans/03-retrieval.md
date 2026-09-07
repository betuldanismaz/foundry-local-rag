# Step 3 — Retrieval Function

## Goal

Build the retrieval layer: given a user query, embed it with the same
embedding model used at ingestion, compute cosine similarity against all
stored chunks, and return the top-K most relevant chunks.

## Depends On

Step 2 complete — `rag_data.db` populated with chunks and embeddings.

## Tasks

### 3.1 Write `retrieval.py`

This module exports one main function and its supporting pieces:

**a) Cosine similarity function**
```python
def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
```
- Compute dot product / (magnitude_a * magnitude_b)
- Pure Python with standard library only (no numpy) — keeps dependencies
  minimal and the math visible to students
- Handle edge case: if either vector has zero magnitude, return 0.0

Implementation:
```python
import math

def cosine_similarity(vec_a, vec_b):
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    mag_a = math.sqrt(sum(a * a for a in vec_a))
    mag_b = math.sqrt(sum(b * b for b in vec_b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)
```

**b) Chunk data structure**
Use a simple dataclass or named tuple to hold retrieved chunks:
```python
from dataclasses import dataclass

@dataclass
class Chunk:
    source: str
    text: str
    score: float
```

**c) Main retrieval function**
```python
def get_top_chunks(query: str, k: int = 3) -> list[Chunk]:
```

Steps:
1. Initialize FoundryLocalManager with the **same embedding model** used
   in `ingest.py` (e.g., `qwen3-embedding-0.6b`)
2. Create OpenAI client pointed at `manager.endpoint`
3. Embed the query using the same `client.embeddings.create()` call
4. Load all rows from SQLite: `SELECT source, chunk_text, embedding FROM chunks`
5. For each row:
   - Parse the embedding from JSON
   - Compute cosine similarity with the query embedding
6. Sort by similarity (descending)
7. Return top-K as `Chunk` objects

**d) Optimization note for students**
The function loads all embeddings into memory on every call. This is
intentional and correct at this scale (dozens of chunks). For thousands+
of chunks, you'd use a vector database — but that's out of scope. Add
a brief comment or print noting this design choice.

### 3.2 Add a standalone test at the bottom

```python
if __name__ == "__main__":
    query = "What is the largest planet?"
    print(f"Query: {query}\n")
    chunks = get_top_chunks(query, k=3)
    for i, chunk in enumerate(chunks, 1):
        print(f"--- Result {i} (score: {chunk.score:.4f}, source: {chunk.source}) ---")
        print(chunk.text[:200])
        print()
```

### 3.3 Run and verify

```bash
python retrieval.py
```

Verification:
- Returns chunks without errors
- Top results are **relevant** to the query (e.g., a question about
  Jupiter should return Jupiter-related chunks, not random text)
- Scores are between 0 and 1 (cosine similarity range for non-negative
  embeddings — may occasionally go slightly negative)
- Results are ranked by score (highest first)

Test with multiple queries:
- A query matching a specific document ("Tell me about Mars")
- A general query ("What planets are in the solar system?")
- An unrelated query ("What is the company vacation policy?") — should
  return low-scoring chunks from space docs, or the company policy doc

## Done When

- [ ] `retrieval.py` exists with `get_top_chunks()`, `cosine_similarity()`, and `Chunk`
- [ ] Running it standalone prints relevant chunks for a test query
- [ ] Results are ranked by similarity score
- [ ] The same embedding model is used as in `ingest.py`
- [ ] Cosine similarity math is correct (pure Python, no numpy)

## Critical Constraint

**Embedding model consistency**: `retrieval.py` MUST use the exact same
embedding model as `ingest.py`. If they differ, cosine similarity scores
will be meaningless. Consider extracting the model name to a shared
constant (e.g., in a `config.py` or at the top of both files).

## Troubleshooting

- **All scores near 0 or identical**: Likely an embedding model mismatch
  between ingest and query time. Verify both use the same model string.
- **Scores all very high (>0.95)**: The embedding model may not be
  discriminative enough, or chunks are too similar. Check that different
  topics produce different scores.
- **Slow retrieval**: Loading and comparing ~30 embeddings should be
  near-instant. If slow, the bottleneck is likely model loading or the
  embedding API call — that's expected on first call.
