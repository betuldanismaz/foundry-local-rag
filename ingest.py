"""Chunk the documents in documents/, embed each chunk, and store them in
SQLite (rag_data.db). Safe to re-run — rebuilds the database from scratch.
"""

import json
import sqlite3
from pathlib import Path

from openai import OpenAI

from config import EMBEDDING_MODEL
from foundry_client import get_client, get_loaded_model_id

DOCUMENTS_DIR = Path("documents")
DB_PATH = "rag_data.db"
CHUNK_SIZE = 500


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE) -> list[str]:
    """Split text into chunks of roughly `chunk_size` characters.

    Splits on paragraph boundaries (blank lines) first. If a paragraph is
    still too long, splits it further on sentence boundaries.
    """
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    chunks = []
    for paragraph in paragraphs:
        if len(paragraph) <= chunk_size:
            chunks.append(paragraph)
            continue

        sentences = paragraph.replace("\n", " ").split(". ")
        current = ""
        for sentence in sentences:
            candidate = f"{current} {sentence}".strip() if current else sentence
            if len(candidate) > chunk_size and current:
                chunks.append(current.strip())
                current = sentence
            else:
                current = candidate
        if current:
            chunks.append(current.strip())

    return [c for c in chunks if c]


def get_embedding(text: str, client: OpenAI, model_name: str) -> list[float]:
    response = client.embeddings.create(input=text, model=model_name)
    return response.data[0].embedding


def create_table(conn: sqlite3.Connection) -> None:
    conn.execute("DROP TABLE IF EXISTS chunks")
    conn.execute(
        """
        CREATE TABLE chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            chunk_text TEXT NOT NULL,
            embedding TEXT NOT NULL
        )
        """
    )
    conn.commit()


def main():
    client = get_client()
    model_id = get_loaded_model_id(client, EMBEDDING_MODEL)
    print(f"Using embedding model: {model_id}")

    conn = sqlite3.connect(DB_PATH)
    create_table(conn)

    total_chunks = 0
    for file_path in sorted(DOCUMENTS_DIR.glob("*.txt")) + sorted(DOCUMENTS_DIR.glob("*.md")):
        text = file_path.read_text(encoding="utf-8")
        chunks = chunk_text(text)

        for chunk in chunks:
            embedding = get_embedding(chunk, client, model_id)
            conn.execute(
                "INSERT INTO chunks (source, chunk_text, embedding) VALUES (?, ?, ?)",
                (file_path.name, chunk, json.dumps(embedding)),
            )

        conn.commit()
        total_chunks += len(chunks)
        print(f"Ingested {file_path.name}: {len(chunks)} chunks")

    print(f"\nTotal chunks ingested: {total_chunks}")
    conn.close()


if __name__ == "__main__":
    main()
