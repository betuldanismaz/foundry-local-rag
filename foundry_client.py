"""Shared helper for talking to a locally running Foundry Local daemon.

Foundry Local exposes an OpenAI-compatible API at <base_url>/v1, so every
script in this project (ingest.py, retrieval.py, chat.py) just needs the
daemon's base URL and a standard `openai` client pointed at it.
"""

import re
import subprocess

from openai import OpenAI


def get_foundry_base_url() -> str:
    """Ask the Foundry Local CLI for the running daemon's base URL."""
    result = subprocess.run(
        ["foundry", "server", "status"], capture_output=True, text=True, check=True
    )
    match = re.search(r"http://[\w.-]+:\d+", result.stdout)
    if not match:
        raise RuntimeError(
            "Could not find Foundry Local's URL. Is the service running? "
            "Try: foundry server start"
        )
    return match.group(0)


def get_client() -> OpenAI:
    """Create an OpenAI client pointed at the local Foundry Local daemon."""
    base_url = get_foundry_base_url()
    return OpenAI(base_url=f"{base_url}/v1", api_key="not-needed")


def get_loaded_model_id(client: OpenAI, alias: str) -> str:
    """Look up the full model id for an alias among currently loaded models."""
    for model in client.models.list().data:
        if model.id.startswith(alias):
            return model.id
    raise RuntimeError(
        f"Model '{alias}' is not loaded. Try: foundry model load {alias}"
    )
