# Step 1 — Environment & Smoke Test

## Goal

Set up the Python environment, install dependencies, and verify that
Foundry Local can load a model and return a chat completion. This is the
"Hello Model" milestone.

## Prerequisites (manual, before this step)

1. Foundry Local CLI is installed:
   - Windows: `winget install Microsoft.FoundryLocal`
   - macOS: `brew tap microsoft/foundrylocal && brew install foundrylocal`
2. CLI works: run `foundry model list` — should print available models
3. Python 3.11+ installed and on PATH

## Tasks

### 1.1 Create `requirements.txt`

```
foundry-local-sdk
```

Notes:
- On Windows with hardware acceleration, `foundry-local-sdk-winml` is an
  alternative — but these are **mutually exclusive**. Install only one.
- No other dependencies needed for the core project. Streamlit/Gradio
  only if the stretch UI goal is attempted later.

### 1.2 Create virtual environment and install

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

### 1.3 Write `smoke_test.py`

A minimal script that:

1. Imports `FoundryLocalManager` from `foundry_local_sdk`
2. Creates a manager instance
3. Lists available models (print them — useful for debugging)
4. Loads a small chat model (try `phi-3.5-mini`, fall back to whatever is
   available)
5. Gets the OpenAI-compatible endpoint from the manager
6. Creates an `openai.OpenAI` client pointed at that local endpoint
7. Sends a single chat completion request with a simple question
   (e.g., "What is 2 + 2?")
8. Prints the response

Key SDK patterns (from Foundry Local Lab reference):
```python
from foundry_local_sdk import FoundryLocalManager

manager = FoundryLocalManager("phi-3.5-mini")

# The manager exposes an OpenAI-compatible endpoint
from openai import OpenAI
client = OpenAI(base_url=manager.endpoint, api_key="foundry-local")

response = client.chat.completions.create(
    model=manager.model_name,
    messages=[{"role": "user", "content": "What is 2 + 2?"}]
)
print(response.choices[0].message.content)
```

### 1.4 Run and verify

```bash
python smoke_test.py
```

Expected: prints a coherent answer to "What is 2 + 2?" (should say "4").
If the model isn't downloaded yet, the SDK will pull it — first run may
be slow.

## Done When

- [ ] `requirements.txt` exists with `foundry-local-sdk`
- [ ] `smoke_test.py` runs without errors
- [ ] A chat completion response prints to the console
- [ ] The response is coherent (model is working, not garbage output)

## Troubleshooting

- **"Model not found"**: Run `foundry model list` to see what's available.
  Try `qwen2.5-0.5b` if phi-3.5-mini isn't listed.
- **Import errors**: Make sure you installed `foundry-local-sdk`, not
  just the CLI. The CLI and the pip package are separate installs.
- **Slow first run**: Normal — the model binary is being downloaded.
  Subsequent runs will be fast.
- **Out of memory**: Try a smaller model like `qwen2.5-0.5b`.
