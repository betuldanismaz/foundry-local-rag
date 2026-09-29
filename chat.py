"""Answer a question by retrieving relevant document chunks and asking the
local chat model to answer using only that context.
"""

from config import CHAT_MODEL
from foundry_client import get_client, get_loaded_model_id
from retrieval import Chunk, get_top_chunks

SYSTEM_PROMPT = """You are a helpful assistant that answers questions based only on the provided context.

Rules:
- Only use information from the context below to answer the question.
- If the context does not contain enough information to answer, say "I don't have enough information to answer that question."
- When possible, mention which source document your answer comes from.
- Keep your answers concise and factual."""


def format_context(chunks: list[Chunk]) -> str:
    return "\n\n".join(f"[Source: {chunk.source}]\n{chunk.text}" for chunk in chunks)


def answer_query(question: str) -> str:
    chunks = get_top_chunks(question, k=3)
    context = format_context(chunks)

    client = get_client()
    model_id = get_loaded_model_id(client, CHAT_MODEL)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT + "\n\nContext:\n" + context},
        {"role": "user", "content": question},
    ]
    response = client.chat.completions.create(
        model=model_id,
        messages=messages,
        temperature=0.1,
        max_tokens=500,
    )
    answer = response.choices[0].message.content

    sources = sorted(set(chunk.source for chunk in chunks))
    return f"{answer}\n\nSources: {', '.join(sources)}"


if __name__ == "__main__":
    test_questions = [
        "What is the largest planet in the solar system?",
        "How far is Mars from the Sun?",
        "What is the meaning of life?",  # Should trigger "I don't know"
    ]
    for q in test_questions:
        print(f"Q: {q}")
        print(f"A: {answer_query(q)}")
        print()
