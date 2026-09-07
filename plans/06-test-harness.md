# Step 6 — Test Harness

## Goal

Create an automated test script that runs a set of predefined questions
through the RAG pipeline and checks whether answers are grounded (not
hallucinated) and whether unanswerable questions are correctly refused.

## Depends On

Step 5 complete — full pipeline working end-to-end via `main.py`.

## Tasks

### 6.1 Write `test_rag.py`

This is not a unit test framework — it's a simple script that runs
questions and prints pass/fail results a human can review. LLM output
is non-deterministic, so tests check for heuristic signals rather than
exact string matches.

**Structure:**

```python
from chat import answer_query

test_cases = [
    # (question, expected_behavior, keywords_that_should_appear)
    # expected_behavior: "answer" = should give a real answer
    #                    "refuse" = should say "I don't know" or similar
]
```

**Test categories:**

**a) Answerable questions (should produce grounded answers)**
- Questions directly addressed by the documents
- Check that the answer contains expected keywords from the source docs
- Check that a source attribution is present

```python
answerable = [
    {
        "question": "What is the largest planet in the solar system?",
        "expected_keywords": ["Jupiter"],
        "expected_source": "jupiter.txt",
    },
    {
        "question": "How many moons does Earth have?",
        "expected_keywords": ["Moon", "one", "1"],
        "expected_source": "moon.txt",
    },
    # Add 3-5 more based on actual document content
]
```

**b) Unanswerable questions (should trigger refusal)**
- Questions about topics NOT in the documents
- Check that the answer contains refusal phrases

```python
unanswerable = [
    {
        "question": "What is the recipe for chocolate cake?",
        "refusal_phrases": ["don't know", "don't have", "not enough information",
                           "no information", "cannot answer"],
    },
    {
        "question": "Who won the 2024 Super Bowl?",
        "refusal_phrases": ["don't know", "don't have", "not enough information"],
    },
    # Add 2-3 more
]
```

**c) Edge cases**
- Very short query ("Mars?")
- Very long query (full sentence with extra words)
- Query with typos (optional — tests robustness of embedding similarity)

### 6.2 Test runner logic

```python
def run_tests():
    passed = 0
    failed = 0
    results = []

    print("=== Running Answerable Tests ===\n")
    for test in answerable:
        answer = answer_query(test["question"])
        answer_lower = answer.lower()

        # Check if any expected keyword appears
        has_keyword = any(kw.lower() in answer_lower
                        for kw in test["expected_keywords"])

        status = "PASS" if has_keyword else "FAIL"
        if has_keyword:
            passed += 1
        else:
            failed += 1

        print(f"[{status}] {test['question']}")
        print(f"  Answer: {answer[:200]}...")
        print()

    print("=== Running Unanswerable Tests ===\n")
    for test in unanswerable:
        answer = answer_query(test["question"])
        answer_lower = answer.lower()

        # Check if any refusal phrase appears
        has_refusal = any(phrase in answer_lower
                        for phrase in test["refusal_phrases"])

        status = "PASS" if has_refusal else "FAIL"
        if has_refusal:
            passed += 1
        else:
            failed += 1

        print(f"[{status}] {test['question']}")
        print(f"  Answer: {answer[:200]}...")
        print()

    print(f"=== Results: {passed} passed, {failed} failed out of "
          f"{passed + failed} tests ===")

if __name__ == "__main__":
    run_tests()
```

### 6.3 Run and interpret results

```bash
python test_rag.py
```

Important notes about interpreting results:
- LLM output is **non-deterministic** — running twice may give different
  results. A test that fails once may pass next time.
- These tests are **heuristic**, not exact. A "FAIL" on an answerable
  question might mean the model phrased the answer differently (used a
  synonym for the expected keyword).
- The **unanswerable tests are more important** — a model that
  hallucinates answers to unanswerable questions is the main failure
  mode RAG is meant to prevent.
- If most tests pass, the system is working. If most fail, debug the
  pipeline (retrieval quality, system prompt, model choice).

### 6.4 Tune based on results

If tests reveal issues:
- **Model hallucinates on unanswerable questions**: Strengthen the system
  prompt in `chat.py`. Make the refusal instruction more emphatic.
- **Wrong chunks retrieved**: Check the retrieval scores. If top chunks
  are irrelevant, the embedding model may need to change, or chunks
  may be too large/small.
- **Correct chunks but wrong answer**: The chat model may be too small
  to follow instructions well. Try a slightly larger model if RAM allows.

## Done When

- [ ] `test_rag.py` exists with both answerable and unanswerable test cases
- [ ] Script runs and prints pass/fail for each test
- [ ] Most answerable tests pass (correct keywords in answer)
- [ ] Most unanswerable tests pass (refusal phrase detected)
- [ ] Results are printed in a clear, reviewable format

## File Deliverables After All Steps

At this point, the full project should contain:

```
foundrylocal/
├── documents/          # 5-10 sample docs
├── requirements.txt    # foundry-local-sdk (+ openai if needed)
├── smoke_test.py       # Step 1 verification
├── ingest.py           # Step 2 chunking + embedding
├── retrieval.py        # Step 3 similarity search
├── chat.py             # Step 4 prompt assembly + generation
├── main.py             # Step 5 CLI entry point
├── test_rag.py         # Step 6 test harness
└── rag_data.db         # Generated database (not committed)
```

Final verification: run the full flow from scratch:
```bash
pip install -r requirements.txt
python ingest.py
python main.py
# Ask a few questions interactively
python test_rag.py
```
