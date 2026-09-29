"""Verify Foundry Local can load a model and return a chat completion."""

from config import CHAT_MODEL
from foundry_client import get_client, get_loaded_model_id


def main():
    client = get_client()
    model_id = get_loaded_model_id(client, CHAT_MODEL)
    print(f"Using loaded model: {model_id}")

    response = client.chat.completions.create(
        model=model_id,
        messages=[{"role": "user", "content": "What is 2 + 2?"}],
    )
    print("\nModel response:")
    print(response.choices[0].message.content)


if __name__ == "__main__":
    main()
