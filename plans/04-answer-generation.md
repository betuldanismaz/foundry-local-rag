# Step 4 — Answer Generation

## Goal

Build the core RAG pipeline function: retrieve relevant chunks for a
question, assemble a grounded prompt with those chunks as context, and
call the local LLM to generate an answer.

## Depends On

Step 3 complete — `get_top_chunks()` returning relevant, scored chunks.

## Tasks

### 4.1 Write `chat.py`

This module ties retrieval to generation.

**a) System prompt**

Define a clear system prompt that instructs the model to:
- Answer ONLY based on the provided context
- Say "I don't know" or "I don't have enough information" when the
  context doesn't contain the answer
- Cite which source document the information came from (if feasible)
- Keep answers concise and factual

```python
SYSTEM_PROMPT = """You are a helpful assistant that answers questions based only on the provided context.

Rules:
- Only use information from the context below to answer the question.
- If the context does not contain enough information to answer, say "I don't have enough information to answer that question."
- When possible, mention which source document your answer comes from.
- Keep your answers concise and factual."""
```

**b) Context formatting function**
```python
def format_context(chunks: list[Chunk]) -> str:
```
- Takes the list of retrieved chunks and formats them into a string
  the LLM can read
- Include the source filename for each chunk so the model can cite it

Example format:
```
[Source: earth.txt]
Earth is the third planet from the Sun...

[Source: mars.txt]
Mars is the fourth planet from the Sun...
```

**c) Main answer function**
```python
def answer_query(question: str) -> str:
```

Steps:
1. Call `get_top_chunks(question, k=3)` from `retrieval.py`
2. Format the chunks into a context string
3. Initialize FoundryLocalManager with the **chat model**
   (e.g., `phi-3.5-mini`) — note: this is a different model than the
   embedding model used in retrieval
4. Create OpenAI client pointed at `manager.endpoint`
5. Build the messages list:
   ```python
   messages = [
       {"role": "system", "content": SYSTEM_PROMPT + "\n\nContext:\n" + context},
       {"role": "user", "content": question}
   ]
   ```
6. Call `client.chat.completions.create()` with the messages
7. Return the response text

**d) Optional: include source attribution in output**
If the model doesn't naturally cite sources, append a "Sources" line:
```python
sources = set(chunk.source for chunk in chunks)
answer = response.choices[0].message.content
return f"{answer}\n\nSources: {', '.join(sources)}"
```

### 4.2 Model management consideration

This step uses the **chat model** (phi-3.5-mini), while retrieval uses
the **embedding model** (qwen3-embedding-0.6b). These are different
models serving different purposes:
- Embedding model: converts text to vectors for similarity search
- Chat model: generates natural language answers

The FoundryLocalManager can manage model loading. If both models need
to be loaded simultaneously, verify that the system has enough RAM.
On 8GB machines, you may need to unload one before loading the other —
the SDK should handle this, but watch for OOM errors.

### 4.3 Add standalone test

```python
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
```

### 4.4 Run and verify

```bash
python chat.py
```

Verification:
- Answerable questions get correct, grounded answers
- Answers reference content that's actually in the documents
- The "meaning of life" question (not in docs) triggers the "I don't
  know" fallback — NOT a hallucinated answer
- Source attribution appears (either from the model or appended)

## Done When

- [ ] `chat.py` exists with `answer_query()` function
- [ ] Answerable questions produce correct, grounded answers
- [ ] Unanswerable questions trigger "I don't know" (no hallucination)
- [ ] Source documents are cited in or appended to the answer
- [ ] The chat model (phi-3.5-mini) is used for generation, NOT the
      embedding model

## Important Design Notes

- The system prompt is the key control lever for answer quality. If the
  model hallucinates or ignores context, refine the system prompt first.
- Temperature should be low (0.1-0.3 or even 0) for factual Q&A to
  reduce randomness. Consider setting `temperature=0.1` in the
  completions call.
- `max_tokens` can be set to limit answer length (e.g., 500) — prevents
  runaway generation on vague questions.

## Troubleshooting

- **Model ignores context and answers from training data**: Strengthen
  the system prompt. Add "Do NOT use your training knowledge." Make the
  context block clearly delimited.
- **"I don't know" for everything**: Check that chunks are being
  retrieved and included in the prompt. Print the assembled messages
  to debug.
- **OOM errors**: The chat model + embedding model together may exceed
  RAM. The SDK should manage model loading/unloading, but if not, ensure
  the embedding model is unloaded before loading the chat model.
- **Very slow responses**: Normal for first call (model loading). If
  consistently slow, try a smaller chat model.
