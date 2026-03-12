import os
from datetime import datetime

import requests

MODEL = "us.anthropic.claude-3-5-haiku-20241022-v1:0"
AWS_REGION = os.environ.get("AWS_REGION", "us-west-2")
BEDROCK_TOKEN = os.environ.get("AWS_BEARER_TOKEN_BEDROCK", "")
PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "prompts")

EXTRACT_REMINDER_TOOL = {
    "name": "extract_reminder",
    "description": "Extract reminder details from the user's message and provide a reply.",
    "input_schema": {
        "type": "object",
        "properties": {
            "agenda": {
                "type": ["string", "null"],
                "description": "The cleaned reminder text, or null if not yet provided.",
            },
            "date": {
                "type": ["string", "null"],
                "description": "Date in YYYY-MM-DD format, or null if not yet provided.",
            },
            "time": {
                "type": ["string", "null"],
                "description": "Time in HH:MM 24-hour format, or null if not yet provided.",
            },
            "complete": {
                "type": "boolean",
                "description": "True if agenda, date, AND time are all present.",
            },
            "reply": {
                "type": "string",
                "description": "The message to display to the user.",
            },
        },
        "required": ["agenda", "date", "time", "complete", "reply"],
    },
}


def _load_system_prompt():
    """Load the system prompt from prompts/skill.md and inject current datetime."""
    path = os.path.join(PROMPTS_DIR, "skill.md")
    with open(path, "r") as f:
        template = f.read()
    now = datetime.now()
    return template.replace(
        "{current_datetime}",
        now.strftime("%Y-%m-%d %H:%M:%S (%A)"),
    )


class BedrockAPIError(Exception):
    """Raised when the Bedrock API returns a non-200 response."""

    def __init__(self, status_code, message):
        self.status_code = status_code
        self.message = message
        super().__init__(f"Bedrock API error {status_code}: {message}")


def get_reminder_extraction(conversation_history):
    """Send conversation history to Claude via AWS Bedrock and get structured reminder extraction.

    Uses the Bedrock API key (bearer token) from AWS_BEARER_TOKEN_BEDROCK env var.

    Args:
        conversation_history: List of {"role": "user"|"assistant", "content": str}

    Returns:
        dict with keys: agenda, date, time, complete, reply

    Raises:
        BedrockAPIError: on API failures
        ValueError: if the response doesn't contain the expected tool call
    """
    url = f"https://bedrock-runtime.{AWS_REGION}.amazonaws.com/model/{MODEL}/invoke"

    body = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1024,
        "system": _load_system_prompt(),
        "tools": [EXTRACT_REMINDER_TOOL],
        "tool_choice": {"type": "tool", "name": "extract_reminder"},
        "messages": conversation_history,
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {BEDROCK_TOKEN}",
    }

    resp = requests.post(url, headers=headers, json=body, timeout=30)

    if resp.status_code != 200:
        raise BedrockAPIError(resp.status_code, resp.text)

    data = resp.json()

    for block in data.get("content", []):
        if block.get("type") == "tool_use" and block.get("name") == "extract_reminder":
            return block["input"]

    raise ValueError("LLM response did not contain expected extract_reminder tool call")
