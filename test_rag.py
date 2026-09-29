"""Automated test harness for the RAG pipeline.

Not a unit-test framework — a simple script that runs a fixed set of
questions and prints pass/fail results for a human to review. LLM output
is non-deterministic, so these checks look for keywords/phrases rather
than exact matches. A single FAIL doesn't necessarily mean something is
broken — re-run and use judgment, especially for the answerable cases.
The unanswerable cases matter more: a model that hallucinates instead of
refusing is the main failure mode RAG is meant to prevent.
"""

from chat import answer_query

answerable = [
    {
        "question": "What is the largest planet in the solar system?",
        "expected_keywords": ["Jupiter"],
        "expected_source": "jupiter.txt",
    },
    {
        "question": "How many moons does Earth have?",
        "expected_keywords": ["Moon", "one", "1"],
        "expected_source": "earth.txt",
    },
    {
        "question": "What is the hottest planet in the solar system?",
        "expected_keywords": ["Venus"],
        "expected_source": "venus.txt",
    },
    {
        "question": "How far is Mars from the Sun?",
        "expected_keywords": ["228 million", "1.52"],
        "expected_source": "mars.txt",
    },
    {
        "question": "What is Saturn best known for?",
        "expected_keywords": ["ring"],
        "expected_source": "saturn.txt",
    },
    {
        "question": "How many days per week can employees work remotely?",
        "expected_keywords": ["three", "3"],
        "expected_source": "company_policy.txt",
    },
]

unanswerable = [
    {
        "question": "What is the recipe for chocolate cake?",
        "refusal_phrases": [
            "don't know", "don't have", "not enough information",
            "no information", "cannot answer",
        ],
    },
    {
        "question": "Who won the 2024 Super Bowl?",
        "refusal_phrases": [
            "don't know", "don't have", "not enough information",
            "no information", "cannot answer",
        ],
    },
    {
        "question": "What is the population of Tokyo?",
        "refusal_phrases": [
            "don't know", "don't have", "not enough information",
            "no information", "cannot answer",
        ],
    },
]

edge_cases = [
    "Mars?",
    "Can you tell me, in as much detail as possible, what makes Jupiter "
    "different from the smaller rocky planets closer to the Sun?",
]


def run_tests():
    passed = 0
    failed = 0

    print("=== Running Answerable Tests ===\n")
    for test in answerable:
        answer = answer_query(test["question"])
        answer_lower = answer.lower()

        has_keyword = any(
            kw.lower() in answer_lower for kw in test["expected_keywords"]
        )

        status = "PASS" if has_keyword else "FAIL"
        passed += has_keyword
        failed += not has_keyword

        print(f"[{status}] {test['question']}")
        print(f"  Answer: {answer[:200]}...")
        print()

    print("=== Running Unanswerable Tests ===\n")
    for test in unanswerable:
        answer = answer_query(test["question"])
        answer_lower = answer.lower()

        has_refusal = any(
            phrase in answer_lower for phrase in test["refusal_phrases"]
        )

        status = "PASS" if has_refusal else "FAIL"
        passed += has_refusal
        failed += not has_refusal

        print(f"[{status}] {test['question']}")
        print(f"  Answer: {answer[:200]}...")
        print()

    print("=== Running Edge Cases (informational, not pass/fail) ===\n")
    for question in edge_cases:
        answer = answer_query(question)
        print(f"Q: {question}")
        print(f"  Answer: {answer[:200]}...")
        print()

    print(
        f"=== Results: {passed} passed, {failed} failed out of "
        f"{passed + failed} tests ==="
    )


if __name__ == "__main__":
    run_tests()
