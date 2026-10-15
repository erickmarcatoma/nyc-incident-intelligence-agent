import json
from types import SimpleNamespace

import pytest

from backend import agent
from backend.agent import AgentProtocolError, run_agent


class FakeToolUse:
    type = "tool_use"
    name = "query_nyc_open_data_incidents"
    id = "toolu_test"
    input = {"borough": "Queens"}

    def model_dump(self) -> dict[str, object]:
        return {
            "type": self.type,
            "name": self.name,
            "id": self.id,
            "input": self.input,
        }


class FakeMessages:
    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []

    def create(self, **kwargs: object) -> SimpleNamespace:
        self.calls.append(kwargs)
        if len(self.calls) == 1:
            return SimpleNamespace(content=[FakeToolUse()])
        return SimpleNamespace(
            content=[
                SimpleNamespace(
                    type="text",
                    text=json.dumps(
                        {
                            "overview": "One reported collision was recorded.",
                            "potential_impacts": (
                                "No real-world impacts can be inferred from this "
                                "historical record, not current traffic."
                            ),
                        }
                    ),
                )
            ]
        )


class FakeClient:
    def __init__(self) -> None:
        self.messages = FakeMessages()


def successful_tool_result() -> dict[str, object]:
    return {
        "status": "success",
        "borough": "Queens",
        "data_source": "nyc_open_data",
        "overview": "Retrieved one collision record.",
        "incidents": [
            {
                "id": "4905715",
                "location": "QUEENS BLVD, MAIN ST",
                "type": "Motor vehicle collision",
                "reported_status": (
                    "Reported persons injured: 2; persons killed: 0."
                ),
                "reported_at": "2026-06-11T06:30:00-04:00",
                "source": "NYC Open Data: Motor Vehicle Collisions - Crashes",
                "source_url": (
                    "https://data.cityofnewyork.us/resource/"
                    "h9gi-nx95.json?collision_id=4905715"
                ),
            }
        ],
        "potential_impacts": "Historical crash reports do not show current traffic.",
        "data_freshness": "Most recent record returned: June 11, 2026.",
        "limitations": "Historical crash reports, not real-time traffic.",
    }


def test_run_agent_uses_tool_result_and_preserves_source_fields(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = FakeClient()
    monkeypatch.setattr(agent.anthropic, "Anthropic", lambda: client)
    monkeypatch.setattr(
        agent,
        "query_nyc_open_data_incidents",
        lambda borough: successful_tool_result(),
    )
    monkeypatch.setenv("ANTHROPIC_MODEL", "test-model")

    result = run_agent("Any traffic incidents?", agent.Borough.QUEENS)

    assert result["status"] == "success"
    assert result["data_source"] == "nyc_open_data"
    assert result["overview"] == "One reported collision was recorded."
    assert result["incidents"][0]["id"] == "4905715"
    assert "not real-time traffic" in result["limitations"]
    assert len(client.messages.calls) == 2
    assert client.messages.calls[0]["tool_choice"] == {
        "type": "tool",
        "name": "query_nyc_open_data_incidents",
    }
    assert client.messages.calls[0]["model"] == "test-model"
    assert client.messages.calls[1]["output_config"] == {
        "format": agent.BRIEFING_OUTPUT_FORMAT
    }
    final_messages = client.messages.calls[1]["messages"]
    assert isinstance(final_messages, list)
    tool_result = final_messages[2]["content"][0]
    assert tool_result["type"] == "tool_result"
    assert tool_result["tool_use_id"] == "toolu_test"
    assert json.loads(tool_result["content"])["incidents"][0]["id"] == "4905715"


def test_run_agent_rejects_unexpected_tool_request(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = FakeClient()
    client.messages.create = lambda **kwargs: SimpleNamespace(
        content=[SimpleNamespace(type="tool_use", name="other_tool", input={})]
    )
    monkeypatch.setattr(agent.anthropic, "Anthropic", lambda: client)

    with pytest.raises(AgentProtocolError):
        run_agent("Any traffic incidents?", agent.Borough.QUEENS)
