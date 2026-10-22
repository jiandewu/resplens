import asyncio

from mcp import Client

from resplens import server
from resplens.data import Dataset


def call(name: str, arguments: dict):
    async def run():
        async with Client(server.mcp) as client:
            return await client.call_tool(name, arguments)
    return asyncio.run(run())


def test_tools_are_registered():
    async def run():
        async with Client(server.mcp) as client:
            return {tool.name for tool in (await client.list_tools()).tools}
    assert asyncio.run(run()) == {"describe_measures", "describe_state", "get_series", "check_reliability",
                                  "get_revisions", "get_as_of"}


def test_tool_call_returns_structured_content(mirror, monkeypatch):
    monkeypatch.setattr(server, "_dataset", Dataset(mirror=mirror))
    result = call("get_series", {"state": "ZZ", "measure": "hospital_admission_count", "pathogen": "covid",
                                 "max_weeks": 1})
    assert not result.is_error
    assert result.structured_content["weeks"] == [{"week": "2026-10-10", "value": 65, "flag": "observed_valid",
                                                    "as_of": "2026-10-16"}]


def test_bad_request_becomes_tool_error(mirror, monkeypatch):
    monkeypatch.setattr(server, "_dataset", Dataset(mirror=mirror))
    result = call("describe_state", {"state": "XX"})
    assert result.is_error
    assert "unknown state" in result.content[0].text
