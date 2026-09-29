"""CLI entry point for the Local RAG Q&A Assistant."""

import os
import sqlite3

from chat import answer_query


def check_database() -> bool:
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


def main():
    print("=== Local RAG Q&A Assistant ===")
    print("Ask questions about the loaded documents.")
    print("Type 'quit' or 'exit' to stop.\n")

    if not check_database():
        return

    while True:
        question = input("You: ").strip()

        if not question:
            continue

        if question.lower() in ("quit", "exit"):
            print("Goodbye!")
            break

        print("\nThinking...\n")
        try:
            answer = answer_query(question)
            print(f"Assistant: {answer}\n")
        except Exception as e:
            print(f"Error: {e}\n")
            print("Something went wrong. Try again or type 'quit' to exit.\n")


if __name__ == "__main__":
    main()
