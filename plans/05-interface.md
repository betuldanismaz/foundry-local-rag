# Step 5 — CLI Interface

## Goal

Build the main entry point: a simple command-line loop where the user
types questions and gets answers. This is the "working demo" milestone.

## Depends On

Step 4 complete — `answer_query()` returning grounded answers.

## Tasks

### 5.1 Write `main.py`

A clean, minimal CLI loop.

**Structure:**
```python
from chat import answer_query

def main():
    print("=== Local RAG Q&A Assistant ===")
    print("Ask questions about the loaded documents.")
    print("Type 'quit' or 'exit' to stop.\n")

    while True:
        question = input("You: ").strip()

        if not question:
            continue

        if question.lower() in ("quit", "exit"):
            print("Goodbye!")
            break

        print("\nThinking...\n")
        answer = answer_query(question)
        print(f"Assistant: {answer}\n")

if __name__ == "__main__":
    main()
```

**Key design points:**
- The `"Thinking..."` message is important — model inference takes a
  few seconds and users need feedback that something is happening
- Handle empty input gracefully (skip, don't crash)
- Clean exit on "quit" or "exit"
- Print formatting: clear separation between question and answer

### 5.2 Optional: Add error handling

Wrap the answer call to handle common failures gracefully:
```python
try:
    answer = answer_query(question)
    print(f"Assistant: {answer}\n")
except Exception as e:
    print(f"Error: {e}\n")
    print("Something went wrong. Try again or type 'quit' to exit.\n")
```

This prevents a single failed query from crashing the whole session —
important for a demo environment where students may type unexpected input.

### 5.3 Optional: Startup check

Before entering the loop, verify that:
1. `rag_data.db` exists (if not, tell the user to run `ingest.py` first)
2. The database has chunks in it (if empty, same message)

```python
import os
import sqlite3

def check_database():
    if not os.path.exists("rag_data.db"):
        print("Error: rag_data.db not found. Run 'python ingest.py' first.")
        return False
    conn = sqlite3.connect("rag_data.db")
    count = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
    conn.close()
    if count == 0:
        print("Error: No chunks in database. Run 'python ingest.py' first.")
        return False
    print(f"Database loaded: {count} chunks available.\n")
    return True
```

### 5.4 Run end-to-end

```bash
# Make sure documents are ingested
python ingest.py

# Run the chatbot
python main.py
```

Test the full loop:
1. Ask a question answerable from the docs
2. Ask a follow-up question on a different topic in the docs
3. Ask something NOT in the docs — verify "I don't know" behavior
4. Type empty input — should not crash
5. Type "quit" — should exit cleanly

## Done When

- [ ] `main.py` exists and runs as the entry point
- [ ] CLI loop accepts questions and prints answers
- [ ] Empty input is handled (no crash)
- [ ] "quit" / "exit" exits cleanly
- [ ] End-to-end flow works: ingest docs → run main → ask questions → get answers
- [ ] Unanswerable questions get "I don't know" responses

## Stretch Goals (only after CLI works)

These are NOT part of the core plan. Only attempt after the CLI is solid:

- **Streamlit UI**: Wrap `answer_query()` in a Streamlit chat interface.
  Add `streamlit` to requirements.txt. Create `app.py`:
  ```python
  import streamlit as st
  from chat import answer_query
  st.title("Local RAG Q&A")
  question = st.text_input("Ask a question:")
  if question:
      st.write(answer_query(question))
  ```
- **Gradio UI**: Similar wrapper using Gradio's ChatInterface
- **Flask + HTML**: Minimal web UI with a form and response display

All stretch UIs just call `answer_query()` — the core logic stays in
`chat.py`, not duplicated.
