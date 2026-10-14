import os
import json
import anthropic
from dotenv import load_dotenv

load_dotenv()  # reads ANTHROPIC_API_KEY and ANTHROPIC_MODEL from .env
client = anthropic.Anthropic()

SYSTEM_PROMPT = """You are an NYC incident briefing assistant.
Summarize the incidents provided in the tool data for the user.
Only use the data given. If there is none, say so."""

def run_agent(question: str, tool_result: dict) -> str:
    msg = client.messages.create(
        model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-5"),
        max_tokens=500,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": f"{question}\n\nIncident data:\n{json.dumps(tool_result)}",
        }],
    )
    return msg.content[0].text