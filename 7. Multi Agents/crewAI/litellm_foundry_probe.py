from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from typing import Any

from litellm import completion


RESOURCE_NAME = os.environ.get("AZURE_RESOURCE_NAME", "ai-engineering-vidvatta1")
RESOURCE_GROUP = os.environ.get("AZURE_RESOURCE_GROUP", "ai-engineering-vidvatta")
ENDPOINT_ROOT = os.environ.get(
    "AZURE_OPENAI_ENDPOINT",
    f"https://{RESOURCE_NAME}.openai.azure.com",
)
DEFAULT_DEPLOYMENT = os.environ.get("AZURE_DEPLOYMENT", "gpt-5.4-mini-2")
API_VERSION = os.environ.get("AZURE_API_VERSION", "2025-04-01-preview")
PROMPT = os.environ.get(
    "LITELLM_TEST_PROMPT",
    "Reply with exactly: OK",
)


@dataclass(frozen=True)
class Attempt:
    name: str
    model: str
    api_base: str
    api_version: str | None = None


def get_api_key() -> str:
    key = os.environ.get("AZURE_API_KEY") or os.environ.get("AZURE_OPENAI_API_KEY")
    if not key:
        raise RuntimeError(
            "Set AZURE_API_KEY or AZURE_OPENAI_API_KEY before running this probe."
        )
    return key


def run_attempt(attempt: Attempt, api_key: str) -> Any:
    kwargs: dict[str, Any] = {
        "model": attempt.model,
        "api_key": api_key,
        "api_base": attempt.api_base,
        "messages": [
            {"role": "system", "content": "You are a concise test harness."},
            {"role": "user", "content": PROMPT},
        ],
        "temperature": 1,
        "max_completion_tokens": 32,
    }
    if attempt.api_version:
        kwargs["api_version"] = attempt.api_version
    return completion(**kwargs)


def main() -> int:
    api_key = get_api_key()
    deployment = os.environ.get("AZURE_DEPLOYMENT", DEFAULT_DEPLOYMENT)

    attempts = [
        Attempt(
            name="openai_v1",
            model=f"openai/{deployment}",
            api_base=f"{ENDPOINT_ROOT.rstrip('/')}/openai/v1/",
            api_version=None,
        ),
        Attempt(
            name="azure_compat",
            model=f"azure/{deployment}",
            api_base=ENDPOINT_ROOT.rstrip("/"),
            api_version=API_VERSION,
        ),
    ]

    print(
        json.dumps(
            {
                "resource_group": RESOURCE_GROUP,
                "resource_name": RESOURCE_NAME,
                "endpoint_root": ENDPOINT_ROOT.rstrip("/"),
                "deployment": deployment,
                "attempt_order": [attempt.name for attempt in attempts],
            },
            indent=2,
        )
    )

    last_error: Exception | None = None
    for attempt in attempts:
        print(f"\nTrying {attempt.name} -> {attempt.model}")
        try:
            response = run_attempt(attempt, api_key)
            message = response.choices[0].message.content
            print(
                json.dumps(
                    {
                        "attempt": attempt.name,
                        "model": response.model,
                        "content": message,
                    },
                    indent=2,
                )
            )
            return 0
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            print(f"{attempt.name} failed: {exc}", file=sys.stderr)

    raise RuntimeError("All LiteLLM attempts failed") from last_error


if __name__ == "__main__":
    raise SystemExit(main())
