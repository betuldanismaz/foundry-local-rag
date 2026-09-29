"""Retrieve the most relevant chunks from rag_data.db for a given query,
using cosine similarity against chunk embeddings computed at ingest time.
"""

import json
import math
import sqlite3
from dataclasses import dataclass

from config import EMBEDDING_MODEL
from foundry_client import get_client, get_loaded_model_id

DB_PATH = "rag_data.db"


@dataclass
class Chunk:
    source: str
    text: str
    score: float


def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    mag_a = math.sqrt(sum(a * a for a in vec_a))
    mag_b = math.sqrt(sum(b * b for b in vec_b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


def get_top_chunks(query: str, k: int = 3) -> list[Chunk]:
    client = get_client()
    model_id = get_loaded_model_id(client, EMBEDDING_MODEL)

    query_embedding = client.embeddings.create(input=query, model=model_id).data[0].embedding

    # Brute-force: load every stored embedding into memory and score it
    # against the query. Fine at this scale (dozens of chunks) — a
    # real vector database would only be worth it at thousands+ chunks.
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute("SELECT source, chunk_text, embedding FROM chunks").fetchall()
    conn.close()

    scored_chunks = []
    for source, chunk_text, embedding_json in rows:
        chunk_embedding = json.loads(embedding_json)
        score = cosine_similarity(query_embedding, chunk_embedding)
        scored_chunks.append(Chunk(source=source, text=chunk_text, score=score))

    scored_chunks.sort(key=lambda c: c.score, reverse=True)
    return scored_chunks[:k]


if __name__ == "__main__":
    query = "What is the largest planet?"
    print(f"Query: {query}\n")
    chunks = get_top_chunks(query, k=3)
    for i, chunk in enumerate(chunks, 1):
        print(f"--- Result {i} (score: {chunk.score:.4f}, source: {chunk.source}) ---")
        print(chunk.text[:200])
        print()
