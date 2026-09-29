"""Shared model names. ingest.py and retrieval.py must use the same
EMBEDDING_MODEL — mismatched embedding models produce meaningless
similarity scores.
"""

CHAT_MODEL = "phi-3.5-mini"
EMBEDDING_MODEL = "qwen3-embedding-0.6b"
