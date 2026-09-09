import asyncio

import pytest

pytestmark = pytest.mark.integration


def test_mcp_server_lists_and_calls_read_only_tools():
    mcp_module = pytest.importorskip("mcp")
    from mcp import Client
    from agentic_qe.mcp_server import build_mcp_server

    async def run():
        server = build_mcp_server()
        async with Client(server) as client:
            tools = await client.list_tools()
            names = {tool.name for tool in tools.tools}
            assert {"scenario_context", "dataset_profile", "quality_capabilities"}.issubset(names)

            result = await client.call_tool(
                "scenario_context",
                {"scenario_path": "examples/etl-decimal-precision/scenario.json"},
            )
            assert result.structured_content["result"]["risk"] == "HIGH"

    asyncio.run(run())
